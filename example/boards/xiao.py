from sys import implementation, platform
from machine import Pin, PWM, SPI, UART

_machine_name = implementation._machine.lower()

if "stm32c5" in _machine_name:
    from ADC import ADC
    from CAN import CAN
    from RTC import RTC
    from machine import I2C, SoftSPI
    from boards.xiao_stm32c5 import xiao_stm32c5 as xiao
elif "nrf54lm20b" in _machine_name:
    from ADC import ADC
    from PDM import PDM
    from LowPWR import LowPWR
    from RTC import RTC
    from machine import I2C
    from boards.xiao_nrf54lm20b import xiao_nrf54lm20b as xiao
elif "nrf54lm20a" in _machine_name:
    from ADC import ADC
    from PDM import PDM
    from LowPWR import LowPWR
    from RTC import RTC
    from machine import I2C
    from boards.xiao_nrf54lm20a import xiao_nrf54lm20a as xiao
elif "nrf54l15" in _machine_name:
    from ADC import ADC
    from PDM import PDM
    from LowPWR import LowPWR
    from RTC import RTC
    from machine import I2C
    from boards.xiao_nrf54l15 import xiao_nrf54l15 as xiao
elif "mg24" in _machine_name:
    from ADC import ADC
    from RTC import RTC
    from machine import I2C
    from boards.xiao_mg24 import xiao_mg24 as xiao
elif "ra4m1" in _machine_name:
    from machine import ADC, RTC, SoftI2C, SoftSPI
    from boards.xiao_ra4m1 import xiao_ra4m1 as xiao


class XiaoPin(Pin):
    def __init__(self, pin_num, mode=-1, pull=None):
        try:
            super().__init__(xiao.pin(pin_num), mode, pull)
        except Exception:
            raise ValueError("Invalid pin")


class XiaoADC(ADC):
    def __init__(self, adc_num):
        try:
            super().__init__(xiao.adc(adc_num))
        except Exception:
            raise ValueError("Invalid adc")


class XiaoPWM(PWM):
    def __init__(self, pwm_num):
        try:
            super().__init__(xiao.pwm(pwm_num))
        except Exception:
            raise ValueError("Invalid pwm")


if "ra4m1" in _machine_name:
    class XiaoI2C(SoftI2C):
        def __init__(self, i2c_num, sda_num, scl_num, freq_num=400000):
            try:
                super().__init__(scl=xiao.pin(scl_num), sda=xiao.pin(sda_num))
            except Exception:
                raise ValueError("Invalid i2c")

    class XiaoSPI(SoftSPI):
        def __init__(self, spi_num, baudrate_num, sck_num, mosi_num, miso_num):
            try:
                super().__init__(
                    baudrate=baudrate_num,
                    polarity=0,
                    phase=0,
                    bits=8,
                    firstbit=SoftSPI.MSB,
                    sck=xiao.pin(sck_num),
                    mosi=xiao.pin(mosi_num),
                    miso=xiao.pin(miso_num),
                )
            except Exception:
                raise ValueError("Invalid spi")
elif "stm32c5" in _machine_name:
    # The XIAO header exposes no hardware SPI on this board: D8 (PA15)
    # carries no SPI-SCK alternate function (STM32C5A3 DS15137 Table 14),
    # so the header SPI pins are bit-banged. The Zephyr port's SoftSPI
    # requires machine.Pin objects (mp_hal_get_pin_obj), hence the XiaoPin
    # wrappers instead of the raw xiao.pin() tuples used on ra4m1.
    class XiaoI2C(I2C):
        def __init__(self, i2c_num, sda_num=None, scl_num=None, freq=400000):
            try:
                super().__init__(xiao.i2c(i2c_num))
            except Exception:
                raise ValueError("Invalid i2c")

    class XiaoSPI(SoftSPI):
        def __init__(self, spi_num=None, baudrate_num=500000,
                     sck_num=8, mosi_num=10, miso_num=9,
                     polarity=0, phase=0):
            try:
                super().__init__(
                    baudrate=baudrate_num,
                    polarity=polarity,
                    phase=phase,
                    bits=8,
                    firstbit=SoftSPI.MSB,
                    sck=XiaoPin(sck_num, Pin.OUT),
                    mosi=XiaoPin(mosi_num, Pin.OUT),
                    miso=XiaoPin(miso_num, Pin.IN),
                )
            except Exception:
                raise ValueError("Invalid spi")

