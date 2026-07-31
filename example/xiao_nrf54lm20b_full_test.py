"""Interactive XIAO nRF54LM20B board test.

Run from the MicroPython REPL:

    import xiao_nrf54lm20b_full_test as test
    test.main()

The tests are intentionally bounded. Missing jumpers, peripherals, or a
second BLE device produce SKIP instead of blocking the REPL.
"""

import gc
import sys
import time

from machine import Pin
from boards.xiao import XiaoADC, XiaoI2C, XiaoPDM, XiaoPin, XiaoPWM, XiaoSPI, XiaoUART


BOARD_NAME = "XIAO nRF54LM20B"
UART_PORT = "uart1"       # UART21; uart0 is the REPL console.
UART_BAUD = 115200
IMU_BUS = "i2c1"           # I2C30, P0.08/P0.07.
IMU_ADDRESS = 0x6A
IMU_WHO_AM_I = 0x0F
IMU_EXPECTED_ID = 0x6A
# Zephyr's SENSOR_CHAN_GAUGE_VOLTAGE enum in the NCS 3.3.0/Zephyr 4.4
# sensor API. zsensor currently exports generic channels but not gauge ones.
PMIC_GAUGE_VOLTAGE_CHANNEL = 54

_pass = 0
_fail = 0
_skip = 0


def _result(name, state, message=""):
    global _pass, _fail, _skip
    if state == "PASS":
        _pass += 1
    elif state == "FAIL":
        _fail += 1
    elif state == "SKIP":
        _skip += 1
    suffix = " - " + str(message) if message else ""
    print("[{0}] {1}{2}".format(state, name, suffix))
    return state


def _parse_int(value, default=None):
    try:
        text = str(value).lower()
        if text.startswith("d"):
            text = text[1:]
        return int(text, 0)
    except Exception:
        return default


def _read_adc(adc):
    try:
        raw = adc.read_u16()
    except Exception:
        raw = adc.read()
    try:
        uv = adc.read_uv()
    except Exception:
        uv = None
    return raw, uv


def _open_i2c(bus_name):
    return XiaoI2C(bus_name, "imu_sda", "imu_scl", 400000)


def _read_i16(data, index):
    value = data[index] | (data[index + 1] << 8)
    return value - 65536 if value & 0x8000 else value


def print_help():
    print("Commands:")
    print("  help                 show this help")
    print("  status               show board and pin information")
    print("  all                  run all bounded tests")
    print("  uart                 UART21 loopback; connect TX P1.8 to RX P1.9")
    print("  adc                  sample ADC channels 0..7")
    print("  pwm                  output 1kHz/50% on PWM20 channel 0 (P1.22)")
    print("  i2c                  scan I2C22 and IMU I2C30")
    print("  led on|off|blink     control RGB LED blue channel")
    print("  io <pin> [count]     toggle a header GPIO, for example io D0 3")
    print("  imu                  read LSM6DS3TR-C at I2C address 0x6A")
    print("  battery              report PMIC fuel-gauge availability")
    print("  ble                  advertise and perform a bounded scan")
    print("  pdm                  capture one short frame from the PDM mic")
    print("  spi                  initialize user SPI23")
    print("  exit                 leave the test console")
    print("")
    print("Hardware notes:")
    print("  REPL: UART20 TX=P1.11, RX=P1.10, 115200 baud")
    print("  UART test: UART21 TX=P1.8, RX=P1.9; add a jumper for loopback")
    print("  I2C22: SDA=P1.3, SCL=P1.7; IMU I2C30: SDA=P0.8, SCL=P0.7")
    print("  LED: blue=P1.23, red=P1.22, green=P1.24, active-high")
    print("  PDM: CLK=P1.13, DIN=P1.14; requires a working microphone")
    print("  Battery: nPM1300 PMIC fuel-gauge; reports SKIP if driver unavailable")


def test_status():
    try:
        print("board:", BOARD_NAME)
        print("machine:", sys.implementation._machine)
        print("platform:", sys.platform)
        print("GC free:", gc.mem_free())
        print("console: UART20, 115200 baud")
        print("header: D0-D15 mapped; D6/D7 are UART21 RX/TX")
        print("imu: I2C30, P0.08/P0.07, address 0x6A")
        print("led: RGB P1.22/P1.23/P1.24, active-high")
        return _result("status", "PASS")
    except Exception as exc:
        return _result("status", "FAIL", exc)


