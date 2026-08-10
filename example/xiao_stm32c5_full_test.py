"""XIAO STM32C5 complete hardware test.

Run from the REPL with:
    import xiao_stm32c5_full_test as t; t.main()
"""
import time
import gc
from machine import Pin
from boards.xiao import XiaoADC, XiaoCAN, XiaoI2C, XiaoPin, XiaoPWM, XiaoUART

BOARD = "XIAO STM32C5"
VREF = 3300
IMU = 0x6A
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


def test_led():
    try:
        led = XiaoPin("led", Pin.OUT)
        for _ in range(3):
            led.value(0)
            time.sleep_ms(100)
            led.value(1)
            time.sleep_ms(100)
        led.value(1)
        return _r("LED", "PASS", "active-low blink")
    except Exception as e:
        return _r("LED", "FAIL", e)


def test_gpio():
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
    ok = True
    base = []
    for ch in range(4):
        raw, uv = _adc_read(ch)
        if not raw or any(x < 0 or x > 4095 for x in raw):
            print("[ADC A{0}] FAIL: unreadable or out of range".format(ch))
            ok = False
            base.append(None)
            continue
        lo, hi, avg, sd = _stats(raw)
        base.append(avg)
        print("[ADC A{0}] raw={1:.0f}+-{2:.0f} range={3}-{4}".format(
            ch, avg, sd, lo, hi))
        us = [x for x in uv if x is not None]
        if us and avg:
            expected = avg / 4095.0 * VREF * 1000
            ratio = (sum(us) / len(us)) / expected
            if ratio < .8 or ratio > 1.2:
                print("  WARN: read_uv/raw mismatch")
    for ch in range(4):
        if base[ch] is None:
            continue
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
            print("  A{0} cross-talk drift={1:.0f}".format(ch, drift))
        except Exception as e:
            print("  A{0} cross-talk SKIP: {1}".format(ch, e))
    try:
        v = XiaoADC("vbat").read()
        print("[ADC vbat] raw={0}".format(v))
    except Exception as e:
        print("[ADC vbat] FAIL: {0}".format(e))
        ok = False
    return _r("ADC full", "PASS" if ok else "FAIL")


def test_pwm():
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
        return _r("PWM full", "PASS" if ok else "FAIL",
                  "15 settings; verify output with scope/LED")
    except Exception as e:
        return _r("PWM full", "FAIL", e)
    finally:
        _off(pwm)


def test_i2c():
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
        _r("I2C stress", "PASS" if stable else "FAIL", "3 scans")
    except Exception as e:
        _r("I2C IMU scan", "FAIL", e)
        _r("I2C stress", "SKIP", e)
    try:
        b = XiaoI2C("i2c0", "i2c1_sda", "i2c1_scl", 400000)
        a = b.scan()
        return _r("I2C1 header", "PASS", "{0} device(s) {1}".format(
            len(a), [hex(x) for x in a]))
    except Exception as e:
        return _r("I2C1 header", "SKIP", e)


def test_imu():
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
        d = readings[-1]
        print("[IMU] accel=({0},{1},{2}) gyro=({3},{4},{5})".format(*d))
        if all(x == 0 for row in readings for x in row):
            return _r("IMU", "FAIL", "all axes zero")
        return _r("IMU", "PASS", "WHO_AM_I=0x{0:02X}, 5 reads".format(who))
    except Exception as e:
        return _r("IMU", "FAIL", e)


def test_battery():
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
            raw, uv * 2 / 1000000))
    except Exception as e:
        return _r("Battery", "SKIP", e)
    finally:
        if en is not None:
            try:
                en.value(0)
            except Exception:
                pass


def test_uart():
    u = None
    try:
        u = XiaoUART("uart1", 115200, 6, 7)
        data = b"xiao-c5-uart-test\n"
        u.write(data)
        got = u.read(len(data))
        return _r("UART", "PASS" if got == data else "SKIP",
                  "loopback" if got == data else "PA9-PA10 jumper required")
    except Exception as e:
        return _r("UART", "SKIP", e)
    finally:
        _off(u)


def test_rtc():
    try:
        from RTC import RTC
        r = RTC()
        r.set_datetime((2026, 7, 24, 12, 0, 0))
        d = r.get_datetime()
        return _r("RTC", "PASS" if d[:3] == (2026, 7, 24) else "FAIL", d)
    except Exception as e:
        return _r("RTC", "SKIP", e)


def test_storage():
    try:
        import os
        path = "/flash/_board_test_.txt"
        data = b"xiao-c5-storage-ok"
        with open(path, "wb") as f:
            f.write(data)
        with open(path, "rb") as f:
            got = f.read()
        os.remove(path)
        return _r("Storage", "PASS" if got == data else "FAIL", "LittleFS")
    except Exception as e:
        return _r("Storage", "SKIP", e)


def test_fdcan():
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
    c = None
    try:
        c = _can()
        # Exhaustive two-way check over the whole length range: every legal
        # FD length must send, every illegal length must raise ValueError.
        # Same closed set as modcan.c: {0-8, 12, 16, 20, 24, 32, 48, 64}.
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
    a = None
    try:
        a = _can()
        rejected = False
        try:
            # Mismatched fd vs the running fd=True controller.
            b = XiaoCAN("can0", bitrate=500000, data_bitrate=2000000,
                        fd=False, loopback=True)
            b.deinit()
        except (ValueError, OSError):
            rejected = True
        # The mismatched construction must NOT have stopped the live
        # controller: the first owner must still be able to send/recv.
        # (Catches the can_cleanup-refcount-underflow regression, where a
        # failed second CAN() decremented a refcount it never incremented
        # and stopped the shared controller.)
        a.send(0x555, b"alive")
        alive = a.recv(200) is not None
        return _r("FDCAN config mismatch", "PASS" if rejected and alive else "FAIL",
                  "rejected={0}, owner-alive={1}".format(rejected, alive))
    except Exception as e:
        return _r("FDCAN config mismatch", "FAIL", e)
    finally:
        _off(a)


def test_fdcan_ids():
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


def test_all():
    global _p, _f, _s
    _p = _f = _s = 0
    print("=" * 50)
    print(BOARD + " full test")
    print("=" * 50)
    test_led()
    test_gpio()
    test_adc()
    test_i2c()
    test_imu()
    test_pwm()
    test_battery()
    test_uart()
    test_rtc()
    test_storage()
    test_fdcan()
    test_fdcan_stress()
    test_fdcan_multi()
    test_fdcan_deinit()
    test_fdcan_bad_payload()
    test_fdcan_speeds()
    test_fdcan_owner()
    test_fdcan_mismatch()
    test_fdcan_ids()
    print("=" * 50)
    print("Results: {0} PASS, {1} FAIL, {2} SKIP ({3} total)".format(
        _p, _f, _s, _p + _f + _s))
    return _f == 0


def main():
    return test_all()


if __name__ == "__main__":
    main()
