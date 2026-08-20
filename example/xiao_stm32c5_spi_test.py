"""XIAO STM32C5 SPI loopback test (hardware SPI3).

The header SPI is hardware SPI3 on the current board revision:
D8 (PE2) = SCK, D9 (PB0) = MISO, D10 (PB15) = MOSI. The pin mux is fixed
by the board device tree, so XiaoSPI only takes the bus id and baud rate.

Wiring: short D10 (MOSI) to D9 (MISO) with a jumper wire. D8 (SCK) is
controller-driven and needs no connection.

Run from the REPL with:
    import xiao_stm32c5_spi_test as t; t.main()
"""
from boards.xiao import XiaoSPI

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
    print("XIAO STM32C5 SPI3 loopback test")
    print("Wiring: jumper D10 (MOSI) <-> D9 (MISO); D8 = SCK (unconnected)")
    print("")
    # XiaoSPI(spi_id, baudrate, sck, mosi, miso) -- the pin numbers are
    # accepted for API parity but ignored: SPI3 pins come from the DTS.
    for baudrate in BAUDRATES:
        spi = XiaoSPI(0, baudrate, 8, 10, 9)
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
