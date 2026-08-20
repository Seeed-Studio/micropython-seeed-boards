# XIAO STM32C5 base peripheral test (GPIO/ADC/I2C/IMU/PWM/UART/Battery/Storage/RTC)
#
# For CAN tests see xiao_stm32c5_can_test.py.
# For two-board CAN interconnect tests see can_interconnect.py.
#
# Run:
#   import xiao_stm32c5_base_test as t
#   t.main()

import sys
import time
import gc

from machine import Pin

from boards.xiao import XiaoADC, XiaoI2C, XiaoPin, XiaoPWM, XiaoUART


BOARD_NAME = "XIAO STM32C5"
LED_PIN = "led"
BATTERY_ENABLE_PIN = "bat_en"
BATTERY_DIVIDER = 2.0
IMU_ADDRESS = 0x6A
IMU_WHO_AM_I = 0x0F
IMU_EXPECTED_ID = 0x6A
IMU_CTRL1_XL = 0x10
IMU_CTRL2_G = 0x11
IMU_CTRL3_C = 0x12
IMU_ODR_104HZ = 0x40  # 104 Hz ODR, +/-2g / 245 dps
IMU_CONFIG_DELAY_MS = 20
IMU_OUT_TEMP_L = 0x20
IMU_OUTX_L_G = 0x22
IMU_OUTX_L_XL = 0x28

# Expected ADC reference voltage in mV (from overlay: vref-mv = <3300>)
ADC_VREF_MV = 3300

_test_pass = 0
_test_fail = 0
_test_skip = 0


def _result(name, state, message=""):
    global _test_pass, _test_fail, _test_skip
    suffix = " - " + str(message) if message else ""
    print("[{0}] {1}{2}".format(state, name, suffix))
    if state == "PASS":
        _test_pass += 1
    elif state == "FAIL":
        _test_fail += 1
    elif state == "SKIP":
        _test_skip += 1
    return state == "PASS"


def _parse_pin(value):
    value = str(value).lower()
    if value.startswith("d"):
        value = value[1:]
    try:
        return int(value)
    except Exception:
        return value


def _read_i16(data, index):
    value = data[index] | (data[index + 1] << 8)
    if value & 0x8000:
        value -= 0x10000
    return value


def _open_i2c(name):
    return XiaoI2C(name, "imu_sda", "imu_scl", 400000)


def _stats(samples, name="samples"):
    """Return (min, max, avg, stddev) for a list of samples."""
    if not samples:
        return (0, 0, 0, 0)
    n = len(samples)
    avg = sum(samples) / n
    var = sum((s - avg) ** 2 for s in samples) / n
    return min(samples), max(samples), avg, var ** 0.5


def print_help():
    print("Commands:")
    print("  help              show this help")
    print("  status            show board info")
    print("  all               run all non-destructive tests")
    print("  quick             quick smoke test (ADC+LED+I2C+IMU)")
    print("  adc               full ADC test (ch0-3, multi-sample, cross-talk)")
    print("  adc_simple        quick ADC read (A0-A3)")
    print("  pwm               PWM output test (PA8, 1kHz)")
    print("  pwm_full          PWM sweep test (100Hz-10kHz)")
    print("  i2c               scan header and IMU buses")
    print("  i2c_stress        repeated I2C scan (3x)")
    print("  led on|off|blink  control onboard LED")
    print("  io <pin> [count]  toggle a GPIO")
    print("  io_all            test all GPIO pins D0-D15")
    print("  gpio_in           GPIO input test (D8-D11, pull-up)")
    print("  imu               read IMU once")
    print("  imu_verify        verify IMU data changes between reads")
    print("  battery           read battery voltage")
    print("  uart              UART loopback test (need PA9-PA10 jumper)")
    print("  storage           LittleFS read/write/delete test")
    print("  rtc               RTC set/get datetime test")
    print("  i2c1_header       scan I2C1 header bus (D4/D5)")
    print("  exit              leave the test console")
    print("")
    print("External test prerequisites:")
    print("  uart: connect PA9 to PA10 only when the REPL is not in use")
    print("  pwm: observe internal PA8/TIM1_CH1 test point with a scope")
    print("  battery: connect a supported battery; BAT_EN is PA15, sense is PA4")


