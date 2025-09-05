#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/util.h>
#include <zephyr/audio/dmic.h>
#include "py/mphal.h"
#include "py/runtime.h"
#include "py/obj.h"
#include "py/objarray.h"
#include "zephyr_device.h" 

typedef struct _pdm_obj_t {
    mp_obj_base_t base;
    const struct device *dev;
    uint8_t stream_id;
    struct k_mem_slab *mem_slab;
    size_t block_size;
    uint32_t sample_rate;
    uint8_t sample_width;
    uint8_t num_channels;
    bool active;
} pdm_obj_t;

#define MAX_BLOCK_SIZE 6400
#define BLOCK_COUNT 4      
K_MEM_SLAB_DEFINE_STATIC(mem_slab, MAX_BLOCK_SIZE, BLOCK_COUNT, 4);

extern const mp_obj_type_t pdm_type;

static void pdm_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    pdm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "PDM(device=%s, stream=%d, rate=%u, width=%u, channels=%u)",
              self->dev->name, self->stream_id, self->sample_rate, self->sample_width, self->num_channels);
}

static mp_obj_t pdm_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, 2, false);

    const struct device *dev = zephyr_device_find(args[0]);
    if (dev == NULL) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("PDM device not found: %s"), mp_obj_str_get_str(args[0]));
    }
    
    if (!device_is_ready(dev)) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("PDM device not ready: %s"), dev->name);
    }

    pdm_obj_t *self = mp_obj_malloc_with_finaliser(pdm_obj_t, &pdm_type);
    self->dev = dev;
    self->active = false;
    self->mem_slab = &mem_slab;

    if (n_args > 1) {
        self->stream_id = mp_obj_get_int(args[1]);
    } else {
        self->stream_id = 0; 
    }
    
    self->sample_rate = 16000;
    self->sample_width = 16;
    self->num_channels = 1;
    self->block_size = (self->sample_width / 8) * (self->sample_rate / 10) * self->num_channels;
    
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t pdm_configure(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_rate, ARG_width, ARG_channels, ARG_block_size };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_rate, MP_ARG_INT, {.u_int = 16000} },
        { MP_QSTR_width, MP_ARG_INT, {.u_int = 16} },
        { MP_QSTR_channels, MP_ARG_INT, {.u_int = 1} },
        { MP_QSTR_block_size, MP_ARG_INT, {.u_int = 0} },
    };
    
    pdm_obj_t *self = MP_OBJ_TO_PTR(pos_args[0]);
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args - 1, pos_args + 1, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);
    
    self->sample_rate = args[ARG_rate].u_int;
    self->sample_width = args[ARG_width].u_int;
    self->num_channels = args[ARG_channels].u_int;
    
    if (args[ARG_block_size].u_int == 0) {
        self->block_size = (self->sample_width / 8) * (self->sample_rate / 10) * self->num_channels;
    } else {
        self->block_size = args[ARG_block_size].u_int;
    }
    
    struct dmic_cfg config = {0};
    
    struct pcm_stream_cfg stream_cfg = {
        .pcm_rate = self->sample_rate,
        .pcm_width = self->sample_width,
        .block_size = self->block_size,
        .mem_slab = self->mem_slab,
    };
    config.streams = &stream_cfg;
    
    struct pdm_chan_cfg channel_cfg = {
        .req_num_chan = self->num_channels,
        .act_num_chan = self->num_channels,
        .req_num_streams = 1,
        .act_num_streams = 1,
    };
    
    channel_cfg.req_chan_map_lo = 0;
    channel_cfg.req_chan_map_hi = 0;
    
    if (self->num_channels == 1) {
        channel_cfg.req_chan_map_lo = dmic_build_channel_map(0, 0, PDM_CHAN_LEFT);
    } else if (self->num_channels == 2) {
        channel_cfg.req_chan_map_lo = 
            dmic_build_channel_map(0, 0, PDM_CHAN_LEFT) |
            dmic_build_channel_map(1, 0, PDM_CHAN_RIGHT);
    } else {
        for (int i = 0; i < self->num_channels; i++) {
            enum pdm_lr chan = (i % 2 == 0) ? PDM_CHAN_LEFT : PDM_CHAN_RIGHT;
            
            if (i < 8) {
                channel_cfg.req_chan_map_lo |= dmic_build_channel_map(i, i, chan);
            } else {
                channel_cfg.req_chan_map_hi |= dmic_build_channel_map(i, i - 8, chan);
            }
        }
    }
    config.channel = channel_cfg;
    
    struct pdm_io_cfg io_cfg = {
        .min_pdm_clk_freq = 1000000,
        .max_pdm_clk_freq = 3500000,
        .min_pdm_clk_dc = 40,
        .max_pdm_clk_dc = 60,
    };
    config.io = io_cfg;
    
    int ret = dmic_configure(self->dev, &config);
    if (ret != 0) {
        const char *err_msg;
        switch (-ret) {
            case EINVAL:
                err_msg = "Invalid configuration parameters";
                break;
            case EIO:
                err_msg = "I/O error during configuration";
                break;
            case ENOTSUP:
                err_msg = "Unsupported configuration";
                break;
            default:
                err_msg = "Unknown configuration error";
        }
        mp_raise_msg_varg(&mp_type_OSError, "PDM configure failed: %s (errno %d)", err_msg, -ret);
    }
    
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(pdm_configure_obj, 1, pdm_configure);

