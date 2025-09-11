class xiao_esp32c5:
    def pin(pin):
        xiao_pin = {
            0: 1,
            1: 0,
            2: 25,
            3: 7,
            4: 23,
            5: 24,
            6: 11,
            7: 12,
            8: 9,
            9: 8,
            10: 10,
            "led": 27,
            "sw": 28,
            "vbat": 6,
            "vbat_en": 26,
        }
        return xiao_pin[pin]

    def adc(adc):
        xiao_adc = {
            0: 1,
            1: 0,
            2: 25,
            3: 7,
            4: 23,
            5: 24,
            6: 11,
            7: 12,
            8: 9,
            9: 8,
            10: 10,
            "vbat": 6,
        }
        return xiao_adc[adc]

    def pwm(pwm):
        xiao_pwm = {
            0: 1,
            1: 0,
            2: 25,
            3: 7,
            4: 23,
            5: 24,
            6: 11,
            7: 12,
            8: 9,
            9: 8,
            10: 10,
        }
        return xiao_pwm[pwm]

    def i2c(i2c):
        xiao_i2c = {
            "i2c0": 0,
        }
        return xiao_i2c[i2c]

    def spi(spi):
        xiao_spi = {
            "spi0": 1,
        }
        return xiao_spi[spi]

    def uart(uart):
        xiao_uart = {
            "uart0": 0,
            "uart1": 1,
        }
        return xiao_uart[uart]
