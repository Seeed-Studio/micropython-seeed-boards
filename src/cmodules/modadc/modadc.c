/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2025 NED KONZ <NED@METAMAGIX.TECH>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "py/runtime.h"
#include "py/obj.h"
#include "py/mphal.h"
#include "zephyr_device.h"

#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/util.h>
#include <zephyr/drivers/adc.h>

#if !DT_NODE_EXISTS(DT_PATH(zephyr_user)) || \
    !DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
#error "No suitable devicetree overlay specified"
#endif

#define DT_SPEC_AND_COMMA(node_id, prop, idx) \
    ADC_DT_SPEC_GET_BY_IDX(node_id, idx),

static const struct adc_dt_spec adc_channels[] = {
    DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels,
        DT_SPEC_AND_COMMA)
};

#define NUM_CHANNELS ARRAY_SIZE(adc_channels)

static uint16_t sample_buffer;

static struct adc_sequence adc_sequence = {
    .options = NULL,
    .channels = 0,
    .buffer = &sample_buffer,
    .buffer_size = sizeof(sample_buffer),
    .resolution = 12,
    .oversampling = 0,
    .calibrate = false,
};

typedef struct _adc_obj_t {
    mp_obj_base_t base;
    const char *name;
    const struct adc_dt_spec *spec;
} adc_obj_t;

extern const mp_obj_type_t adc_type;

static void adc_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    adc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "ADC(%s.%d)", self->name, self->spec->channel_id);
}

static mp_obj_t adc_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, MP_OBJ_FUN_ARGS_MAX, true);

    adc_obj_t *self = NULL;
    if (mp_obj_is_type(args[0], &adc_type)) {
        self = MP_OBJ_TO_PTR(args[0]);
    } else if (mp_obj_is_type(args[0], &mp_type_tuple)) {
        mp_obj_t *items;
        mp_obj_get_array_fixed_n(args[0], 2, &items);
        const char *dev_name = mp_obj_str_get_str(items[0]);
        int channel_id = mp_obj_get_int(items[1]);
        const struct device *wanted_port = zephyr_device_find(items[0]);

        const struct adc_dt_spec *wanted_adc_channel = NULL;
        for (size_t i = 0U; i < NUM_CHANNELS; i++) {
            if (adc_channels[i].dev == wanted_port &&
                adc_channels[i].channel_id == channel_id) {
                wanted_adc_channel = &adc_channels[i];
                break;
            }
        }
        if (!wanted_adc_channel) {
            mp_raise_msg_varg(&mp_type_ValueError, "ADC channel (%s, %d) not found", dev_name, channel_id);
        }

        if (!adc_is_ready_dt(wanted_adc_channel)) {
            mp_raise_msg_varg(&mp_type_ValueError, "ADC device (%s) not ready", dev_name);
        }

        int err = adc_channel_setup_dt(wanted_adc_channel);
        if (err < 0) {
            mp_raise_msg_varg(&mp_type_ValueError, "Could not setup ADC %s channel %d (err=%d)", dev_name, channel_id, err);
        }

        self = mp_obj_malloc(adc_obj_t, &adc_type);
        self->spec = wanted_adc_channel;
        self->name = dev_name;
    } else {
        mp_raise_ValueError("ADC must be initialized with a tuple of (adcblock, channel) or an ADC object");
    }

    return MP_OBJ_FROM_PTR(self);
}

static mp_uint_t adc_read_raw_value(const struct adc_dt_spec *spec) {
    int err = adc_sequence_init_dt(spec, &adc_sequence);
    if (err < 0) {
        mp_raise_msg_varg(&mp_type_ValueError, "ADC %s channel %d invalid (err=%d)", spec->dev->name, spec->channel_id, err);
    }

    err = adc_read_dt(spec, &adc_sequence);
    if (err < 0) {
        mp_raise_msg_varg(&mp_type_ValueError, "ADC %s channel %d read failed (err=%d)", spec->dev->name, spec->channel_id, err);
    }

    return (mp_uint_t)sample_buffer;
}

static mp_int_t adc_read_u16(adc_obj_t *self) {
    mp_uint_t raw = adc_read_raw_value(self->spec);
    mp_int_t bits = self->spec->resolution;
    mp_uint_t u16 = raw << (16 - bits) | raw >> (2 * bits - 16);
    return u16;
}

static mp_int_t adc_read_uv(adc_obj_t *self) {
    int32_t raw = (int32_t)adc_read_raw_value(self->spec);
    int err = adc_raw_to_millivolts_dt(self->spec, &raw);
    if (err < 0) {
        mp_raise_msg_varg(&mp_type_ValueError, "ADC %s channel %d uv conversion failed (err=%d)",
            self->name, self->spec->channel_id, err);
    }
    return (mp_int_t)raw * 1000UL;
}

static mp_int_t adc_read_value(adc_obj_t *self) {
    mp_uint_t raw = adc_read_raw_value(self->spec);
    return (mp_int_t)raw;
}

static mp_obj_t adc_read_u16_fun(mp_obj_t self_in) {
    adc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    return mp_obj_new_int(adc_read_u16(self));
}
MP_DEFINE_CONST_FUN_OBJ_1(adc_read_u16_fun_obj, adc_read_u16_fun);

static mp_obj_t adc_read_uv_fun(mp_obj_t self_in) {
    adc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    return mp_obj_new_int(adc_read_uv(self));
}
MP_DEFINE_CONST_FUN_OBJ_1(adc_read_uv_fun_obj, adc_read_uv_fun);

static mp_obj_t adc_read_value_fun(mp_obj_t self_in) {
    adc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    return mp_obj_new_int(adc_read_value(self));
}
MP_DEFINE_CONST_FUN_OBJ_1(adc_read_value_fun_obj, adc_read_value_fun);

static const mp_rom_map_elem_t adc_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_read_u16), MP_ROM_PTR(&adc_read_u16_fun_obj) },
    { MP_ROM_QSTR(MP_QSTR_read_uv), MP_ROM_PTR(&adc_read_uv_fun_obj) },
    { MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&adc_read_value_fun_obj) },
};
static MP_DEFINE_CONST_DICT(adc_locals_dict, adc_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    adc_type,
    MP_QSTR_ADC,
    MP_TYPE_FLAG_NONE,
    make_new, adc_make_new,
    print, adc_print,
    locals_dict, &adc_locals_dict
);

static const mp_rom_map_elem_t adc_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ADC) },
    { MP_ROM_QSTR(MP_QSTR_ADC), MP_ROM_PTR(&adc_type) },
};
static MP_DEFINE_CONST_DICT(adc_module_globals, adc_module_globals_table);

const mp_obj_module_t adc_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&adc_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ADC, adc_module);
