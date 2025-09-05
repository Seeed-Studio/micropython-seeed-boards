from sys import implementation, platform
from machine import Pin, PWM, I2C, SPI, UART

if "nrf54l15" in implementation._machine:
    from ADC import ADC
    from PDM import PDM
    from LowPWR import LowPWR
    from RTC import RTC
    from boards.xiao_nrf54l15 import xiao_nrf54l15 as xiao
elif "ESP32C5" in implementation._machine:
    from machine import ADC, RTC
    from boards.xiao_esp32c5 import xiao_esp32c5 as xiao

class XiaoPin(Pin):
    def __init__(self, pin_num, mode=-1, pull=None):
        try:
            super().__init__(xiao.pin(pin_num), mode, pull)
        except:
            raise ValueError("Invalid pin")
        
class XiaoADC(ADC):
    def __init__(self, adc_num):
        try:
            super().__init__(xiao.adc(adc_num))
        except:
            raise ValueError("Invalid adc")

class XiaoPWM(PWM):
    def __init__(self, pwm_num):
        try:
            super().__init__(xiao.pwm(pwm_num))
        except:
            raise ValueError("Invalid pwm")

class XiaoI2C(I2C):
    if platform == "esp32":
        def __init__(self, i2c_num, sda_num, scl_num, freq_num=400000):
            try:
                super().__init__(xiao.i2c(i2c_num), sda=xiao.pin(sda_num), scl=xiao.pin(scl_num), freq=freq_num)
            except:
                raise ValueError("Invalid i2c")
    else:
        def __init__(self, i2c_num, sda_num, scl_num, freq=400000):
            try:
                super().__init__(xiao.i2c(i2c_num))
            except:
                raise ValueError("Invalid i2c")

class XiaoSPI(SPI):
    if platform == "esp32":
        def __init__(self, spi_num, baudrate_num, sck_num, mosi_num, miso_num):
            try:
                super().__init__(xiao.spi(spi_num), baudrate=baudrate_num, sck=xiao.pin(sck_num), mosi=xiao.pin(mosi_num), miso=xiao.pin(miso_num))
            except:
                raise ValueError("Invalid spi")
    else:
        def __init__(self, spi_num, baudrate_num, sck_num, mosi_num, miso_num):
            try:
                super().__init__(xiao.spi(spi_num), baudrate=baudrate_num, polarity=0, phase=0, bits=8, firstbit=SPI.MSB)
            except:
                raise ValueError("Invalid spi")

class XiaoUART(UART):
    if platform == "esp32":
        def __init__(self, uart_num, baudrate_num, tx_num, rx_num):
            try:
                super().__init__(xiao.uart(uart_num), baudrate=baudrate_num, tx=xiao.pin(tx_num), rx=xiao.pin(rx_num))
            except:
                raise ValueError("Invalid uart")
    else:
       def __init__(self, uart_num, baudrate_num, tx_num, rx_num):
            try:
                super().__init__(xiao.uart(uart_num), baudrate=baudrate_num)
            except:
                raise ValueError("Invalid uart")


class XiaoRTC(RTC):
    if platform == "esp32":
        def __init__(self):
            try:
                self._rtc = RTC()
            except:
                raise ValueError("Invalid rtc")
        def set_datetime(self, datetime_tuple):
            self._rtc.datetime((datetime_tuple[0], datetime_tuple[1], datetime_tuple[2], 
                               0, datetime_tuple[3], datetime_tuple[4], datetime_tuple[5], 0))    
        def get_datetime(self):
            t = self._rtc.datetime()
            return (t[0], t[1], t[2], t[4], t[5], t[6])
    else:
        def __init__(self):
            try:
                super().__init__()
            except:
                raise ValueError("Invalid rtc")

if platform == "zephyr":
    class XiaoPDM(PDM):
        def __init__(self, pdm_num):
            try:
                super().__init__(xiao.pdm(pdm_num))
            except:
                raise ValueError("Invalid pdm")
            
    class XiaoLowPWR(LowPWR):
        def __init__(self):
            try:
                super().__init__()
            except:
                raise ValueError("Invalid lowpwr")


        
        