"""XIAO STM32C5 SPI loopback test (bit-banged SoftSPI).

The XIAO header carries no hardware SPI on this board: D8 (PA15) has no
SPI-SCK alternate function (STM32C5A3 datasheet DS15137 Table 14), so the
D8/D9/D10 header pins are driven by machine.SoftSPI instead of a hardware
SPI peripheral.

Wiring: short D10 (MOSI, PB15) to D9 (MISO, PB0) with a jumper wire.
D8 (SCK, PA15) is controller-driven and needs no connection.

Run from the REPL with:
    import xiao_stm32c5_spi_test as t; t.main()
"""
from machine import Pin, SoftSPI

BOARD_HEADER = "XIAO STM32C5 SoftSPI loopback test"

# Header pin -> GPIO: D8 = SCK = PA15, D9 = MISO = PB0, D10 = MOSI = PB15.
SCK = ("gpioa", 15)
MISO = ("gpiob", 0)
MOSI = ("gpiob", 15)

# Two rates: a conservative one and a faster one to shake out timing.
BAUDRATES = (250000, 1000000)

PATTERNS = (
    b"\x00",
    b"\xff",
    b"\xa5\x3c",
    b"XIAO-STM32C5-SPI-loopback!",
    bytes(range(64)),
)

_p = _f = 0


def _r(name, state, msg=""):
    global _p, _f
    print("[{0}] {1}{2}".format(state, name, " - " + str(msg) if msg else ""))
    if state == "PASS":
        _p += 1
    elif state == "FAIL":
        _f += 1
    return state == "PASS"


def _run(spi, baudrate):
    for pattern in PATTERNS:
        rx = bytearray(len(pattern))
        spi.write_readinto(pattern, rx)
        got = bytes(rx)
        ok = got == pattern
        _r(
            "loopback @{0} baud, {1} B {2}..".format(
                baudrate, len(pattern), pattern[:4].hex()
            ),
            "PASS" if ok else "FAIL",
            "" if ok else "received {0}..".format(got[:4].hex()),
        )


def main():
    print(BOARD_HEADER)
    print("Wiring: jumper D10 (MOSI) <-> D9 (MISO); D8 = SCK (unconnected)")
    print("")
    for baudrate in BAUDRATES:
        spi = SoftSPI(
            baudrate=baudrate,
            polarity=0,
            phase=0,
            bits=8,
            firstbit=SoftSPI.MSB,
            sck=Pin(SCK, Pin.OUT),
            mosi=Pin(MOSI, Pin.OUT),
            miso=Pin(MISO, Pin.IN),
        )
        try:
            _run(spi, baudrate)
        finally:
            spi.deinit()
    print("")
    print("summary: {0} passed, {1} failed".format(_p, _f))
    if _f:
        print("If every case failed: check the D10<->D9 jumper wire.")
    return _f == 0


if __name__ == "__main__":
    main()
