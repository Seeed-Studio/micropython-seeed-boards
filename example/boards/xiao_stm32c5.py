class xiao_stm32c5:
    def pin(pin):
        xiao_pin = {
            0: ("gpioa", 0),
            1: ("gpioa", 1),
            2: ("gpioa", 2),
            3: ("gpioa", 3),
            4: ("gpiob", 7),
            5: ("gpiob", 6),
            6: ("gpioa", 9),
            7: ("gpioa", 10),
            8: ("gpioa", 15),
            9: ("gpiob", 0),
            10: ("gpiob", 15),
            11: ("gpiob", 8),
            12: ("gpiob", 9),
            13: ("gpiob", 5),
            14: ("gpiob", 13),
            15: ("gpiob", 14),
            "led": ("gpiob", 12),
            "bat_en": ("gpioe", 2),
            "imu_int": ("gpioc", 13),
        }
        return xiao_pin[pin]

    def adc(adc):
        xiao_adc = {
            0: ("adc1", 0),
            1: ("adc1", 1),
            2: ("adc1", 2),
            3: ("adc1", 3),
            "vbat": ("adc1", 4),
        }
        return xiao_adc[adc]

    def pwm(pwm):
        # PA8 / TIM1_CH1: internal heater-capable PWM, independent of I2C1.
        xiao_pwm = {
            0: ("pwm1", 0),
        }
        return xiao_pwm[pwm]

    def i2c(i2c):
        xiao_i2c = {
            "i2c0": "i2c1",
            "imu": "i2c2",
            "i2c1": "i2c2",
        }
        return xiao_i2c[i2c]

    def uart(uart):
        xiao_uart = {
            "uart0": "usart1",
            "uart1": "usart1",
        }
        return xiao_uart[uart]

    def can(can):
        xiao_can = {
            "can0": "fdcan2",
            "can1": "fdcan1",
        }
        return xiao_can[can]

