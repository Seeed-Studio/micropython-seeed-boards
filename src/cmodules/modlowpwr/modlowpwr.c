#include "py/runtime.h"
#include "py/obj.h"
#include "py/mphal.h"

#include <zephyr/drivers/hwinfo.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/pm/device.h>
#include "zephyr_device.h"
#include <zephyr/device.h>
#include <zephyr/sys/util.h>
#include <zephyr/kernel.h>

#define RESET_DEBUG_FLAG 0x01
#define RESET_CLOCK_FLAG 0x02
#define RESET_GPIO_FLAG  0x04
#define RESET_OTHER_FLAG 0x08

static uint32_t reset_cause = RESET_OTHER_FLAG;
static const struct device *console_dev = NULL;

typedef struct _lowpwr_obj_t {
    mp_obj_base_t base;
    const struct device *console;
} lowpwr_obj_t;

static void print_reset_cause_internal(void);
static void clear_reset_cause_internal(void);
static void power_off_internal(void);
static void configure_wakeup_pin_internal(const struct gpio_dt_spec *pin);

extern const mp_obj_type_t lowpwr_type;

static void lowpwr_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind)
{
    lowpwr_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "LowPWR(%s)", self->console ? self->console->name : "default");
}

static mp_obj_t lowpwr_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args)
{
    lowpwr_obj_t *self = mp_obj_malloc_with_finaliser(lowpwr_obj_t, &lowpwr_type);
    self->console = NULL; 
    
    if (n_args > 0) {
        const struct device *dev = zephyr_device_find(args[0]);
        if (dev == NULL) {
            mp_raise_msg_varg(&mp_type_OSError, 
                "Console device not found: %s", mp_obj_str_get_str(args[0]));
        }
        
        if (!device_is_ready(dev)) {
            mp_raise_msg_varg(&mp_type_OSError, 
                "Console device not ready: %s", mp_obj_str_get_str(args[0]));
        }
        
        self->console = dev;
        console_dev = dev; 
    }
    
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t lowpwr_print_reset_cause(mp_obj_t self_in)
{
    print_reset_cause_internal();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lowpwr_print_reset_cause_obj, lowpwr_print_reset_cause);

static mp_obj_t lowpwr_clear_reset_cause(mp_obj_t self_in)
{
    clear_reset_cause_internal();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lowpwr_clear_reset_cause_obj, lowpwr_clear_reset_cause);

static mp_obj_t lowpwr_power_off(mp_obj_t self_in)
{
    power_off_internal();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(lowpwr_power_off_obj, lowpwr_power_off);

static mp_obj_t lowpwr_configure_wakeup_pin(mp_obj_t self_in, mp_obj_t pin_in)
{
    if (!mp_obj_is_type(pin_in, &mp_type_tuple)) {
        mp_raise_TypeError("Argument must be a tuple (device_name, pin_number)");
    }
    
    mp_obj_t *items;
    mp_obj_get_array_fixed_n(pin_in, 2, &items);
    
    const struct device *dev = zephyr_device_find(items[0]);
    if (dev == NULL) {
        mp_raise_msg_varg(&mp_type_OSError, 
            "GPIO device not found: %s", mp_obj_str_get_str(items[0]));
    }
    
    if (!device_is_ready(dev)) {
        mp_raise_msg_varg(&mp_type_OSError, 
            "GPIO device not ready: %s", mp_obj_str_get_str(items[0]));
    }
    
    int pin_num = mp_obj_get_int(items[1]);
    
    struct gpio_dt_spec pin_spec = {
        .port = dev,
        .pin = pin_num,
        .dt_flags = 0  
    };
    
    configure_wakeup_pin_internal(&pin_spec);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(lowpwr_configure_wakeup_pin_obj, lowpwr_configure_wakeup_pin);

static const mp_rom_map_elem_t lowpwr_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_print_reset_cause), MP_ROM_PTR(&lowpwr_print_reset_cause_obj) },
    { MP_ROM_QSTR(MP_QSTR_clear_reset_cause), MP_ROM_PTR(&lowpwr_clear_reset_cause_obj) },
    { MP_ROM_QSTR(MP_QSTR_power_off), MP_ROM_PTR(&lowpwr_power_off_obj) },
    { MP_ROM_QSTR(MP_QSTR_configure_wakeup_pin), MP_ROM_PTR(&lowpwr_configure_wakeup_pin_obj) },
};
static MP_DEFINE_CONST_DICT(lowpwr_locals_dict, lowpwr_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    lowpwr_type,
    MP_QSTR_LowPWR,
    MP_TYPE_FLAG_NONE,
    make_new, lowpwr_make_new,
    print, lowpwr_print,
    locals_dict, &lowpwr_locals_dict
);

static const mp_rom_map_elem_t lowpwr_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_LowPWR) },
    { MP_ROM_QSTR(MP_QSTR_LowPWR), MP_ROM_PTR(&lowpwr_type) },
};
static MP_DEFINE_CONST_DICT(lowpwr_module_globals, lowpwr_module_globals_table);

const mp_obj_module_t lowpwr_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lowpwr_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_LowPWR, lowpwr_module);

static void print_reset_cause_internal(void)
{
    uint32_t hw_cause;
    if (hwinfo_get_reset_cause(&hw_cause) == 0) {
        reset_cause = hw_cause;
    }
    
    if (reset_cause & RESET_DEBUG_FLAG) {
        mp_printf(&mp_plat_print, "Reset by debugger.\n");
    } else if (reset_cause & RESET_CLOCK_FLAG) {
        mp_printf(&mp_plat_print, "Wakeup from System OFF by RTC.\n");
    } else if (reset_cause & RESET_GPIO_FLAG) {
        mp_printf(&mp_plat_print, "Wakeup from System OFF by GPIO.\n");
    } else {
        mp_printf(&mp_plat_print, "Other wake up cause: 0x%08X\n", reset_cause);
    }
}

static void clear_reset_cause_internal(void)
{
    reset_cause = RESET_OTHER_FLAG;
}

static void power_off_internal(void)
{
    if (console_dev && device_is_ready(console_dev)) {
        pm_device_action_run(console_dev, PM_DEVICE_ACTION_SUSPEND);
    }
    
    clear_reset_cause_internal();
    sys_poweroff();
}

static void configure_wakeup_pin_internal(const struct gpio_dt_spec *pin)
{
    if (!gpio_is_ready_dt(pin)) {
        mp_raise_msg_varg(&mp_type_OSError, 
            "Wakeup pin device %s not ready", pin->port->name);
    }
    
    int rc = gpio_pin_configure_dt(pin, GPIO_INPUT);
    if (rc < 0) {
        mp_raise_OSError(-rc);
    }
    
    rc = gpio_pin_interrupt_configure_dt(pin, GPIO_INT_LEVEL_LOW);
    if (rc < 0) {
        mp_raise_OSError(-rc);
    }
}