/*
 * MicroPython CAN wrapper for the Zephyr CAN controller API.
 *
 * The XIAO STM32C5 board maps can0 to FDCAN2. The wrapper intentionally uses
 * bounded receive timeouts so a missing transceiver or bus cannot hang the
 * interactive board test.
 */

#include "py/runtime.h"
#include "py/obj.h"
#include "zephyr_device.h"

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/drivers/can.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/util.h>

#define CAN_RX_QUEUE_DEPTH 128

typedef struct _can_obj_t {
    mp_obj_base_t base;
    const struct device *dev;
    int filter_id;
    bool fd;
    bool started;
    bool we_started;
    struct k_msgq rx_msgq;
    struct can_frame rx_frames[CAN_RX_QUEUE_DEPTH];
} can_obj_t;

extern const mp_obj_type_t can_type;

static void can_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind)
{
    can_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "CAN(%s, fd=%d, started=%d)",
        self->dev ? self->dev->name : "deinit", self->fd, self->started);
}

static void can_raise_errno(const char *operation, int err)
{
    mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("CAN %s failed (%d)"), operation, err);
}

static void can_cleanup(can_obj_t *self)
{
    if (self->dev == NULL) {
        return;
    }

    if (self->filter_id >= 0) {
        can_remove_rx_filter(self->dev, self->filter_id);
        self->filter_id = -1;
    }

    if (self->started && self->we_started) {
        (void)can_stop(self->dev);
        self->started = false;
    }

    self->dev = NULL;
}

static mp_obj_t can_make_new(const mp_obj_type_t *type,
                             size_t n_args, size_t n_kw,
                             const mp_obj_t *args)
{
    enum {
        ARG_dev,
        ARG_bitrate,
        ARG_data_bitrate,
        ARG_fd,
        ARG_loopback,
        ARG_COUNT,
    };
    static const mp_arg_t allowed_args[ARG_COUNT] = {
        { MP_QSTR_dev, MP_ARG_OBJ, {.u_obj = MP_OBJ_NULL} },
        { MP_QSTR_bitrate, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 500000} },
        { MP_QSTR_data_bitrate, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 2000000} },
        { MP_QSTR_fd, MP_ARG_KW_ONLY | MP_ARG_BOOL, {.u_bool = false} },
        { MP_QSTR_loopback, MP_ARG_KW_ONLY | MP_ARG_BOOL, {.u_bool = false} },
    };
    mp_arg_val_t parsed[ARG_COUNT];

    mp_arg_check_num(n_args, n_kw, 1, 1, true);
    mp_arg_parse_all_kw_array(n_args, n_kw, args, ARG_COUNT, allowed_args, parsed);

    const struct device *dev = zephyr_device_find(parsed[ARG_dev].u_obj);
    if (dev == NULL) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("CAN device not found: %s"),
            mp_obj_str_get_str(parsed[ARG_dev].u_obj));
    }
    if (!device_is_ready(dev)) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("CAN device not ready: %s"),
            dev->name);
    }

    can_obj_t *self = mp_obj_malloc_with_finaliser(can_obj_t, &can_type);
    self->dev = dev;
    self->filter_id = -1;
    self->fd = parsed[ARG_fd].u_bool;
    self->started = false;
    self->we_started = false;

    k_msgq_init(&self->rx_msgq, (char *)self->rx_frames,
                sizeof(struct can_frame), CAN_RX_QUEUE_DEPTH);

    int err = can_set_bitrate(dev, (uint32_t)parsed[ARG_bitrate].u_int);
    bool controller_running = (err == -EBUSY);

    if (err < 0 && !controller_running) {
        can_cleanup(self);
        can_raise_errno("set bitrate", err);
    }

    can_mode_t mode = parsed[ARG_loopback].u_bool ? CAN_MODE_LOOPBACK : 0;
    if (self->fd) {
        mode |= CAN_MODE_FD;
        if (!controller_running) {
            err = can_set_bitrate_data(dev, (uint32_t)parsed[ARG_data_bitrate].u_int);
            if (err < 0 && err != -EBUSY) {
                can_cleanup(self);
                can_raise_errno("set data bitrate", err);
            }
        }
    }

    if (!controller_running) {
        err = can_set_mode(dev, mode);
        if (err < 0 && err != -EBUSY) {
            can_cleanup(self);
            can_raise_errno("set mode", err);
        }
    }

    struct can_filter filter = {
        .id = 0,
        .mask = 0,
        .flags = 0,
    };
    self->filter_id = can_add_rx_filter_msgq(dev, &self->rx_msgq, &filter);
    if (self->filter_id < 0) {
        can_cleanup(self);
        can_raise_errno("add filter", self->filter_id);
    }

    err = can_start(dev);
    if (err == 0) {
        self->we_started = true;
    } else if (err == -EALREADY) {
        self->we_started = false;
    } else {
        can_cleanup(self);
        can_raise_errno("start", err);
    }
    self->started = true;
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t can_send_fun(mp_obj_t self_in, mp_obj_t id_in, mp_obj_t data_in)
{
    can_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->dev == NULL || !self->started) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("CAN is deinitialized"));
    }

    mp_buffer_info_t buffer;
    mp_get_buffer_raise(data_in, &buffer, MP_BUFFER_READ);
    if (buffer.len > CAN_MAX_DLEN || (!self->fd && buffer.len > 8U)) {
        mp_raise_ValueError(MP_ERROR_TEXT("CAN payload is too long"));
    }

    /* CAN FD DLC only encodes specific payload lengths: 0-8, 12, 16, 20,
     * 24, 32, 48, 64.  Reject lengths that cannot be represented exactly
     * to avoid silent zero-padding (e.g. 9 bytes -> DLC 9 -> 12 bytes on
     * the wire). */
    if (self->fd) {
        uint8_t len = (uint8_t)buffer.len;
        if (!(len <= 8 || len == 12 || len == 16 || len == 20 ||
              len == 24 || len == 32 || len == 48 || len == 64)) {
            mp_raise_ValueError(MP_ERROR_TEXT(
                "CAN FD payload must be 0-8, 12, 16, 20, 24, 32, 48, or 64 bytes"));
        }
    }

    struct can_frame frame = {0};
    frame.id = mp_obj_get_int(id_in);
    frame.dlc = can_bytes_to_dlc((uint8_t)buffer.len);
    frame.flags = self->fd ? (CAN_FRAME_FDF | CAN_FRAME_BRS) : 0;
    memcpy(frame.data, buffer.buf, buffer.len);

    int err = can_send(self->dev, &frame, K_MSEC(100), NULL, NULL);
    if (err < 0) {
        can_raise_errno("send", err);
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_3(can_send_obj, can_send_fun);

static mp_obj_t can_recv_fun(size_t n_args, const mp_obj_t *args)
{
    can_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    if (self->dev == NULL || !self->started) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("CAN is deinitialized"));
    }

    mp_int_t timeout_ms = n_args > 1 ? mp_obj_get_int(args[1]) : 0;
    if (timeout_ms < 0) {
        timeout_ms = 0;
    }

    struct can_frame frame;
    int err = k_msgq_get(&self->rx_msgq, &frame, K_MSEC(timeout_ms));
    if (err == -EAGAIN || err == -ENOMSG) {
        return mp_const_none;
    }
    if (err < 0) {
        can_raise_errno("receive", err);
    }

    mp_obj_t tuple[3] = {
        mp_obj_new_int_from_uint(frame.id),
        mp_obj_new_bytes(frame.data, can_dlc_to_bytes(frame.dlc)),
        mp_obj_new_int_from_uint(frame.flags),
    };
    return mp_obj_new_tuple(3, tuple);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(can_recv_obj, 1, 2, can_recv_fun);