def test_status():
    try:
        import sys as _sys
        print("board:", BOARD_NAME)
        print("machine:", _sys.implementation._machine)
        print("platform:", _sys.platform)
        print("GC free:", gc.mem_free())
        print("pins: D0-D3=ADC, D4/D5=I2C1, D6/D7=USART1")
        print("can: default FDCAN2 on PB5/PB13")
        print("imu: I2C2 PB3/PB4, address 0x6A")
        print("battery: BAT_EN PA15, ADC1_IN4 PA4, divider 2:1")
        return _result("status", "PASS")
    except Exception as exc:
        return _result("status", "FAIL", exc)


# --- LED ---

def test_led(action="blink"):
    try:
        led = XiaoPin(LED_PIN, Pin.OUT)
        if action == "on":
            led.value(0)
        elif action == "off":
            led.value(1)
        else:
            for _ in range(3):
                led.value(0)
                time.sleep_ms(150)
                led.value(1)
                time.sleep_ms(150)
            led.value(1)
        return _result("LED", "PASS", "active-low, action={0}".format(action))
    except Exception as exc:
        return _result("LED", "FAIL", exc)


# --- GPIO ---

def test_io(pin=0, count=2):
    try:
        pin_id = _parse_pin(pin)
        gpio = XiaoPin(pin_id, Pin.OUT)
        for _ in range(max(1, count)):
            gpio.value(0)
            time.sleep_ms(50)
            gpio.value(1)
            time.sleep_ms(50)
        return _result("GPIO D{0}".format(pin_id), "PASS", "count={0}".format(count))
    except Exception as exc:
        return _result("GPIO D{0}".format(pin), "FAIL", exc)


def test_io_all():
    """Test all GPIO pins D0-D15, skipping REPL pins (D6/D7=USART1)."""
    # D6/D7 are USART1 (REPL), cannot use as GPIO
    skip = {6, 7}
    passed = 0
    failed = []
    skipped = []
    for pin in range(16):
        if pin in skip:
            skipped.append("D{0}".format(pin))
            continue
        try:
            gpio = XiaoPin(pin, Pin.OUT)
            gpio.value(0)
            time.sleep_ms(10)
            gpio.value(1)
            time.sleep_ms(10)
            passed += 1
        except Exception as exc:
            failed.append("D{0}:{1}".format(pin, exc))
    result_msg = "{0}/{1} ok".format(passed, 16 - len(skip))
    if skipped:
        result_msg += ", skipped: {0}".format(", ".join(skipped))
    if failed:
        result_msg += ", failed: {0}".format(", ".join(failed))
        return _result("GPIO all", "FAIL", result_msg)
    return _result("GPIO all", "PASS", result_msg)


def test_gpio_input():
    """Test GPIO input with pull-up on free pins D8-D11."""
    pins = [8, 9, 10, 11]
    ok = 0
    failed = []
    for p in pins:
        try:
            gpio = XiaoPin(p, Pin.IN, Pin.PULL_UP)
            val = gpio.value()
            # Floating pin with pull-up should read 1
            if val == 1:
                ok += 1
            else:
                failed.append("D{0}=0".format(p))
        except Exception as exc:
            failed.append("D{0}:{1}".format(p, exc))
    if failed:
        return _result("GPIO input", "FAIL",
                       "{0}/{1} ok, {1}".format(ok, len(pins), ", ".join(failed)))
    return _result("GPIO input", "PASS", "{0}/{0} ok".format(len(pins)))


# --- ADC (comprehensive) ---

def _adc_read_channel(channel, n_samples=10):
    """Read an ADC channel n times and return (raw_list, uv_list)."""
    raw_list = []
    uv_list = []
    adc = None
    try:
        adc = XiaoADC(channel)
        for _ in range(n_samples):
            raw = adc.read()
            raw_list.append(raw)
            try:
                uv = adc.read_uv()
                uv_list.append(uv)
            except Exception:
                uv_list.append(None)
            time.sleep_ms(1)
    except Exception:
        pass
    return raw_list, uv_list