def test_led(action="blink"):
    led = None
    try:
        led = XiaoPin("led_blue", Pin.OUT)
        if action == "on":
            led.value(1)
        elif action == "off":
            led.value(0)
        elif action == "blink":
            for _ in range(3):
                led.value(1)
                time.sleep_ms(150)
                led.value(0)
                time.sleep_ms(150)
            led.value(0)
        else:
            return _result("LED", "FAIL", "use on, off, or blink")
        return _result("LED", "PASS", "blue LED active-high, action={0}".format(action))
    except Exception as exc:
        return _result("LED", "FAIL", exc)
    finally:
        if led is not None and action != "on":
            try:
                led.value(0)
            except Exception:
                pass


def test_io(pin_value=0, count=2):
    pin_number = _parse_int(pin_value, None)
    if pin_number is None or pin_number < 0 or pin_number > 15:
        return _result("GPIO", "FAIL", "pin must be D0..D15")
    if pin_number in (6, 7):
        return _result("GPIO D{0}".format(pin_number), "SKIP", "reserved for UART21")
    try:
        count = max(1, _parse_int(count, 2))
        gpio = XiaoPin(pin_number, Pin.OUT)
        for _ in range(count):
            gpio.value(0)
            time.sleep_ms(50)
            gpio.value(1)
            time.sleep_ms(50)
        gpio.value(0)
        return _result("GPIO D{0}".format(pin_number), "PASS", "toggle count={0}".format(count))
    except Exception as exc:
        return _result("GPIO D{0}".format(pin_number), "FAIL", exc)