static mp_obj_t can_status_fun(mp_obj_t self_in)
{
    can_obj_t *self = MP_OBJ_TO_PTR(self_in);
    enum can_state state = CAN_STATE_STOPPED;
    struct can_bus_err_cnt err_cnt = {0};
    can_mode_t mode = 0;
    int err = 0;

    if (self->dev != NULL) {
        err = can_get_state(self->dev, &state, &err_cnt);
        if (err == 0) {
            mode = can_get_mode(self->dev);
        }
    }

    mp_obj_t tuple[5] = {
        mp_obj_new_int(err),
        mp_obj_new_int(state),
        mp_obj_new_int(err_cnt.tx_err_cnt),
        mp_obj_new_int(err_cnt.rx_err_cnt),
        mp_obj_new_int_from_uint(mode),
    };
    return mp_obj_new_tuple(5, tuple);
}
MP_DEFINE_CONST_FUN_OBJ_1(can_status_obj, can_status_fun);

static mp_obj_t can_deinit_fun(mp_obj_t self_in)
{
    can_cleanup(MP_OBJ_TO_PTR(self_in));
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(can_deinit_obj, can_deinit_fun);

static const mp_rom_map_elem_t can_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_send), MP_ROM_PTR(&can_send_obj) },
    { MP_ROM_QSTR(MP_QSTR_recv), MP_ROM_PTR(&can_recv_obj) },
    { MP_ROM_QSTR(MP_QSTR_status), MP_ROM_PTR(&can_status_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&can_deinit_obj) },
    { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&can_deinit_obj) },
};
static MP_DEFINE_CONST_DICT(can_locals_dict, can_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    can_type,
    MP_QSTR_CAN,
    MP_TYPE_FLAG_NONE,
    make_new, can_make_new,
    print, can_print,
    locals_dict, &can_locals_dict
);

static const mp_rom_map_elem_t can_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_CAN) },
    { MP_ROM_QSTR(MP_QSTR_CAN), MP_ROM_PTR(&can_type) },
};
static MP_DEFINE_CONST_DICT(can_module_globals, can_module_globals_table);

const mp_obj_module_t can_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&can_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_CAN, can_module);
