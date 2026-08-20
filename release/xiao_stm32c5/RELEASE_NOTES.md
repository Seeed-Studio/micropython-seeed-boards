# XIAO STM32C5 MicroPython {{VERSION}}

## Build evidence

- MicroPython port: Zephyr (pinned upstream base + storage/time-RTC patches)
- Zephyr framework: 4.4.0
- UF2 application address: `0x08008000`
- UF2 family ID: `0x00C5C5C5`
- UF2 volume label: `XIAOC5BOOT`
- REPL: USB CDC-ACM on the on-board USB port (any baud rate)

## Included capabilities

MicroPython GPIO, UART, I2C, ADC, PWM, LittleFS, and CAN/FDCAN with
bounded receive timeout; `time.localtime` / `time.gmtime` / `time.mktime`
and `machine.RTC` (LSE-backed hardware RTC, with software fallback);
hardware SPI3 on the header (D8/PE2 SCK, D9/PB0 MISO, D10/PB15 MOSI);
frozen XIAO board helpers (`boards.xiao`); test scripts for peripherals,
CAN, and SPI loopback under `tests/`.

## Hardware qualification

Compilation and UF2 structural checks are complete for this package. The
following must be filled from a real-board test record before publishing a
formal release:

- TinyUF2 bootloader version:
- Hardware revision:
- Host OS:
- Ten update/boot cycles:
- Upgrade and rollback:
- Wrong/incompatible UF2 recovery:
- UART / ADC / PWM / FDCAN / I2C / LED / GPIO / IMU / battery / SPI results:

Known limitations: `time.time()` counts from boot, wall-clock time is kept
by `machine.RTC()`; the header SPI pins are fixed by the device tree
(no runtime pin remapping for SPI).
