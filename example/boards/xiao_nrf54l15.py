class xiao_nrf54l15:
    def pin(pin):
        xiao_pin = {
            0: ("gpio1", 4),   
            1: ("gpio1", 5),   
            2: ("gpio1", 6),   
            3: ("gpio1", 7),   
            4: ("gpio1", 10),  
            5: ("gpio1", 1),   
            6: ("gpio2", 8),   
            7: ("gpio2", 7),  
            8: ("gpio2", 1),   
            9: ("gpio2", 4),   
            10: ("gpio2", 2),
            "led": ("gpio2", 0),
            "sw": ("gpio0", 0),
            "en": ("gpio0", 1),
            "vbat_en": ("gpio1", 15),
            "imu_en": ("gpio0", 1),
            "mic_en": ("gpio0", 1),
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
            "spi0": "spi00",
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