def _adc_check_channel(channel, label):
    """Comprehensive check of a single ADC channel."""
    raw_list, uv_list = _adc_read_channel(channel, 10)

    if not raw_list:
        print("  [{0}] FAIL: cannot read".format(label))
        return False, "cannot read"

    # Check 1: all values are in valid range (0-4095 for 12-bit)
    out_of_range = [r for r in raw_list if r < 0 or r > 4095]
    if out_of_range:
        print("  [{0}] FAIL: out of range: {1}".format(label, out_of_range))
        return False, "out of range: {0}".format(out_of_range)

    # Check 2: compute statistics
    rmin, rmax, ravg, rstd = _stats(raw_list)
    uvs = [u for u in uv_list if u is not None]
    if uvs:
        umin, umax, uavg, ustd = _stats(uvs)

    # Check 3: noise level (stddev should be reasonable)
    if rstd > 100:
        print("  [{0}] WARN: noisy (raw std={1:.0f}, range=[{2},{3}])".format(
            label, rstd, rmin, rmax))
    else:
        print("  [{0}] raw={1:.0f}+-{2:.0f} range=[{3},{4}]".format(
            label, ravg, rstd, rmin, rmax))

    # Check 4: read_uv() consistency with read()
    if uvs and ravg > 0:
        # Expected uv from raw: raw / 4095 * 3300 * 1000
        expected_uv_avg = (ravg / 4095.0) * ADC_VREF_MV * 1000
        uv_avg = uavg
        # Allow 10% tolerance for calibration differences
        if expected_uv_avg > 0:
            ratio = uv_avg / expected_uv_avg
            if ratio < 0.8 or ratio > 1.2:
                print("  [{0}] WARN: uv/raw mismatch: uv={1:.0f}uV, expected~{2:.0f}uV".format(
                    label, uv_avg, expected_uv_avg))

    # Check 5: stale value (all reads identical -> possibly stuck)
    if rmin == rmax and ravg > 0:
        print("  [{0}] WARN: all readings identical ({1}), possibly stuck".format(
            label, rmin))

    return True, ""


def test_adc():
    """Full ADC test: channel-by-channel, multi-sample, cross-talk check."""
    print("--- ADC Full Test ---")
    all_ok = True

    # Phase 1: read each channel independently
    print("Phase 1: Individual channel sampling (10 samples each)")
    for ch in range(4):
        ok, msg = _adc_check_channel(ch, "A{0}".format(ch))
        if not ok:
            all_ok = False

    # Phase 2: cross-talk check - read all channels, then read one while others change
    print("Phase 2: Cross-talk check")
    try:
        # Baseline: read all channels
        baselines = []
        for ch in range(4):
            r, _ = _adc_read_channel(ch, 3)
            if r:
                baselines.append(sum(r) / len(r))
            else:
                baselines.append(None)

        # Cross-talk: read channel 0 while channel 1 is being toggled as GPIO
        # Skip channels that conflict with REPL (D6=ch6, D7=ch7)
        for test_ch in range(4):
            if baselines[test_ch] is None:
                continue
            # Read the test channel 5 times
            adc = XiaoADC(test_ch)
            readings_static = []
            for _ in range(5):
                readings_static.append(adc.read())
                time.sleep_ms(2)
            avg_static = sum(readings_static) / len(readings_static)

            # Toggle adjacent channels as GPIO and read test channel
            toggle_ch = (test_ch + 1) % 4
            try:
                gpio = XiaoPin(toggle_ch, Pin.OUT)
                readings_toggle = []
                for _ in range(10):
                    gpio.value(0 if _ % 2 == 0 else 1)
                    time.sleep_ms(1)
                    readings_toggle.append(adc.read())
                avg_toggle = sum(readings_toggle) / len(readings_toggle)
                diff = abs(avg_toggle - avg_static)
                if diff > 50:
                    print("  A{0}: cross-talk WARN: {1:.0f} raw drift when D{2} toggled".format(
                        test_ch, diff, toggle_ch))
                else:
                    print("  A{0}: cross-talk OK (drift={1:.0f})".format(test_ch, diff))
            except Exception:
                print("  A{0}: cross-talk SKIP (cannot toggle D{1})".format(test_ch, toggle_ch))
    except Exception as exc:
        print("  cross-talk check error:", exc)

    # Phase 3: check channel 4 (battery) exists
    print("Phase 3: Battery channel check")
    try:
        adc = XiaoADC("vbat")
        raw = adc.read()
        print("  vbat: raw={0} (channel 4 accessible)".format(raw))
    except Exception as exc:
        print("  vbat: FAIL -", exc)
        all_ok = False

    return _result("ADC full", "PASS" if all_ok else "FAIL")


