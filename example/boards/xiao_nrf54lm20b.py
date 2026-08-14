class xiao_nrf54lm20b:
    """XIAO nRF54LM20B pin and peripheral aliases."""

    @staticmethod
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
            "led": ("gpio1", 23),
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

    @staticmethod
    def adc(pin):
        # XiaoADC() takes an XIAO silk-screen D pin number, not an nRF SAADC
        # AIN number.  The nRF54LM20B ADC-capable pins are:
        # D0/D1/D2/D3/D4/D8/D9/D10 = AIN0/AIN1/AIN2/AIN3/AIN7/AIN6/AIN5/AIN4.
        xiao_adc = {
            0: ("adc", 0),
            1: ("adc", 1),
            2: ("adc", 2),
            3: ("adc", 3),
            4: ("adc", 7),
            8: ("adc", 6),
            9: ("adc", 5),
            10: ("adc", 4),
        }
        return xiao_adc[pin]

    @staticmethod
    def pwm(pwm):
        # The board's MicroPython PWM output is PWM20 channel 0 on D8/P1.04.
        # D8 is also SPI0 SCK, so PWM and hardware SPI0 are mutually exclusive.
        return {0: ("pwm20", 0)}[pwm]

    @staticmethod
    def i2c(i2c):
        return {"i2c0": "i2c22", "i2c1": "i2c30"}[i2c]

    @staticmethod
    def spi(spi):
        return {"spi0": "spi23"}[spi]

    @staticmethod
    def uart(uart):
        return {"uart0": "uart20", "uart1": "uart21"}[uart]

    @staticmethod
    def pdm(pdm):
        return {"pdm0": "pdm20"}[pdm]
