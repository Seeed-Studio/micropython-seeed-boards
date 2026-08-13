# XIAO STM32C5 MicroPython {{VERSION}}

## Build evidence

- MicroPython port: Zephyr
- Zephyr framework: 4.4.0
- UF2 application address: `0x08008000`
- UF2 family ID: `0x00C5C5C5`
- UF2 volume label: `XIAOC5BOOT`
- REPL: USART1, 115200 8-N-1

## Included capabilities

The image includes MicroPython GPIO, UART, I2C, ADC, PWM, LittleFS, RTC,
board helpers, and a Zephyr CAN/FDCAN wrapper with bounded receive timeout.
The interactive board test script is included separately under `tests/` in the
package and is copied to the device filesystem by the user.

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
- UART / ADC / PWM / FDCAN / I2C / LED / GPIO / IMU / battery results:

Known limitations: USB CDC REPL and 1200-bps automatic bootloader entry are
not part of v1; D8-D10 are not advertised as hardware SPI pins.