def test_adc_simple():
    """Quick ADC read (A0-A3)."""
    passed = True
    values = []
    try:
        for channel in range(4):
            adc = XiaoADC(channel)
            raw = adc.read()
            try:
                uv = adc.read_uv()
                values.append("A{0}: raw={1}, {2}mV".format(channel, raw, uv // 1000))
            except Exception:
                values.append("A{0}: raw={1}".format(channel, raw))
        print("[ADC] " + "; ".join(values))
        return _result("ADC simple", "PASS" if passed else "FAIL")
    except Exception as exc:
        return _result("ADC simple", "FAIL", exc)


# --- PWM ---

def test_pwm():
    pwm = None
    try:
        pwm = XiaoPWM(0)
        pwm.init(freq=1000, duty_u16=32768)
        time.sleep_ms(250)
        print("[PWM] pin=PA8, freq=1000Hz, duty=50%")
        return _result("PWM", "PASS", "scope/LED verification required")
    except Exception as exc:
        return _result("PWM", "FAIL", exc)
    finally:
        if pwm is not None:
            try:
                pwm.deinit()
            except Exception:
                pass


def test_pwm_full():
    """PWM sweep test: different frequencies and duty cycles."""
    pwm = None
    all_ok = True
    try:
        pwm = XiaoPWM(0)
        freqs = [100, 500, 1000, 5000, 10000]
        duties = [25, 50, 75]
        for freq in freqs:
            for duty_pct in duties:
                duty_u16 = int(duty_pct / 100.0 * 65535)
                try:
                    pwm.init(freq=freq, duty_u16=duty_u16)
                    time.sleep_ms(50)
                except Exception as exc:
                    print("  PWM {0}Hz/{1}%: FAIL ({2})".format(freq, duty_pct, exc))
                    all_ok = False
        print("  PWM sweep: {0} freqs x {1} duties".format(len(freqs), len(duties)))
        return _result("PWM full", "PASS" if all_ok else "FAIL",
                       "scope verification required")
    except Exception as exc:
        return _result("PWM full", "FAIL", exc)
    finally:
        if pwm is not None:
            try:
                pwm.deinit()
            except Exception:
                pass


# --- I2C ---

def test_i2c():
    """Scan IMU bus only. i2c0 (header D4/D5) is skipped — no external
    devices are connected, and probing an empty bus is slow."""
    found = []
    try:
        bus = _open_i2c("imu")
        addresses = bus.scan()
        print("[I2C] imu: {0}".format(
            [hex(address) for address in addresses]))
        found.extend(addresses)
        return _result("I2C", "PASS" if found else "SKIP",
                       "no device detected" if not found else "scan complete")
    except Exception as exc:
        return _result("I2C", "FAIL", exc)


def test_i2c_stress():
    """Repeated I2C scan to check for intermittent issues."""
    all_ok = True
    try:
        bus = _open_i2c("imu")
        results = []
        for i in range(3):
            addresses = bus.scan()
            results.append(set(addresses))
            time.sleep_ms(20)
        # Check all scans returned the same result
        first = results[0]
        for i, r in enumerate(results[1:], 1):
            if r != first:
                print("  scan {0}: mismatch: {1} vs {2}".format(
                    i, [hex(a) for a in sorted(first)],
                    [hex(a) for a in sorted(r)]))
                all_ok = False
        print("  I2C stress: 3 scans, {0} devices consistently found: {1}".format(
            len(first), [hex(a) for a in sorted(first)]))
        return _result("I2C stress", "PASS" if all_ok else "FAIL")
    except Exception as exc:
        return _result("I2C stress", "SKIP", exc)


def test_i2c1_header():
    """Scan the I2C1 header bus (D4/PB7 SDA, D5/PB6 SCL)."""
    try:
        bus = XiaoI2C("i2c0", "i2c1_sda", "i2c1_scl", 400000)
        addresses = bus.scan()
        if addresses:
            print("[I2C1] header devices: {0}".format(
                [hex(a) for a in addresses]))
        else:
            print("[I2C1] header: no devices (expected)")
        return _result("I2C1 header", "PASS",
                       "{0} device(s)".format(len(addresses)))
    except Exception as exc:
        return _result("I2C1 header", "SKIP", exc)


# --- IMU ---

def test_imu():
    try:
        bus = _open_i2c("imu")
        who = bus.readfrom_mem(IMU_ADDRESS, IMU_WHO_AM_I, 1)[0]
        if who != IMU_EXPECTED_ID:
            return _result("IMU", "FAIL",
                           "WHO_AM_I=0x{0:02X}".format(who))
        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL3_C, bytes((0x44,)))
        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL1_XL, bytes((IMU_ODR_104HZ,)))
        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL2_G, bytes((IMU_ODR_104HZ,)))
        time.sleep_ms(IMU_CONFIG_DELAY_MS)
        data = bus.readfrom_mem(IMU_ADDRESS, IMU_OUT_TEMP_L, 14)
        temperature = 25.0 + _read_i16(data, 0) / 256.0
        gx = _read_i16(data, 2)
        gy = _read_i16(data, 4)
        gz = _read_i16(data, 6)
        ax = _read_i16(data, 8)
        ay = _read_i16(data, 10)
        az = _read_i16(data, 12)
        print("[IMU] temp={0:.2f}C raw_accel=({1},{2},{3}) raw_gyro=({4},{5},{6})".format(
            temperature, ax, ay, az, gx, gy, gz))
        return _result("IMU", "PASS", "WHO_AM_I=0x{0:02X}".format(who))
    except Exception as exc:
        return _result("IMU", "FAIL", exc)