static mp_obj_t pdm_start(mp_obj_t self_in) {
    pdm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    
    if (self->active) {
        return mp_const_none; 
    }
    
    int ret = dmic_trigger(self->dev, DMIC_TRIGGER_START);
    if (ret != 0) {
        mp_raise_OSError(-ret);
    }
    
    self->active = true;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(pdm_start_obj, pdm_start);

static mp_obj_t pdm_stop(mp_obj_t self_in) {
    pdm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    
    if (!self->active) {
        return mp_const_none; 
    }
    
    int ret = dmic_trigger(self->dev, DMIC_TRIGGER_STOP);
    if (ret != 0) {
        mp_raise_OSError(-ret);
    }
    
    self->active = false;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(pdm_stop_obj, pdm_stop);

static mp_obj_t pdm_read(mp_obj_t self_in) {
    pdm_obj_t *self = MP_OBJ_TO_PTR(self_in);
    
    if (!self->active) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("PDM not active, call start() first"));
    }
    
    void *buffer;
    size_t size;
    int ret;
    
    ret = dmic_read(self->dev, self->stream_id, &buffer, &size, 100);
    if (ret != 0) {
        if (ret == -EAGAIN) {
            return mp_obj_new_bytearray(0, NULL);
        }
        mp_raise_OSError(-ret);
    }
    uint8_t *copy = m_new(uint8_t, size);
    if (copy == NULL) {
        k_mem_slab_free(self->mem_slab, buffer);
        mp_raise_OSError(ENOMEM);
    }
    
    memcpy(copy, buffer, size);
    
    k_mem_slab_free(self->mem_slab, buffer);
    
    return mp_obj_new_bytearray(size, copy);
}
static MP_DEFINE_CONST_FUN_OBJ_1(pdm_read_obj, pdm_read);

static const mp_rom_map_elem_t pdm_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_configure), MP_ROM_PTR(&pdm_configure_obj) },
    { MP_ROM_QSTR(MP_QSTR_start), MP_ROM_PTR(&pdm_start_obj) },
    { MP_ROM_QSTR(MP_QSTR_stop), MP_ROM_PTR(&pdm_stop_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&pdm_read_obj) },
};
static MP_DEFINE_CONST_DICT(pdm_locals_dict, pdm_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    pdm_type,
    MP_QSTR_PDM,
    MP_TYPE_FLAG_NONE,
    make_new, pdm_make_new,
    print, pdm_print,
    locals_dict, &pdm_locals_dict
);

static const mp_rom_map_elem_t pdm_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_PDM) },
    { MP_ROM_QSTR(MP_QSTR_PDM), MP_ROM_PTR(&pdm_type) },
};
static MP_DEFINE_CONST_DICT(pdm_module_globals, pdm_module_globals_table);

const mp_obj_module_t pdm_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&pdm_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_PDM, pdm_module);