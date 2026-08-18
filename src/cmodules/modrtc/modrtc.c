/*
 * This file is part of the micropython-seeed-boards project, https://github.com/Seeed-Studio/micropython-seeed-boards/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2025 Xinglei Li <xinglei.li@seeed.cc>
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

#include <zephyr/drivers/rtc.h>
#include <zephyr/device.h>
#include <zephyr/sys/util.h>
#include <zephyr/kernel.h>
#include <time.h>
#include <string.h> 

#ifndef MICROPY_HW_RTC_USER_MEM_MAX
#define MICROPY_HW_RTC_USER_MEM_MAX 0
#endif

typedef struct _rtc_obj_t {
    mp_obj_base_t base;
    const struct device *rtc_dev;
    #if MICROPY_HW_RTC_USER_MEM_MAX > 0
    uint8_t user_mem[MICROPY_HW_RTC_USER_MEM_MAX];
    size_t user_mem_len;
    #endif
} rtc_obj_t;

static void rtc_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind);
static mp_obj_t rtc_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args);
static mp_obj_t rtc_set_datetime(mp_obj_t self_in, mp_obj_t datetime_in);
static mp_obj_t rtc_get_datetime(mp_obj_t self_in);
#if MICROPY_HW_RTC_USER_MEM_MAX > 0
static mp_obj_t rtc_memory(size_t n_args, const mp_obj_t *args);
#endif
static mp_obj_t rtc_deinit(mp_obj_t self_in);

static rtc_obj_t rtc_singleton;
static bool rtc_initialized = false;

static int set_rtc_time(const struct device *dev, int year, int month, int day, 
                        int hour, int minute, int second)
{
    struct rtc_time new_time;
    struct tm temp_tm = {0};

    temp_tm.tm_year = year - 1900;
    temp_tm.tm_mon = month - 1;
    temp_tm.tm_mday = day;
    temp_tm.tm_hour = hour;
    temp_tm.tm_min = minute;
    temp_tm.tm_sec = second;

    new_time.tm_year = temp_tm.tm_year;
    new_time.tm_mon = temp_tm.tm_mon;
    new_time.tm_mday = temp_tm.tm_mday;
    new_time.tm_hour = temp_tm.tm_hour;
    new_time.tm_min = temp_tm.tm_min;
    new_time.tm_sec = temp_tm.tm_sec;
    new_time.tm_wday = 0;
    new_time.tm_yday = 0;
    new_time.tm_isdst = 0;

    int ret = rtc_set_time(dev, &new_time);
    if (ret == 0) {
        printk("RTC time set to: %04d-%02d-%02d %02d:%02d:%02d\n",
               year, month, day, hour, minute, second);
    } else {
        printk("Error: Failed to set RTC time! Code: %d\n", ret);
    }
    return ret;
}

static void rtc_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind)
{
    rtc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->rtc_dev) {
        mp_printf(print, "RTC(%s)", self->rtc_dev->name);
    } else {
        mp_printf(print, "RTC(not initialized)");
    }
}

static mp_obj_t rtc_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args)
{
    if (!rtc_initialized) {
        rtc_singleton.base.type = type;
        rtc_singleton.rtc_dev = NULL;
        
        const struct device *dev = DEVICE_DT_GET_OR_NULL(DT_ALIAS(rtc));
        if (dev != NULL && device_is_ready(dev)) {
            rtc_singleton.rtc_dev = dev;
            printk("Using default RTC device: %s\n", dev->name);
        } 
        #if MICROPY_HW_RTC_USER_MEM_MAX > 0
        rtc_singleton.user_mem_len = 0;
        #endif
        
        rtc_initialized = true;
    }
    
    if (n_args > 0) {
        const struct device *dev = zephyr_device_find(args[0]);
        if (dev != NULL && device_is_ready(dev)) {
            rtc_singleton.rtc_dev = dev;
            printk("Using specified RTC device: %s\n", dev->name);
        } else {
            mp_raise_msg_varg(&mp_type_OSError, 
                "RTC device not found or not ready: %s", 
                mp_obj_str_get_str(args[0]));
        }
    }
    
    return MP_OBJ_FROM_PTR(&rtc_singleton);
}

static mp_obj_t rtc_set_datetime(mp_obj_t self_in, mp_obj_t datetime_in)
{
    rtc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    
    if (!self->rtc_dev) {
        mp_raise_msg(&mp_type_OSError, "RTC device not initialized");
    }
    
    mp_obj_t *items;
    mp_obj_get_array_fixed_n(datetime_in, 6, &items);
    
    int year = mp_obj_get_int(items[0]);
    int month = mp_obj_get_int(items[1]);
    int day = mp_obj_get_int(items[2]);
    int hour = mp_obj_get_int(items[3]);
    int minute = mp_obj_get_int(items[4]);
    int second = mp_obj_get_int(items[5]);
    
    int ret = set_rtc_time(self->rtc_dev, year, month, day, hour, minute, second);
    if (ret != 0) {
        mp_raise_OSError(-ret);
    }
    
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(rtc_set_datetime_obj, rtc_set_datetime);

static mp_obj_t rtc_get_datetime(mp_obj_t self_in)
{
    rtc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    
    if (!self->rtc_dev) {
        mp_raise_msg(&mp_type_OSError, "RTC device not initialized");
    }
    
    struct rtc_time rtc_time;
    memset(&rtc_time, 0, sizeof(rtc_time));
    
    int ret = rtc_get_time(self->rtc_dev, &rtc_time);
    if (ret != 0) {
        mp_raise_OSError(-ret);
    }
    
    mp_obj_t tuple[6] = {
        mp_obj_new_int(rtc_time.tm_year + 1900),
        mp_obj_new_int(rtc_time.tm_mon + 1),
        mp_obj_new_int(rtc_time.tm_mday),
        mp_obj_new_int(rtc_time.tm_hour),
        mp_obj_new_int(rtc_time.tm_min),
        mp_obj_new_int(rtc_time.tm_sec),
    };
    
    return mp_obj_new_tuple(6, tuple);
}
MP_DEFINE_CONST_FUN_OBJ_1(rtc_get_datetime_obj, rtc_get_datetime);

static mp_obj_t rtc_deinit(mp_obj_t self_in)
{
    rtc_obj_t *self = MP_OBJ_TO_PTR(self_in);
    self->rtc_dev = NULL;
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(rtc_deinit_obj, rtc_deinit);

#if MICROPY_HW_RTC_USER_MEM_MAX > 0
static mp_obj_t rtc_memory(size_t n_args, const mp_obj_t *args)
{
    rtc_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    
    if (n_args == 1) {
        return mp_obj_new_bytes(self->user_mem, self->user_mem_len);
    } else {
        mp_buffer_info_t bufinfo;
        mp_get_buffer_raise(args[1], &bufinfo, MP_BUFFER_READ);
        
        if (bufinfo.len > MICROPY_HW_RTC_USER_MEM_MAX) {
            mp_raise_ValueError("Memory too large");
        }
        
        memcpy(self->user_mem, bufinfo.buf, bufinfo.len);
        self->user_mem_len = bufinfo.len;
        
        return mp_const_none;
    }
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(rtc_memory_obj, 1, 2, rtc_memory);
#endif

static const mp_rom_map_elem_t rtc_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_set_datetime), MP_ROM_PTR(&rtc_set_datetime_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_datetime), MP_ROM_PTR(&rtc_get_datetime_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&rtc_deinit_obj) },
    #if MICROPY_HW_RTC_USER_MEM_MAX > 0
    { MP_ROM_QSTR(MP_QSTR_memory), MP_ROM_PTR(&rtc_memory_obj) },
    #endif
};
static MP_DEFINE_CONST_DICT(rtc_locals_dict, rtc_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    rtc_type,
    MP_QSTR_RTC,
    MP_TYPE_FLAG_NONE,
    make_new, rtc_make_new,
    print, rtc_print,
    locals_dict, &rtc_locals_dict
);

static const mp_rom_map_elem_t rtc_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_RTC) },
    { MP_ROM_QSTR(MP_QSTR_RTC), MP_ROM_PTR(&rtc_type) },
};
static MP_DEFINE_CONST_DICT(mp_module_rtc_globals, rtc_module_globals_table);

const mp_obj_module_t rtc_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mp_module_rtc_globals,
};

MP_REGISTER_MODULE(MP_QSTR_RTC, rtc_module);