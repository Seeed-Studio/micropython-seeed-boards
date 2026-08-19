# XIAO STM32C5 MicroPython — user guide

## What's in the package

| Path | What |
|---|---|
| `firmware/micropython-xiao-stm32c5.uf2` | Firmware image — flash this. |
| `firmware/SHA256SUMS.txt` | Integrity hashes for firmware and tests. |
| `tests/*.py` | On-device test scripts — copy to the board, import, run. |
| `flash_xiao_stm32c5.sh` | Linux/macOS one-click flash helper. |

## Flash the firmware

1. Connect the board over USB (data-capable cable).
2. Double-click the Reset button — a `XIAOC5BOOT` drive appears.
3. Copy `firmware/micropython-xiao-stm32c5.uf2` onto that drive
   (drag-and-drop, or run `flash_xiao_stm32c5.sh`).

TinyUF2 processes the file and reboots into MicroPython automatically.
Flashing needs no toolchain, ST-Link, or J-Link. The bootloader itself is
never overwritten; if a bad image ever breaks the application, re-enter
bootloader mode (double-click Reset) and copy a known-good UF2.

## Connect the REPL (USB CDC)

The REPL runs on the on-board USB port as a CDC-ACM virtual serial port —
the same cable used for flashing:

- Thonny: *Run → Select interpreter → MicroPython (generic)*, port = the
  serial device that appears after flashing (Windows `COMx`,
  Linux `/dev/ttyACM0`, macOS `/dev/tty.usbmodem*`). Any baud rate works.
- Or `mpremote`, `rshell`, `screen /dev/ttyACM0`, PuTTY, ...

Clock sync: the firmware exposes `time.localtime()` and `machine.RTC()`,
so Thonny (and other host tools) sync the clock without the two warnings
older builds logged. `machine.RTC().datetime((y, m, d, wd, hh, mm, ss, 0))`
sets the LSE-backed hardware RTC; `time.time()` / `time.localtime()` count
from boot.

## Run the tests

Copy the wanted scripts to the board filesystem (Thonny: right-click the
file → *Upload to /*), then from the REPL:

```python
import xiao_stm32c5_full_test as t; t.main()   # everything, incl. CAN
import xiao_stm32c5_base_test  as t; t.main()  # peripherals, no CAN
import xiao_stm32c5_can_test   as t; t.main()  # 9 FDCAN loopback tests
import xiao_stm32c5_spi_test   as t; t.main()  # SPI loopback (see wiring)
```

`can_interconnect.py` needs a second board or a CAN analyser. The board
helper API (`from boards.xiao import XiaoPin, XiaoADC, XiaoPWM, XiaoI2C,
XiaoSPI, XiaoUART, XiaoCAN`) is frozen into the firmware.

## SPI — bit-banged, not hardware

The XIAO header SPI pins cannot reach a hardware SPI peripheral: **D8
(PA15) has no SPI-SCK alternate function** (STM32C5A3 datasheet DS15137,
Table 14). D9 (PB0) and D10 (PB15) carry MISO/MOSI functions but a bus
without SCK is unusable, so the board provides SPI through
`machine.SoftSPI` (bit-banged) on the same pins:

```python
from boards.xiao import XiaoSPI
spi = XiaoSPI(0, 500000)   # sck=D8, mosi=D10, miso=D9, SPI mode 0
rx = bytearray(4)
spi.write_readinto(b"\x9f\x00\x00\x00", rx)   # e.g. flash JEDEC-ID
```

`xiao_stm32c5_spi_test.py` expects a jumper wire between D10 (MOSI) and
D9 (MISO) and verifies every pattern at two baud rates. Keep wire runs
short; SoftSPI over jumper wires is reliable up to a few hundred kHz.

## Pin table

| Header | GPIO | Functions |
|---|---|---|
| D0–D3 | PA0–PA3 | ADC1_IN0–IN3, GPIO |
| D4 / D5 | PB7 / PB6 | I2C1 SDA / SCL |
| D6 / D7 | PA9 / PA10 | USART1 TX / RX (spare UART — the REPL is USB CDC) |
| D8 | PA15 | SoftSPI SCK (no hardware SCK AF — see erratum above) |
| D9 | PB0 | SoftSPI MISO |
| D10 | PB15 | SoftSPI MOSI |
| D11 / D12 | PB8 / PB9 | FDCAN1 RX / TX |
| D13 / D14 | PB5 / PB13 | FDCAN2 RX / TX |
| D15 | PB14 | CAN transceiver standby (active-high) |

On-board devices: user LED PB12 (active-low), LSM6DS3TR-C IMU on I2C2 at
`0x6A`, 16 MB external NOR flash hosting the MicroPython `/flash`
filesystem, battery sense on PA4/ADC1_IN4 with enable pin PE2.

## Known limitations

- No hardware SPI on the header (D8/PA15 erratum) — use `machine.SoftSPI`.
- `time.time()` is boot-relative; wall-clock time lives in
  `machine.RTC().datetime()`.
- The package is not a formal release until real hardware passes the
  qualification list in `RELEASE_NOTES.md`.
