class xiao_ra4m1:
    def pin(pin):
        xiao_pin = {
            0: "P014",
            1: "P000",
            2: "P001",
            3: "P002",
            4: "P206",
            5: "P100",
            6: "P302",
            7: "P301",
            8: "P111",
            9: "P110",
            10: "P109",
            "led": "P011",
            "sw": "P201",
            "vbat_en": "P400",
        }
        return xiao_pin[pin]

    def adc(adc):
        xiao_adc = {
            0: "P014",
            1: "P000",
            2: "P001",
            3: "P002",
            4: "P206",
            5: "P100",
            6: "P302",
            7: "P301",
            8: "P111",
            9: "P110",
            10: "P109",
            "vbat": "P015",
        }
        return xiao_adc[adc]
    
    def pwm(pwm):
        xiao_pwm = {
            5: "P100",
            6: "P302",
            7: "P301",
            8: "P111",
            9: "P110",
            10: "P109",
        }
        return xiao_pwm[pwm]
    
    def i2c(i2c):
        xiao_i2c = {
            "i2c0": 1,
        }
        return xiao_i2c[i2c]

    def spi(spi):
        xiao_spi = {
            "spi0": 0,
        }
        return xiao_spi[spi]
    
    def uart(uart):
        xiao_uart = {
            "uart1": 2,
        }
        return xiao_uart[uart]
    


