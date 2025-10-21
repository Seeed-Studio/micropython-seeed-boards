// MCU config
#define MICROPY_HW_BOARD_NAME       "SEEED_XIAO_RA4M1"
#define MICROPY_HW_MCU_NAME         "RA4M1"
#define MICROPY_HW_MCU_SYSCLK       48000000
#define MICROPY_HW_MCU_PCLK         48000000

// module config
// #define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_BASIC_FEATURES)
// #define MICROPY_ENABLE_FINALISER    (1)

#define MICROPY_EMIT_THUMB          (0)
#define MICROPY_EMIT_INLINE_THUMB   (0)
#define MICROPY_PY_BUILTINS_COMPLEX (0)
#define MICROPY_PY_GENERATOR_PEND_THROW (0)
#define MICROPY_PY_MATH             (0)
#define MICROPY_PY_HEAPQ            (0)
#define MICROPY_PY_THREAD           (0) // disable ARM_THUMB_FP using vldr due to RA has single float only

// peripheral config
#define MICROPY_HW_ENABLE_RTC       (1)
#define MICROPY_HW_RTC_SOURCE       (1)    // 0: subclock, 1:LOCO (32.768khz)
#define MICROPY_HW_ENABLE_ADC       (1)
#define MICROPY_HW_HAS_FLASH        (1)
#define MICROPY_HW_ENABLE_USBDEV    (1)
#define MICROPY_HW_ENABLE_UART_REPL (0)
#define MICROPY_HW_ENABLE_INTERNAL_FLASH_STORAGE (1)

// UART
#define MICROPY_HW_UART2_TX         (pin_P302)
#define MICROPY_HW_UART2_RX         (pin_P301) 

// PWM
#define MICROPY_HW_PWM_1A           (pin_P109)
#define MICROPY_HW_PWM_1B           (pin_P110)
#define MICROPY_HW_PWM_3A           (pin_P111)
#define MICROPY_HW_PWM_4A           (pin_P302)
#define MICROPY_HW_PWM_4B           (pin_P301)
#define MICROPY_HW_PWM_5B           (pin_P100)

// I2C
// #define MICROPY_HW_I2C1_SCL         (pin_P100) 
// #define MICROPY_HW_I2C1_SDA         (pin_P206) 

// Switch
#define MICROPY_HW_HAS_SWITCH       (1)
#define MICROPY_HW_USRSW_PIN        (pin_P201)
#define MICROPY_HW_USRSW_PULL       (MP_HAL_PIN_PULL_UP)
#define MICROPY_HW_USRSW_EXTI_MODE  (MP_HAL_PIN_TRIGGER_FALLING)
#define MICROPY_HW_USRSW_PRESSED    (0)

// LEDs
#define MICROPY_HW_LED1             (pin_P011)
#define MICROPY_HW_LED_ON(pin)      mp_hal_pin_low(pin)
#define MICROPY_HW_LED_OFF(pin)     mp_hal_pin_high(pin)
#define MICROPY_HW_LED_TOGGLE(pin)  mp_hal_pin_toggle(pin)