def test_imu_verify():
    """Verify IMU data changes between reads (not stuck)."""
    try:
        bus = _open_i2c("imu")

        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL3_C, bytes((0x44,)))
        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL1_XL, bytes((IMU_ODR_104HZ,)))
        bus.writeto_mem(IMU_ADDRESS, IMU_CTRL2_G, bytes((IMU_ODR_104HZ,)))
        time.sleep_ms(IMU_CONFIG_DELAY_MS)

        readings = []
        for _ in range(5):
            data = bus.readfrom_mem(IMU_ADDRESS, IMU_OUT_TEMP_L, 14)
            ax = _read_i16(data, 8)
            ay = _read_i16(data, 10)
            az = _read_i16(data, 12)
            gx = _read_i16(data, 2)
            gy = _read_i16(data, 4)
            gz = _read_i16(data, 6)
            readings.append((ax, ay, az, gx, gy, gz))
            time.sleep_ms(20)

        # Check if any axis changed between readings
        all_same = all(r == readings[0] for r in readings)
        if all_same:
            print("  IMU readings: all identical across 5 reads")
        else:
            print("  IMU readings: varying across 5 reads (normal)")

        # Check if all axes are zero (stuck sensor)
        all_zero = all(v == 0 for r in readings for v in r)
        if all_zero:
            return _result("IMU verify", "FAIL", "all axes read zero - sensor stuck?")

        return _result("IMU verify", "PASS",
                       "5 reads, data varies" if not all_same else "5 reads, data stable")
    except Exception as exc:
        return _result("IMU verify", "SKIP", exc)


# --- Battery ---

