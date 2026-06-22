class xiao_nrf54lm20a:
    def pin(pin):
        xiao_pin = {
            0: ("gpio1", 0),
            1: ("gpio1", 31),
            2: ("gpio1", 30),
            3: ("gpio1", 29),
            4: ("gpio1", 3),
            5: ("gpio1", 7),
            6: ("gpio1", 8),
            7: ("gpio1", 9),
            8: ("gpio1", 4),
            9: ("gpio1", 5),
            10: ("gpio1", 6),
            11: ("gpio3", 0),
            12: ("gpio3", 1),
            13: ("gpio3", 2),
            14: ("gpio3", 3),
            15: ("gpio3", 4),
            "led": ("gpio1", 22),
            "led_blue": ("gpio1", 23),
            "led_red": ("gpio1", 22),
            "led_green": ("gpio1", 24),
            "led_b": ("gpio1", 23),
            "led_r": ("gpio1", 22),
            "led_g": ("gpio1", 24),
            "sw": ("gpio0", 9),
            "imu_scl": ("gpio0", 7),
            "imu_sda": ("gpio0", 8),
        }
        return xiao_pin[pin]

    def adc(adc):
        xiao_adc = {
            0: ("adc", 0),
            1: ("adc", 1),
            2: ("adc", 2),
            3: ("adc", 3),
            4: ("adc", 4),
            5: ("adc", 5),
            6: ("adc", 6),
            7: ("adc", 7),
            "vbat": ("adc", 7),
        }
        return xiao_adc[adc]

    def pwm(pwm):
        xiao_pwm = {
            0: ("pwm20", 0),
            1: ("pwm20", 1),
            2: ("pwm20", 2),
            3: ("pwm20", 3),
        }
        return xiao_pwm[pwm]

    def i2c(i2c):
        xiao_i2c = {
            "i2c0": "i2c22",
            "i2c1": "i2c30",
        }
        return xiao_i2c[i2c]

    def spi(spi):
        xiao_spi = {
            "spi0": "spi23",
        }
        return xiao_spi[spi]

    def uart(uart):
        xiao_uart = {
            "uart0": "uart20",
            "uart1": "uart21",
        }
        return xiao_uart[uart]

    def pdm(pdm):
        xiao_pdm = {
            "pdm0": "pdm20",
        }
        return xiao_pdm[pdm]
