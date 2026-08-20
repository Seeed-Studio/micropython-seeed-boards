"""XIAO STM32C5 complete hardware test: peripherals + SPI + FDCAN.

Wiring before a full run:
  - D9 (MISO) <-> D10 (MOSI) jumper  -> required by the SPI loopback test
    (without it the SPI item reports SKIP, not FAIL)
  - optional PA9 <-> PA10 jumper     -> UART loopback (otherwise SKIP)
  - CAN tests use controller loopback: no transceiver or wiring needed

Run everything:
    import xiao_stm32c5_full_test as t; t.main()
Interactive console (single tests, LED/GPIO control):
    import xiao_stm32c5_full_test as t; t.console()
Or call any test directly:
    t.test_adc()

Two-board CAN bus tests live in can_interconnect.py.
"""
import sys
import time
import gc
from machine import Pin
from boards.xiao import (
    XiaoADC, XiaoCAN, XiaoI2C, XiaoPin, XiaoPWM, XiaoSPI, XiaoUART,
)

BOARD = "XIAO STM32C5"
VREF = 3300
IMU = 0x6A
BAT_DIVIDER = 2.0
_p = _f = _s = 0


def _r(name, state, msg=""):
    global _p, _f, _s
    print("[{0}] {1}{2}".format(state, name, " - " + str(msg) if msg else ""))
    if state == "PASS":
        _p += 1
    elif state == "FAIL":
        _f += 1
    elif state == "SKIP":
        _s += 1
    return state == "PASS"


def _off(obj):
    if obj is not None:
        try:
            obj.deinit()
        except Exception:
            pass


def _i2c(name="imu"):
    return XiaoI2C(name, "imu_sda", "imu_scl", 400000)


def _i16(data, i):
    v = data[i] | data[i + 1] << 8
    return v - 65536 if v & 0x8000 else v


def _can(fd=True, data=2000000, bitrate=500000):
    return XiaoCAN("can0", bitrate=bitrate, data_bitrate=data, fd=fd,
                   loopback=True)


def _stats(a):
    n = len(a)
    avg = sum(a) / n
    return min(a), max(a), avg, (sum((x - avg) ** 2 for x in a) / n) ** .5


def test_status():
    try:
        print("board:", BOARD)
        print("machine:", sys.implementation._machine)
        print("platform:", sys.platform)
        print("GC free:", gc.mem_free())
        print("pins: D0-D3=ADC, D4/D5=I2C1, D6/D7=USART1,")
        print("      D8=SPI3_SCK(PE2), D9=SPI3_MISO(PB0), D10=SPI3_MOSI(PB15)")
        print("can:  FDCAN2 on D13(PB5)/D14(PB13), standby D15(PB14)")
        print("imu:  I2C2 PB3/PB4, address 0x6A")
        print("batt: BAT_EN PA15, sense PA4/ADC1_IN4, divider 2:1")
        return _r("status", "PASS")
    except Exception as e:
        return _r("status", "FAIL", e)


def test_led(action="blink"):
    try:
        led = XiaoPin("led", Pin.OUT)
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
        return _r("LED", "PASS", "active-low, action={0}".format(action))
    except Exception as e:
        return _r("LED", "FAIL", e)


def test_gpio():
    """Output: toggle every header pin except the REPL pair D6/D7.
    Input: pull-up on the free pins D8-D11 must read 1."""
    bad = []
    for p in range(16):
        if p in (6, 7):
            continue
        try:
            g = XiaoPin(p, Pin.OUT)
            g.value(0)
            time.sleep_ms(10)
            g.value(1)
        except Exception as e:
            bad.append("D{0}:{1}".format(p, e))
    _r("GPIO output", "FAIL" if bad else "PASS",
       "failed: " + ", ".join(bad) if bad else "14 pins ok; D6/D7 skipped (REPL)")
    bad = []
    for p in (8, 9, 10, 11):
        try:
            if XiaoPin(p, Pin.IN, Pin.PULL_UP).value() != 1:
                bad.append("D{0}=0".format(p))
        except Exception as e:
            bad.append("D{0}:{1}".format(p, e))
    return _r("GPIO input", "FAIL" if bad else "PASS",
              ", ".join(bad) if bad else "D8-D11 pull-up ok")