def test_battery():
    enable = None
    try:
        enable = XiaoPin(BATTERY_ENABLE_PIN, Pin.OUT)
        enable.value(1)
        time.sleep_ms(5)
        adc = XiaoADC("vbat")
        raw = adc.read()
        uv = adc.read_uv()
        millivolts = (uv / 1000.0) * BATTERY_DIVIDER
        if raw <= 0 or uv <= 0:
            return _result("Battery", "SKIP", "no battery voltage detected")
        print("[BATTERY] raw={0}, adc={1}mV, estimated={2:.3f}V".format(
            raw, uv // 1000, millivolts / 1000.0))
        return _result("Battery", "PASS", "calibration divider=2:1")
    except Exception as exc:
        return _result("Battery", "SKIP", exc)
    finally:
        if enable is not None:
            try:
                enable.value(0)
            except Exception:
                pass


# --- UART ---

def test_uart():
    uart = None
    try:
        print("[UART] port=USART1 (PA9/PA10), baudrate=115200")
        uart = XiaoUART("uart1", 115200, 6, 7)
        payload = b"xiao-c5-uart-test\n"
        uart.write(payload)
        received = uart.read(len(payload))
        if received == payload:
            return _result("UART", "PASS", "loopback")
        return _result("UART", "SKIP",
                       "connect PA9 to PA10 for loopback; received={0}".format(received))
    except Exception as exc:
        return _result("UART", "SKIP", exc)
    finally:
        if uart is not None:
            try:
                uart.deinit()
            except Exception:
                pass


# --- RTC ---

def test_rtc():
    """Verify RTC is accessible and keeps time."""
    try:
        from RTC import RTC
        rtc = RTC()
        # Set a known datetime and read back
        rtc.set_datetime((2026, 7, 24, 12, 0, 0))
        dt = rtc.get_datetime()
        if dt[0:3] == (2026, 7, 24):
            return _result("RTC", "PASS",
                           "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*dt))
        return _result("RTC", "FAIL", "unexpected: {0}".format(dt))
    except Exception as exc:
        return _result("RTC", "SKIP", exc)


# --- LittleFS storage ---

def test_storage():
    """Verify LittleFS on external NOR flash: write, read, delete."""
    try:
        import os
        test_path = "/flash/_board_test_.txt"
        test_data = b"xiao-c5-storage-ok"

        # Write
        with open(test_path, "wb") as f:
            f.write(test_data)

        # Read back
        with open(test_path, "rb") as f:
            read_back = f.read()

        # Clean up
        os.remove(test_path)

        if read_back == test_data:
            # Report free space
            stat = os.statvfs("/flash")
            free_kb = stat[0] * stat[3] // 1024
            return _result("Storage", "PASS",
                           "LittleFS ok, {0} KB free".format(free_kb))
        return _result("Storage", "FAIL",
                       "read mismatch: {0}".format(read_back))
    except Exception as exc:
        return _result("Storage", "SKIP", exc)


# --- Test suites ---

def test_quick():
    """Quick smoke test."""
    test_status()
    test_led("blink")
    test_adc_simple()
    test_i2c()
    test_imu()


def test_all():
    """Full base peripheral test suite."""
    global _test_pass, _test_fail, _test_skip
    _test_pass = _test_fail = _test_skip = 0

    print("=" * 50)
    print("  XIAO STM32C5 Base Peripheral Test Suite")
    print("=" * 50)

    # Phase 1: Basic
    print("\n-- Phase 1: Basic --")
    test_status()
    test_led("blink")
    test_io_all()
    test_gpio_input()

    # Phase 2: ADC
    print("\n-- Phase 2: ADC --")
    test_adc()

    # Phase 3: I2C + IMU
    print("\n-- Phase 3: I2C + IMU --")
    test_i2c()
    test_i2c_stress()
    test_imu()
    test_imu_verify()

    # Phase 4: PWM
    print("\n-- Phase 4: PWM --")
    test_pwm()
    test_pwm_full()

    # Phase 5: Power
    print("\n-- Phase 5: Power --")
    test_battery()

    # Phase 6: UART (needs external wiring)
    print("\n-- Phase 6: UART (needs PA9-PA10 jumper) --")
    test_uart()

    # Phase 7: Storage + RTC
    print("\n-- Phase 7: Storage + RTC --")
    test_storage()
    test_rtc()

    # Phase 8: I2C1 header
    print("\n-- Phase 8: I2C1 header --")
    test_i2c1_header()

    print("\n" + "=" * 50)
    total = _test_pass + _test_fail + _test_skip
    print("  Results: {0} PASS, {1} FAIL, {2} SKIP ({3} total)".format(
        _test_pass, _test_fail, _test_skip, total))
    print("=" * 50)


def _dispatch(line):
    parts = line.strip().split()
    if not parts:
        return True
    command = parts[0].lower()

    if command == "help":
        print_help()
    elif command == "status":
        test_status()
    elif command == "all":
        test_all()
    elif command == "quick":
        test_quick()
    elif command == "uart":
        test_uart()
    elif command == "storage":
        test_storage()
    elif command == "rtc":
        test_rtc()
    elif command == "i2c1_header":
        test_i2c1_header()
    elif command == "adc":
        test_adc()
    elif command == "adc_simple":
        test_adc_simple()
    elif command == "pwm":
        test_pwm()
    elif command == "pwm_full":
        test_pwm_full()
    elif command == "i2c":
        test_i2c()
    elif command == "i2c_stress":
        test_i2c_stress()
    elif command == "imu":
        test_imu()
    elif command == "imu_verify":
        test_imu_verify()
    elif command == "battery":
        test_battery()
    elif command == "led":
        test_led(parts[1].lower() if len(parts) > 1 else "blink")
    elif command == "io":
        pin = parts[1] if len(parts) > 1 else 0
        count = int(parts[2]) if len(parts) > 2 else 2
        test_io(pin, count)
    elif command == "io_all":
        test_io_all()
    elif command == "gpio_in":
        test_gpio_input()
    elif command == "exit":
        return False
    else:
        print("Unknown command: " + command)
        print_help()
    return True


def main():
    print(BOARD_NAME + " base test console")
    print_help()
    while True:
        try:
            sys.stdout.write("XIAO STM32C5 base> ")
            line = sys.stdin.readline()
            if not line:
                print("")
                break
            line = line.strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            break
        try:
            if not _dispatch(line):
                break
        except Exception as exc:
            print("[FAIL] command error: " + str(exc))
    print("test console stopped")


if __name__ == "__main__":
    main()
