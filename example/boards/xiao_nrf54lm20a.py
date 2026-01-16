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
            16: ("gpio3", 5),
            17: ("gpio3", 6),
            18: ("gpio3", 7),
            19: ("gpio0", 0),
            20: ("gpio0", 1),
            21: ("gpio0", 2),
            22: ("gpio0", 3),
            23: ("gpio0", 4),
            24: ("gpio0", 5),
            25: ("gpio3", 9),
            26: ("gpio3", 10),
            27: ("gpio3", 11),
            # RGB LED (led_r/led_g/led_b)
            "led_r": ("gpio1", 22),
            "led_g": ("gpio1", 24),
            "led_b": ("gpio1", 23),
            "sw": ("gpio0", 9),
            "en": ("gpio0", 1),
            "power_en": ("gpio1", 12),
            "imu_en": ("gpio0", 1),
            "imu_scl": ("gpio0", 3),
            "imu_sda": ("gpio0", 4),
            "imu_irq": ("gpio0", 6),
            "mic_en": ("gpio0", 1),
            # RF switch control
            "rfsw_ctl": ("gpio1", 28),
            "rfsw_pwr": ("gpio1", 27),
            # PMIC I2C (GPIO bit-banged)
            "pmic_sda": ("gpio1", 15),
            "pmic_scl": ("gpio1", 16),
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
            0: ("pwm20", 0),  # Red LED (gpio1_22)
            1: ("pwm20", 1),  # Blue LED (gpio1_23)
            2: ("pwm20", 2),  # Green LED (gpio1_24)
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
            "spi1": "spi00",
        }
        return xiao_spi[spi]

    def uart(uart):
        xiao_uart = {
            "uart0": "uart20",
            "uart1": "uart21",
        }
        return xiao_uart[uart]

    def pdm(pdm):
        xiao_pdm ={
            "pdm0": "pdm20",
        }
        return xiao_pdm[pdm]

