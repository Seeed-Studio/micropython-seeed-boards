# XIAO nRF54L15 MicroPython v1.27.0 smoke test.
#
# Hardware-validated 2026-09-29 against the master CI build (6/6 PASS).
# Run from the REPL exposed by the board's onboard debug bridge
# (CMSIS-DAP + CDC UART):
#
#     mpremote connect COM<x> run example\xiao_nrf54l15_smoke_test.py
#
# Notes:
# - The nRF54L15's own USB peripheral is not wired to the USB-C connector
#   on this board; the bridge's CDC port IS the console. Absence of any
#   other USB serial device is expected, not a firmware bug.
# - Use mpremote specifically: its raw-paste flow control is needed to
#   push this ~5 KB script through the bridge (a naive raw-REPL dump
#   overflows the CDC buffer and silently loses the script).
# - The final LED check (gpio2.0) is visual -- watch the board.

import sys
import gc
import time
import os

NAME = "xiao_nrf54l15"

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
    assert "nrf54l15" in m, "board string %r lacks 'nrf54l15'" % m
    return sys.implementation._machine


def t_gc():
    free = gc.mem_free()
    # Default CONFIG_MICROPY_HEAP_SIZE is 49152 -> 48000 bytes usable after GC
    # bookkeeping (hardware-measured 2026-09-29: free+alloc == 48000 exactly),
    # so anything above ~46K can never pass. 32K leaves headroom for a
    # deliberately enlarged heap while still catching a broken one.
    assert free > 32 * 1024, "only %d bytes free" % free
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


def t_ble():
    import bluetooth

    b = bluetooth.BLE()
    return "bluetooth.BLE() ok, active=%s" % b.active()


def t_time():
    a = time.ticks_ms()
    time.sleep_ms(200)
    d = time.ticks_diff(time.ticks_ms(), a)
    assert 100 <= d <= 2000, "sleep drifted %d ms" % d
    return "ticks + sleep ok (%d ms)" % d


check("version>=1.27.0", t_version)
check("board=nrf54l15", t_machine)
check("gc heap", t_gc)
check("filesystem r/w", t_fs)
check("bluetooth (BLE)", t_ble, hard=False)  # NCS BT config varies; report only
check("time/ticks", t_time)

# --- LED: gpio2.0 per repo examples/boards/xiao_nrf54l15.py ---------------
try:
    from machine import Pin

    led = Pin(("gpio2", 0), Pin.OUT)
    print("bound gpio2.0 -- watch the board: 3 blinks")
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