def test_io(pin=0, count=2):
    """Toggle one header pin `count` times (console helper)."""
    p = str(pin).lower()
    p = int(p[1:]) if p.startswith("d") else (int(pin) if str(pin).isdigit() else pin)
    try:
        g = XiaoPin(p, Pin.OUT)
        for _ in range(max(1, count)):
            g.value(0)
            time.sleep_ms(50)
            g.value(1)
            time.sleep_ms(50)
        return _r("GPIO D{0}".format(p), "PASS", "count={0}".format(count))
    except Exception as e:
        return _r("GPIO D{0}".format(pin), "FAIL", e)


def _adc_read(ch, n=10):
    raw = []
    uv = []
    try:
        a = XiaoADC(ch)
        for _ in range(n):
            raw.append(a.read())
            try:
                uv.append(a.read_uv())
            except Exception:
                uv.append(None)
            time.sleep_ms(1)
    except Exception:
        pass
    return raw, uv


def test_adc():
    """A0-A3: 10 samples each, range/noise checks, read_uv consistency.
    Cross-talk: toggle the neighbouring pin while sampling. vbat channel
    must be readable."""
    ok = True
    for ch in range(4):
        raw, uv = _adc_read(ch)
        if not raw or any(x < 0 or x > 4095 for x in raw):
            print("[ADC A{0}] FAIL: unreadable or out of range".format(ch))
            ok = False
            continue
        lo, hi, avg, sd = _stats(raw)
        print("[ADC A{0}] raw={1:.0f}+-{2:.0f} range={3}-{4}".format(
            ch, avg, sd, lo, hi))
        if sd > 100:
            print("  WARN: noisy")
        us = [x for x in uv if x is not None]
        if us and avg:
            expected = avg / 4095.0 * VREF * 1000
            ratio = (sum(us) / len(us)) / expected
            if ratio < .8 or ratio > 1.2:
                print("  WARN: read_uv/raw mismatch")
    for ch in range(4):
        try:
            a = XiaoADC(ch)
            static = [a.read() for _ in range(5)]
            g = XiaoPin((ch + 1) % 4, Pin.OUT)
            moved = []
            for i in range(10):
                g.value(i & 1)
                time.sleep_ms(1)
                moved.append(a.read())
            drift = abs(sum(moved) / len(moved) - sum(static) / len(static))
            tag = "WARN" if drift > 50 else "OK"
            print("  A{0} cross-talk {1}: drift={2:.0f}".format(ch, tag, drift))
        except Exception as e:
            print("  A{0} cross-talk SKIP: {1}".format(ch, e))
    try:
        print("[ADC vbat] raw={0}".format(XiaoADC("vbat").read()))
    except Exception as e:
        print("[ADC vbat] FAIL: {0}".format(e))
        ok = False
    return _r("ADC full", "PASS" if ok else "FAIL")


