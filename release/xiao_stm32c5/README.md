# XIAO STM32C5 MicroPython

## Flash

1. Connect the board over USB and double-click Reset.
2. Wait for the `XIAOC5BOOT` drive to appear.
3. Copy `firmware/micropython-xiao-stm32c5.uf2` to that drive. TinyUF2
   processes the file and reboots automatically.

On Linux/macOS, `flash_xiao_stm32c5.sh` can copy the file after the board has
entered bootloader mode. Manual drag-and-drop is always supported. Flashing
does not require Python, PlatformIO, ST-Link, or J-Link.

If the drive is not visible, disconnect/reconnect USB and double-click Reset
again. A wrong UF2 must not overwrite TinyUF2; use the same double-reset flow
to recover and copy a known-good image.

## REPL and test

The v1 REPL is USART1 at 115200 8-N-1: PA9 is TX, PA10 is RX, and GND is
common. USB CDC REPL and 1200-bps automatic bootloader entry are optional
enhancements, not v1 requirements.

Copy `tests/xiao_stm32c5_full_test.py` to the board filesystem, then run the
single full test entry point:

```python
import xiao_stm32c5_full_test as test
test.main()
```

The script runs LED, GPIO, ADC, PWM, I2C, IMU, battery, UART, RTC, LittleFS, and
all 9 FDCAN regression tests. Every item reports `PASS`, `FAIL`, or `SKIP`;
missing external hardware uses bounded waits and must not hang.

## Wiring

- I2C1 header: D4/PB7 SDA, D5/PB6 SCL.
- Onboard LSM6DS3TR-C: I2C2 PB3/PB4, address `0x6A`.
- UART loopback: PA9 to PA10. Do not run it while using that UART as REPL.
- PWM: internal PA8/TIM1_CH1; verify with a scope, LED, or test point.
- FDCAN2: PB5 RX, PB13 TX, PB14 transceiver standby. External testing needs
  a CAN transceiver and a 120-ohm terminated bus.
- Battery: BAT_EN PE2 and sense PA4/ADC1_IN4; a missing battery is `SKIP`.

The package is not a formal release until real XIAO STM32C5 hardware has
passed TinyUF2 upgrade/rollback, wrong-UF2 recovery, ten update/boot cycles,
and the complete function test.