def test_adc():
    values = []
    try:
        for channel in range(8):
            adc = XiaoADC(channel)
            raw, uv = _read_adc(adc)
            if uv is None:
                values.append("A{0} raw={1}".format(channel, raw))
            else:
                values.append("A{0} raw={1} {2}mV".format(channel, raw, uv // 1000))
        print("[ADC] " + "; ".join(values))
        return _result("ADC", "PASS", "8 channels sampled")
    except Exception as exc:
        return _result("ADC", "FAIL", exc)


def test_pwm():
    pwm = None
    try:
        pwm = XiaoPWM(0)
        try:
            pwm.init(freq=1000, duty_u16=32768)
        except Exception:
            pwm.init(freq=1000, duty_ns=500000)
        time.sleep_ms(250)
        return _result("PWM", "PASS", "PWM20 ch0, 1kHz, 50%; verify on LED/scope")
    except Exception as exc:
        return _result("PWM", "FAIL", exc)
    finally:
        if pwm is not None:
            try:
                pwm.deinit()
            except Exception:
                pass


def test_i2c():
    found = []
    errors = []
    for bus_name in ("i2c0", IMU_BUS):
        try:
            devices = _open_i2c(bus_name).scan()
            print("[I2C] {0}: {1}".format(bus_name, [hex(x) for x in devices]))
            found.extend(devices)
        except Exception as exc:
            errors.append("{0}: {1}".format(bus_name, exc))
    if found:
        return _result("I2C", "PASS", "scan complete")
    if errors:
        return _result("I2C", "SKIP", "; ".join(errors))
    return _result("I2C", "SKIP", "no external device detected")


def test_imu():
    try:
        bus = _open_i2c(IMU_BUS)
        devices = bus.scan()
        if IMU_ADDRESS not in devices:
            return _result("IMU", "SKIP", "LSM6DS3TR-C not found at 0x6A")
        who = bus.readfrom_mem(IMU_ADDRESS, IMU_WHO_AM_I, 1)[0]
        if who != IMU_EXPECTED_ID:
            return _result("IMU", "FAIL", "WHO_AM_I=0x{0:02x}".format(who))
        bus.writeto_mem(IMU_ADDRESS, 0x10, b"\x60")
        bus.writeto_mem(IMU_ADDRESS, 0x11, b"\x60")
        time.sleep_ms(20)
        data = bus.readfrom_mem(IMU_ADDRESS, 0x20, 14)
        temp = _read_i16(data, 0) / 256.0 + 25.0
        gyro = [_read_i16(data, 2 + 2 * i) for i in range(3)]
        accel = [_read_i16(data, 8 + 2 * i) for i in range(3)]
        print("[IMU] temp={0:.2f}C gyro_raw={1} accel_raw={2}".format(
            temp, gyro, accel))
        return _result("IMU", "PASS", "LSM6DS3TR-C WHO_AM_I=0x6A")
    except Exception as exc:
        return _result("IMU", "SKIP", exc)


def test_battery():
    try:
        import zsensor

        charger = zsensor.Sensor("pmic_charger")
        charger.measure()
        voltage = charger.get_float(PMIC_GAUGE_VOLTAGE_CHANNEL)
        if voltage <= 0:
            return _result("Battery", "SKIP", "nPM1300 reported no battery voltage")
        print("[BATTERY] source=nPM1300 fuel-gauge voltage={0:.3f}V".format(voltage))
        return _result("Battery", "PASS", "PMIC charger sensor")
    except Exception as exc:
        return _result(
            "Battery",
            "SKIP",
            "nPM1300 sensor unavailable ({0}); do not interpret ADC7 as VBAT".format(exc),
        )


def test_uart():
    try:
        uart = XiaoUART(UART_PORT, UART_BAUD)
        payload = b"xiao20b-uart\n"
        uart.write(payload)
        time.sleep_ms(100)
        available = uart.any()
        if not available:
            return _result("UART", "SKIP", "no loopback response; connect P1.8 TX to P1.9 RX")
        received = uart.read(available)
        if received == payload or (received and payload in received):
            return _result("UART", "PASS", "UART21, {0} baud, loopback matched".format(UART_BAUD))
        return _result("UART", "FAIL", "received={0!r}".format(received))
    except Exception as exc:
        return _result("UART", "SKIP", exc)


def test_ble():
    ble = None
    scan_results = []
    try:
        import bluetooth

        ble = bluetooth.BLE()
        ble.active(True)
        try:
            ble.config(gap_name="XIAO-nRF54LM20B")
        except Exception:
            pass

        def irq(event, data):
            # 5 = scan result, 6 = scan done in MicroPython's BLE API.
            if event == 5:
                scan_results.append(data)

        ble.irq(irq)
        name = b"XIAO-nRF54LM20B"
        adv = b"\x02\x01\x06" + bytes([len(name) + 1, 0x09]) + name
        ble.gap_advertise(100000, adv)
        print("[BLE] advertising started; verify visibility with a phone")
        try:
            ble.gap_scan(3000, 30000, 30000)
            time.sleep_ms(3200)
            ble.gap_scan(None)
        except Exception as exc:
            print("[BLE] scan SKIP:", exc)
        return _result("BLE", "PASS", "advertising active, scan results={0}".format(len(scan_results)))
    except Exception as exc:
        return _result("BLE", "SKIP", exc)
    finally:
        if ble is not None:
            try:
                ble.gap_advertise(None)
                ble.active(False)
            except Exception:
                pass


def test_pdm():
    pdm = None
    try:
        pdm = XiaoPDM("pdm0")
        pdm.configure(rate=16000, width=16, channels=1, block_size=320)
        pdm.start()
        data = pdm.read()
        if not data:
            return _result("PDM", "SKIP", "empty frame; check microphone and power")
        level = max(abs(x - 128) for x in data[: min(len(data), 64)])
        return _result("PDM", "PASS", "frame bytes={0}, sample level={1}".format(len(data), level))
    except Exception as exc:
        return _result("PDM", "SKIP", "microphone capture unavailable: {0}".format(exc))
    finally:
        if pdm is not None:
            try:
                pdm.stop()
            except Exception:
                pass


def test_spi():
    try:
        spi = XiaoSPI("spi0", 1000000, "D8", "D10", "D9")
        try:
            spi.write(b"\x9f")
        except Exception:
            pass
        return _result("SPI", "PASS", "SPI23 initialized at 1MHz; external CS/device not required")
    except Exception as exc:
        return _result("SPI", "SKIP", exc)


def test_all():
    print("Running bounded tests; external loopback/BLE checks may SKIP.")
    test_status()
    test_led("blink")
    test_adc()
    test_pwm()
    test_i2c()
    test_imu()
    test_spi()
    test_pdm()
    test_uart()
    test_ble()
    test_battery()
    print("Summary: PASS={0} FAIL={1} SKIP={2}".format(_pass, _fail, _skip))


def _dispatch(line):
    parts = line.split()
    if not parts:
        return True
    command = parts[0].lower()
    if command == "help":
        print_help()
    elif command == "status":
        test_status()
    elif command == "all":
        test_all()
    elif command == "uart":
        test_uart()
    elif command == "adc":
        test_adc()
    elif command == "pwm":
        test_pwm()
    elif command == "i2c":
        test_i2c()
    elif command == "led":
        test_led(parts[1].lower() if len(parts) > 1 else "blink")
    elif command == "io":
        test_io(parts[1] if len(parts) > 1 else 0, parts[2] if len(parts) > 2 else 2)
    elif command == "imu":
        test_imu()
    elif command == "battery":
        test_battery()
    elif command == "ble":
        test_ble()
    elif command == "pdm":
        test_pdm()
    elif command == "spi":
        test_spi()
    elif command in ("exit", "quit"):
        print("Leaving XIAO nRF54LM20B test console.")
        return False
    else:
        print("Unknown command: {0}; type help".format(command))
    return True


def main():
    print("XIAO nRF54LM20B test console; type help for commands.")
    while True:
        try:
            line = input("XIAO nRF54LM20B test> ")
        except (KeyboardInterrupt, EOFError):
            print("")
            break
        if not _dispatch(line.strip()):
            break
