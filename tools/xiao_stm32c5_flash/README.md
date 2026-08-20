# XIAO STM32C5 — flash package

One-click flash of the prebuilt MicroPython **UF2** via the board's on-board
**TinyUF2** bootloader. No toolchain, pyocd, openocd, ST-Link, or J-Link needed.

## Contents

| File | What |
|---|---|
| `micropython-xiao-stm32c5.uf2` | Firmware image — copied to the board. |
| `xiao_stm32c5_flash.py` | Cross-platform flash helper (finds `XIAOC5BOOT`, copies the UF2). |
| `xiao_stm32c5_flash.sh` | Linux/macOS wrapper. |
| `xiao_stm32c5_flash.bat` | Windows wrapper. |

## Flash

1. Connect the board over USB.
2. **Double-click Reset** — a `XIAOC5BOOT` mass-storage drive appears.
3. Run the helper for your OS:

   ```bash
   ./xiao_stm32c5_flash.sh          # Linux / macOS
   # xiao_stm32c5_flash.bat         # Windows
   # python xiao_stm32c5_flash.py    # any OS with Python 3
   ```

4. The board reboots automatically and MicroPython starts.

If `XIAOC5BOOT` is not found: use a data-capable USB cable, unplug/replug, and
double-click Reset again. A wrong/broken UF2 never overwrites the TinyUF2
bootloader — re-enter bootloader mode and re-flash a known-good image.

## After flashing

- **REPL**: USB CDC-ACM on the same USB cable — pick the serial device
  that appears after the reboot (Windows `COMx`, Linux `/dev/ttyACM0`,
  macOS `/dev/tty.usbmodem*`); any baud rate works. USART1 (PA9/PA10) is
  free as a spare UART.
- **Hardware test**: see the top-level delivery package
  (`release/xiao_stm32c5/README.md`) for the full test scripts, wiring,
  and the pin table.