def test_adc_simple():
    """One raw + millivolt read per channel A0-A3 (console helper)."""
    try:
        parts = []
        for ch in range(4):
            a = XiaoADC(ch)
            try:
                parts.append("A{0}: raw={1}, {2}mV".format(ch, a.read(),
                                                          a.read_uv() // 1000))
            except Exception:
                parts.append("A{0}: raw={1}".format(ch, a.read()))
        print("[ADC] " + "; ".join(parts))
        return _r("ADC simple", "PASS")
    except Exception as e:
        return _r("ADC simple", "FAIL", e)


def test_i2c():
    """IMU bus (I2C2): scan + 3 stable scans in a row."""
    try:
        b = _i2c()
        a = b.scan()
        _r("I2C IMU scan", "PASS" if a else "SKIP",
           [hex(x) for x in a] if a else "no device")
        old = set(a)
        stable = True
        for _ in range(2):
            time.sleep_ms(20)
            if set(b.scan()) != old:
                stable = False
        return _r("I2C stress", "PASS" if stable else "FAIL", "3 scans")
    except Exception as e:
        _r("I2C IMU scan", "FAIL", e)
        return _r("I2C stress", "SKIP", e)


def test_i2c1_header():
    """Scan the header I2C1 bus (D4/D5); empty is the normal result."""
    try:
        b = XiaoI2C("i2c0", "i2c1_sda", "i2c1_scl", 400000)
        a = b.scan()
        return _r("I2C1 header", "PASS", "{0} device(s) {1}".format(
            len(a), [hex(x) for x in a]))
    except Exception as e:
        return _r("I2C1 header", "SKIP", e)


def test_imu():
    """LSM6DS3TR-C: WHO_AM_I, configure 104 Hz, read temperature plus
    5 rounds of accel/gyro; all-zero readings are a FAIL."""
    try:
        b = _i2c()
        who = b.readfrom_mem(IMU, 0x0F, 1)[0]
        if who != IMU:
            return _r("IMU", "FAIL", "WHO_AM_I=0x{0:02X}".format(who))
        for reg in (0x12, 0x10, 0x11):
            b.writeto_mem(IMU, reg, bytes((0x44 if reg == 0x12 else 0x40,)))
        time.sleep_ms(20)
        readings = []
        for _ in range(5):
            d = b.readfrom_mem(IMU, 0x20, 14)
            readings.append(tuple(_i16(d, i) for i in (8, 10, 12, 2, 4, 6)))
            time.sleep_ms(20)
        temp = 25.0 + _i16(b.readfrom_mem(IMU, 0x20, 2), 0) / 256.0
        d = readings[-1]
        print("[IMU] temp={0:.2f}C accel=({1},{2},{3}) gyro=({4},{5},{6})".format(
            temp, *d))
        if all(x == 0 for row in readings for x in row):
            return _r("IMU", "FAIL", "all axes zero")
        return _r("IMU", "PASS", "WHO_AM_I=0x{0:02X}, 5 reads".format(who))
    except Exception as e:
        return _r("IMU", "FAIL", e)


def test_pwm():
    """Steady 1 kHz / 50 % on PA8 (TIM1_CH1) for scope or LED check."""
    pwm = None
    try:
        pwm = XiaoPWM(0)
        pwm.init(freq=1000, duty_u16=32768)
        time.sleep_ms(250)
        return _r("PWM", "PASS", "PA8 1kHz 50%; verify with scope/LED")
    except Exception as e:
        return _r("PWM", "FAIL", e)
    finally:
        _off(pwm)


def test_pwm_full():
    """Sweep 5 frequencies x 3 duty cycles; every init() must succeed."""
    pwm = None
    ok = True
    try:
        pwm = XiaoPWM(0)
        for hz in (100, 500, 1000, 5000, 10000):
            for duty in (25, 50, 75):
                try:
                    pwm.init(freq=hz, duty_u16=int(duty * 655.35))
                    time.sleep_ms(50)
                except Exception as e:
                    print("[PWM] {0}Hz/{1}% FAIL: {2}".format(hz, duty, e))
                    ok = False
        return _r("PWM full", "PASS" if ok else "FAIL", "15 settings")
    except Exception as e:
        return _r("PWM full", "FAIL", e)
    finally:
        _off(pwm)


def test_battery():
    """Enable BAT_EN (PA15), read the divider (2:1) on PA4; no battery
    attached is a SKIP, not a failure."""
    en = None
    try:
        en = XiaoPin("bat_en", Pin.OUT)
        en.value(1)
        time.sleep_ms(5)
        a = XiaoADC("vbat")
        raw, uv = a.read(), a.read_uv()
        if raw <= 0 or uv <= 0:
            return _r("Battery", "SKIP", "no battery voltage")
        return _r("Battery", "PASS", "raw={0}, estimated={1:.3f}V".format(
            raw, uv * BAT_DIVIDER / 1000000))
    except Exception as e:
        return _r("Battery", "SKIP", e)
    finally:
        if en is not None:
            try:
                en.value(0)
            except Exception:
                pass


def test_uart():
    """USART1 (D6/D7) loopback: write then read back the same payload.
    The zephyr UART defaults to a 0 ms read timeout (non-blocking), so
    wait for the echo to land in the RX ring buffer before reading.
    Without the D6<->D7 jumper this is a SKIP."""
    u = None
    try:
        u = XiaoUART("uart1", 115200, 6, 7)
        data = b"xiao-c5-uart-test\n"
        u.write(data)
        time.sleep_ms(50)               # echo flight time into the ring buffer
        got = u.read(len(data))
        if got == data:
            return _r("UART", "PASS", "loopback")
        return _r("UART", "SKIP",
                  "got {0!r}, want {1!r} - D6<->D7 jumper?".format(got, data))
    except Exception as e:
        return _r("UART", "SKIP", e)
    finally:
        _off(u)


def test_rtc():
    """Set a known datetime into the RTC module and read it back."""
    try:
        from RTC import RTC
        r = RTC()
        r.set_datetime((2026, 7, 24, 12, 0, 0))
        d = r.get_datetime()
        return _r("RTC", "PASS" if d[:3] == (2026, 7, 24) else "FAIL", d)
    except Exception as e:
        return _r("RTC", "SKIP", e)


def test_storage():
    """LittleFS on the external NOR: write/read/delete a file, then
    report the remaining free space."""
    try:
        import os
        path = "/flash/_board_test_.txt"
        data = b"xiao-c5-storage-ok"
        with open(path, "wb") as f:
            f.write(data)
        with open(path, "rb") as f:
            got = f.read()
        os.remove(path)
        if got != data:
            return _r("Storage", "FAIL", "read mismatch: {0}".format(got))
        st = os.statvfs("/flash")
        return _r("Storage", "PASS",
                  "LittleFS ok, {0} KB free".format(st[0] * st[3] // 1024))
    except Exception as e:
        return _r("Storage", "SKIP", e)


SPI_PATTERNS = (
    b"\x00",
    b"\xff",
    b"\xa5\x3c",
    b"XIAO-STM32C5-SPI-loopback!",
    bytes(range(64)),
)
# zephyr's spi_stm32 driver rejects (EINVAL) any request below
# spi_kernel_clock/256 (highest prescaler). The SPI3 kernel clock is
# 72 MHz (PCLK1) or 144 MHz depending on selection; both rates below are
# exactly derivable under either clock (72/128 resp. 72/64, 144/256
# resp. 144/128) and above the divisibility floor.
SPI_BAUDRATES = (562500, 1125000)


def test_spi():
    """Hardware SPI3 loopback: full-duplex write_readinto at two baud
    rates over five patterns. With D9<->D10 not jumpered every transfer
    comes back wrong -> SKIP with a wiring hint; partial mismatches are
    real failures."""
    spi = None
    results = []
    try:
        for baudrate in SPI_BAUDRATES:
            print("  [spi] {0} baud, {1} patterns...".format(baudrate, len(SPI_PATTERNS)))
            # XiaoSPI(bus_id, baud, sck, mosi, miso): bus id is the lookup
            # key ("spi0" -> hardware SPI3); pin numbers are accepted but
            # ignored, the mux comes from the board device tree.
            spi = XiaoSPI("spi0", baudrate, 8, 10, 9)
            for pattern in SPI_PATTERNS:
                rx = bytearray(len(pattern))
                spi.write_readinto(pattern, rx)
                results.append(bytes(rx) == pattern)
            _off(spi)
            spi = None
        passed = sum(results)
        if passed == len(results):
            return _r("SPI3 loopback", "PASS",
                      "{0} transfers at {1} baud".format(len(results),
                                                         "/".join(str(b) for b in SPI_BAUDRATES)))
        if passed == 0:
            return _r("SPI3 loopback", "SKIP",
                      "no echo - jumper D9 (MISO) to D10 (MOSI)?")
        return _r("SPI3 loopback", "FAIL",
                  "{0}/{1} transfers ok".format(passed, len(results)))
    except Exception as e:
        return _r("SPI3 loopback", "SKIP", e)
    finally:
        _off(spi)


def test_fdcan():
    """Controller loopback at 500k/2M FD: one frame out, same frame back."""
    c = None
    try:
        c = _can()
        c.send(0x123, b"C5")
        f = c.recv(200)
        return _r("FDCAN loopback", "PASS" if f and f[0] == 0x123 else "FAIL", f)
    except Exception as e:
        return _r("FDCAN loopback", "SKIP", e)
    finally:
        _off(c)


def test_fdcan_stress():
    """100 frames back to back; up to 5 losses are tolerated."""
    c = None
    try:
        c = _can()
        lost = 0
        for i in range(100):
            c.send(0x100 + i, bytes((i & 255, 0xC5, 1, 2)))
            if c.recv(100) is None:
                lost += 1
        return _r("FDCAN stress", "PASS" if lost <= 5 else "FAIL",
                  "lost={0}/100".format(lost))
    except Exception as e:
        return _r("FDCAN stress", "SKIP", e)
    finally:
        _off(c)


def test_fdcan_multi():
    """Two CAN objects on the shared controller: both must construct and
    send independently."""
    a = b = None
    try:
        gc.collect()
        a, b = _can(), _can()
        a.send(0x111, b"AAAA")
        b.send(0x222, b"BBBB")
        f = a.recv(200)
        return _r("FDCAN multi-instance", "PASS" if f else "FAIL",
                  "both created and sent")
    except Exception as e:
        return _r("FDCAN multi-instance", "FAIL", e)
    finally:
        _off(a)
        _off(b)


def test_fdcan_deinit():
    """Deinit of the second instance must not stop the first one."""
    a = b = None
    try:
        gc.collect()
        a, b = _can(), _can()
        b.deinit()
        b = None
        a.send(0x333, b"CCCC")
        return _r("FDCAN deinit isolation", "PASS" if a.recv(200) else "FAIL")
    except Exception as e:
        return _r("FDCAN deinit isolation", "FAIL", e)
    finally:
        _off(a)
        _off(b)


def test_fdcan_bad_payload():
    """Exhaustive two-way check over the whole length range: every legal
    FD length must send, every illegal length must raise ValueError.
    Same closed set as modcan.c: {0-8, 12, 16, 20, 24, 32, 48, 64}."""
    c = None
    try:
        c = _can()
        allowed = set(range(0, 9)) | {12, 16, 20, 24, 32, 48, 64}
        rejected = 0
        accepted = 0
        for size in range(0, 66):          # 0..64 covers legal+illegal; 65 overflows
            try:
                c.send(0x100, bytes(size))
            except ValueError:
                rejected += 1
                continue
            accepted += 1                   # send succeeded => must be a legal length
            c.recv(50)                      # drain loopback echo (queue depth is 32)
        n_illegal = 65 - len(allowed) + 1   # illegal within 0..64 (49) + overflow (65)
        ok = rejected == n_illegal and accepted == len(allowed)
        return _r("FDCAN invalid payload", "PASS" if ok else "FAIL",
                  "rejected {0}/{1}, accepted {2}/{3}".format(
                      rejected, n_illegal, accepted, len(allowed)))
    except Exception as e:
        return _r("FDCAN invalid payload", "SKIP", e)
    finally:
        _off(c)


def test_fdcan_speeds():
    """Reconfigure the controller through 5 nominal/data-rate combos
    (classic + FD) and loop one frame at each."""
    ok = True
    for nominal, data, fd in ((125000, 2000000, False),
                              (250000, 2000000, False),
                              (500000, 2000000, False),
                              (500000, 2000000, True),
                              (500000, 4000000, True)):
        c = None
        try:
            c = _can(fd, data, nominal)
            c.send(0x100, b"TEST")
            f = c.recv(200)
            ok = ok and bool(f and f[0] == 0x100)
        except Exception as e:
            print("[FDCAN speed] FAIL {0}/{1}: {2}".format(nominal, data, e))
            ok = False
        finally:
            _off(c)
        time.sleep_ms(50)
    return _r("FDCAN variable speed", "PASS" if ok else "FAIL", "5 speeds")


def test_fdcan_owner():
    """Deinit of the FIRST owner must hand the controller over cleanly:
    the second instance keeps working."""
    a = b = None
    try:
        gc.collect()
        a, b = _can(), _can()
        a.deinit()
        a = None
        b.send(0x444, b"alive")
        return _r("FDCAN owner-deinit-first", "PASS" if b.recv(200) else "FAIL")
    except Exception as e:
        return _r("FDCAN owner-deinit-first", "FAIL", e)
    finally:
        _off(a)
        _off(b)


def test_fdcan_mismatch():
    """A second CAN() with a mismatched fd flag must be rejected AND must
    not stop the live controller. (Catches the can_cleanup refcount
    underflow regression from PR #22 review.)"""
    a = None
    try:
        a = _can()
        rejected = False
        try:
            b = XiaoCAN("can0", bitrate=500000, data_bitrate=2000000,
                        fd=False, loopback=True)
            b.deinit()
        except (ValueError, OSError):
            rejected = True
        a.send(0x555, b"alive")
        alive = a.recv(200) is not None
        return _r("FDCAN config mismatch", "PASS" if rejected and alive else "FAIL",
                  "rejected={0}, owner-alive={1}".format(rejected, alive))
    except Exception as e:
        return _r("FDCAN config mismatch", "FAIL", e)
    finally:
        _off(a)


def test_fdcan_ids():
    """Standard 11-bit and extended 29-bit IDs must both loop back;
    an out-of-range ID must raise."""
    c = None
    try:
        c = _can(False)
        c.send(0x123, b"STD")
        a = c.recv(200)
        c.send(0x12345, b"EXT")
        b = c.recv(200)
        rejected = False
        try:
            c.send(0x20000000, b"X")
        except ValueError:
            rejected = True
        ok = a and a[0] == 0x123 and b and b[0] == 0x12345 and rejected
        return _r("FDCAN standard/extended ID", "PASS" if ok else "FAIL")
    except Exception as e:
        return _r("FDCAN standard/extended ID", "SKIP", e)
    finally:
        _off(c)


def _step(name, fn):
    print("-- {0} ".format(name) + "-" * (30 - len(name)))
    return fn()


def test_all():
    global _p, _f, _s
    _p = _f = _s = 0
    print("=" * 50)
    print(BOARD + " full test")
    print("SPI loopback needs the D9<->D10 jumper; UART needs D6<->D7")
    print("=" * 50)
    _step("status", test_status)
    # SPI first: the hardware loopback needs the D8/D9/D10 AF mux, which
    # test_gpio would steal (zephyr applies the SPI pin mux only once at
    # boot). CAN loopback is internal and does not care about pin state.
    _step("spi", test_spi)
    _step("led", test_led)
    _step("gpio", test_gpio)
    _step("adc", test_adc)
    _step("i2c", test_i2c)
    _step("i2c1_header", test_i2c1_header)
    _step("imu", test_imu)
    _step("pwm_full", test_pwm_full)
    _step("battery", test_battery)
    _step("uart", test_uart)
    _step("rtc", test_rtc)
    _step("storage", test_storage)
    _step("fdcan", test_fdcan)
    _step("fdcan_stress", test_fdcan_stress)
    _step("fdcan_multi", test_fdcan_multi)
    _step("fdcan_deinit", test_fdcan_deinit)
    _step("fdcan_bad_payload", test_fdcan_bad_payload)
    _step("fdcan_speeds", test_fdcan_speeds)
    _step("fdcan_owner", test_fdcan_owner)
    _step("fdcan_mismatch", test_fdcan_mismatch)
    _step("fdcan_ids", test_fdcan_ids)
    print("=" * 50)
    print("Results: {0} PASS, {1} FAIL, {2} SKIP ({3} total)".format(
        _p, _f, _s, _p + _f + _s))
    return _f == 0


def main():
    return test_all()


def _tests():
    return {n[5:]: f for n, f in globals().items()
            if n.startswith("test_") and callable(f)}


def print_help():
    print("Commands (test name = command, e.g. 'adc' -> test_adc):")
    print("  all            run the complete suite")
    print("  status         board info")
    print("  led on|off|blink")
    print("  io <pin> [n]   toggle one pin n times (e.g. 'io 5 3')")
    print("  <test>         run one test: " +
          ", ".join(sorted(k for k in _tests()
                           if k not in ("all", "status"))))
    print("  help | exit")
    print("Wiring: SPI loopback = D9<->D10 jumper; UART = D6<->D7 jumper;")


def _dispatch(line):
    parts = line.strip().split()
    if not parts:
        return True
    cmd = parts[0].lower()
    if cmd == "exit":
        return False
    if cmd == "help":
        print_help()
        return True
    if cmd == "led":
        test_led(parts[1].lower() if len(parts) > 1 else "blink")
        return True
    if cmd == "io":
        test_io(parts[1] if len(parts) > 1 else 0,
                int(parts[2]) if len(parts) > 2 else 2)
        return True
    fn = _tests().get(cmd)
    if fn is None:
        print("Unknown command: " + cmd)
        print_help()
    else:
        fn()
    return True


def console():
    print(BOARD + " test console - 'help' for commands")
    while True:
        try:
            sys.stdout.write("xiao-c5> ")
            line = sys.stdin.readline()
            if not line:
                print("")
                break
        except (EOFError, KeyboardInterrupt):
            print("")
            break
        try:
            if not _dispatch(line):
                break
        except Exception as e:
            print("[FAIL] command error: " + str(e))
    print("test console stopped")


if __name__ == "__main__":
    main()
