# XIAO MG24 MicroPython v1.27.0 smoke test.
#
# Hardware-validated 2026-09-29 against the master CI build (7/7 PASS).
# Core validation: the custom C modules linked in via USER_C_MODULES (the
# PR #38 fix) must import and be usable. They register with UPPERCASE names
# (ADC / RTC / CAN / PDM / LowPWR -- see MP_REGISTER_MODULE in
# src/cmodules/*) and the callable classes live inside the module
# (ADC.ADC, RTC.RTC); `import adc` fails, `import ADC` is correct.
#
# Run from the REPL exposed by the board's onboard debug bridge
# (CMSIS-DAP + CDC UART):
#
#     mpremote connect COM<x> run example\xiao_mg24_smoke_test.py
#
# Use mpremote specifically (raw-paste flow control; a naive raw-REPL dump
# overflows the bridge's CDC buffer). The MG24's own USB peripheral is not
# wired to the USB-C connector, so no other USB serial device is expected.
# The final LED check (gpioa.7) is visual.

import sys
import gc
import time
import os

NAME = "xiao_mg24"

results = []


def check(name, fn, hard=True):
    try:
        detail = fn()
        results.append((name, True, "", hard))
        print("PASS  %-24s %s" % (name, detail))
    except Exception as e:
        results.append((name, False, repr(e), hard))
        print("%s  %-24s %s" % ("FAIL" if hard else "WARN", name, repr(e)))


print("=== %s smoke ===" % NAME)
print("platform      :", sys.platform)
try:
    print("_machine      :", sys.implementation._machine)
except AttributeError:
    pass
print("implementation:", sys.implementation.name, sys.implementation.version)


def t_version():
    assert sys.implementation.name == "micropython", "not micropython"
    v = sys.implementation.version
    assert tuple(v)[:2] >= (1, 27), "version %r < 1.27.0" % (v,)
    return "v%s" % ".".join(map(str, v))


def t_machine():
    m = getattr(sys.implementation, "_machine", "").lower()
    assert "mg24" in m, "board string %r lacks 'mg24'" % m
    return sys.implementation._machine


def t_cmodule_adc():
    # Module registers as uppercase "ADC" (MP_QSTR_ADC in modadc.c); the
    # callable class is ADC.ADC. Verified on hardware 2026-09-29.
    import ADC

    names = ", ".join(n for n in dir(ADC) if not n.startswith("_"))
    assert "ADC" in names, "ADC module exposes %r, no ADC class" % names
    return "import ADC ok: %s" % names


def t_cmodule_rtc():
    # Module registers as uppercase "RTC" (MP_QSTR_RTC in modrtc.c); the
    # class is RTC.RTC. Verified on hardware 2026-09-29 (software fallback
    # datetime round-trip: MG24 board has no PCF8563).
    import RTC

    names = ", ".join(n for n in dir(RTC) if not n.startswith("_"))
    assert "RTC" in names, "RTC module exposes %r, no RTC class" % names
    r = RTC.RTC()
    r.datetime((2026, 9, 29, 12, 0, 0))
    got = r.datetime()
    assert got[:3] == (2026, 9, 29), "RTC round-trip got %r" % (got,)
    return "import RTC ok + datetime round-trip: %s" % names


def t_gc():
    free = gc.mem_free()
    assert free > 30 * 1024, "only %d bytes free" % free
    return "%d KB free heap" % (free // 1024)


def t_fs():
    root = os.listdir("/")
    wrote = None
    for base in ("/flash", "/"):
        p = base.rstrip("/") + "/__smoke__.txt"
        try:
            with open(p, "w") as f:
                f.write("hello v1.27\n")
            with open(p) as f:
                s = f.read()
            os.remove(p)
            assert s == "hello v1.27\n"
            wrote = base
            break
        except Exception:
            continue
    assert wrote, "no writable filesystem (root=%r)" % (root,)
    return "r/w ok on %s, root=%r" % (wrote, root)


def t_time():
    a = time.ticks_ms()
    time.sleep_ms(200)
    d = time.ticks_diff(time.ticks_ms(), a)
    assert 100 <= d <= 2000, "sleep drifted %d ms" % d
    return "ticks + sleep ok (%d ms)" % d


check("version>=1.27.0", t_version)
check("board=mg24", t_machine)
check("cmodule: import adc", t_cmodule_adc)
check("cmodule: import rtc", t_cmodule_rtc)
check("gc heap", t_gc)
check("filesystem r/w", t_fs)
check("time/ticks", t_time)

# --- LED: gpioa.7 per repo examples/boards/xiao_mg24.py --------------------
try:
    from machine import Pin

    led = Pin(("gpioa", 7), Pin.OUT)
    print("bound gpioa.7 -- watch the board: 3 blinks")
    for _ in range(3):
        led.value(1)
        time.sleep_ms(250)
        led.value(0)
        time.sleep_ms(250)
    led.value(0)
    print("DONE  did an LED blink? (confirm by eye)")
except Exception as e:
    print("SKIP  LED test error:", repr(e))

npass = sum(1 for _, ok, _, _ in results if ok)
for name, ok, err, _ in results:
    if not ok:
        print("  FAILED:", name, err)
print("%s: %d/%d automated checks passed" % (NAME, npass, len(results)))
print("SMOKE %s: %s" % (NAME, "ALL PASS" if npass == len(results) else "HAS FAILURES"))