else:
    class XiaoI2C(I2C):
        if platform == "esp32":
            def __init__(self, i2c_num, sda_num, scl_num, freq_num=400000):
                try:
                    super().__init__(
                        xiao.i2c(i2c_num),
                        sda=xiao.pin(sda_num),
                        scl=xiao.pin(scl_num),
                        freq=freq_num,
                    )
                except Exception:
                    raise ValueError("Invalid i2c")
        else:
            def __init__(self, i2c_num, sda_num=None, scl_num=None, freq=400000):
                try:
                    super().__init__(xiao.i2c(i2c_num))
                except Exception:
                    raise ValueError("Invalid i2c")

    class XiaoSPI(SPI):
        if platform == "esp32":
            def __init__(self, spi_num, baudrate_num, sck_num, mosi_num, miso_num):
                try:
                    super().__init__(
                        xiao.spi(spi_num),
                        baudrate=baudrate_num,
                        sck=xiao.pin(sck_num),
                        mosi=xiao.pin(mosi_num),
                        miso=xiao.pin(miso_num),
                    )
                except Exception:
                    raise ValueError("Invalid spi")
        else:
            def __init__(self, spi_num, baudrate_num, sck_num, mosi_num, miso_num):
                try:
                    super().__init__(
                        xiao.spi(spi_num),
                        baudrate=baudrate_num,
                        polarity=0,
                        phase=0,
                        bits=8,
                        firstbit=SPI.MSB,
                    )
                except Exception:
                    raise ValueError("Invalid spi")


class XiaoUART(UART):
    if platform == "esp32":
        def __init__(self, uart_num, baudrate_num, tx_num, rx_num):
            try:
                super().__init__(
                    xiao.uart(uart_num),
                    baudrate=baudrate_num,
                    tx=xiao.pin(tx_num),
                    rx=xiao.pin(rx_num),
                )
            except Exception:
                raise ValueError("Invalid uart")
    else:
        def __init__(self, uart_num, baudrate_num, tx_num=None, rx_num=None):
            try:
                # Zephyr owns the fixed USART pin mux from the board DTS.
                super().__init__(xiao.uart(uart_num), baudrate=baudrate_num)
            except Exception:
                raise ValueError("Invalid uart")


if "stm32c5" in _machine_name:
    class XiaoCAN(CAN):
        def __init__(self, can_num="can0", **kwargs):
            try:
                super().__init__(xiao.can(can_num), **kwargs)
            except Exception as exc:
                raise ValueError("Invalid can: " + str(exc))


class XiaoRTC(RTC):
    if platform == "esp32" or platform == "renesas-ra":
        def __init__(self):
            try:
                self._rtc = RTC()
            except Exception:
                raise ValueError("Invalid rtc")

        def set_datetime(self, datetime_tuple):
            self._rtc.datetime(
                (
                    datetime_tuple[0], datetime_tuple[1], datetime_tuple[2],
                    0, datetime_tuple[3], datetime_tuple[4], datetime_tuple[5], 0,
                )
            )

        def get_datetime(self):
            t = self._rtc.datetime()
            return (t[0], t[1], t[2], t[4], t[5], t[6])
    else:
        def __init__(self):
            try:
                super().__init__()
            except Exception:
                raise ValueError("Invalid rtc")


if "nrf54lm20a" in _machine_name or "nrf54lm20b" in _machine_name or "nrf54l15" in _machine_name:
    class XiaoPDM(PDM):
        def __init__(self, pdm_num):
            try:
                super().__init__(xiao.pdm(pdm_num))
            except Exception:
                raise ValueError("Invalid pdm")

    class XiaoLowPWR(LowPWR):
        def __init__(self):
            try:
                super().__init__()
            except Exception:
                raise ValueError("Invalid lowpwr")
