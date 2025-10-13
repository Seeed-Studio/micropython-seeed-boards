class xiao_mg24:
    def pin(pin):
        xiao_pin = {
            0: ("gpioc", 0),   
            1: ("gpioc", 1),   
            2: ("gpioc", 2),   
            3: ("gpioc", 3),   
            4: ("gpioc", 4),  
            5: ("gpioc", 5),   
            6: ("gpioc", 6),   
            7: ("gpioc", 7),  
            8: ("gpioa", 3),   
            9: ("gpioa", 4),   
            10: ("gpioa", 5),
            "led": ("gpioa", 7),
            "sw": ("gpioc", 1),
            "vbat_en": ("gpiod", 3),
        }
        return xiao_pin[pin]
    
    def adc(adc):
        xiao_adc = {
            0: ("adc0", 0),
            1: ("adc0", 1),
            2: ("adc0", 2),
            3: ("adc0", 3),
            4: ("adc0", 4),
            5: ("adc0", 5),
            6: ("adc0", 6),
            7: ("adc0", 7),
            8: ("adc0", 8),
            9: ("adc0", 9),
            10: ("adc0", 10),
            "vbat": ("adc0", 7),
        }
        return xiao_adc[adc]
    
    def pwm(pwm):
        xiao_pwm = {
            0: ("pwm", 0),
            1: ("pwm", 1),
            2: ("pwm", 2),
        }
        return xiao_pwm[pwm]
    
    def i2c(i2c):
        xiao_i2c = {
            "i2c0": "i2c0",
        }
        return xiao_i2c[i2c]

    def spi(spi):
        xiao_spi = {
            "spi0": "eusart0",
        }
        return xiao_spi[spi]

    def uart(uart):
        xiao_uart = {
            "uart0": "usart0",
            "uart1": "eusart1",
        }
        return xiao_uart[uart]


