# MicroPython v1.27.0 compatibility patch

`0001-zephyr-xiao-nrf54lm20b-runtime.patch` is applied only to the official
MicroPython `v1.27.0` submodule revision (`78ff170de9e32c79db6e64d3e33d2bd60002bdcd`).

It adds the Zephyr-port integration required by the XIAO nRF54LM20B board:

- discovery and compilation of the board's external C modules;
- the software RTC exposed as `machine.RTC()`;
- `time.localtime()` for host clock synchronisation; and
- `zsensor.GAUGE_VOLTAGE` for nPM1300 battery readings; and
- the Zephyr 4.x Bluetooth advertiser option rename used by NCS 3.3.0.

The external-flash LittleFS mount/format path is supplied by the upstream
v1.27 `_boot.py` frozen module, so no forked MicroPython source is required.

## USB LDO VDCEN patch

`0002-renesas-ra-usb-ldo-vdcen.patch` is the only part of upstream PR
micropython/micropython#16409 (WEACT_RA4M1_CORE board profile, open since
2024-12) that the XIAO RA4M1 build actually depends on: when the board's FSP
config enables the internal USB LDO regulator (`USB_CFG_LDO_REGULATOR`), the
VDCEN bit in `USBMC` must be set before USB enumerates.  The WEACT board
profile itself is not carried — this repo supplies the XIAO board definition
via `boards/seeed/xiao_ra4m1` and the port's native `BOARD_DIR` support, and
v1.27.0 already ships the RA4M1 family (`EK_RA4M1`, `RA4M1_CLICKER`).

Both patches are applied to every job that runs
`tools/apply_micropython_patches.sh`.  They touch disjoint file sets (0001:
`ports/zephyr/*`, 0002: `ports/renesas-ra/*`), so a patch is inert for boards
whose port does not compile those files, and the `VDCEN` code is additionally
guarded by `#if USB_CFG_LDO_REGULATOR == USB_CFG_ENABLE` so it compiles to
nothing on boards that do not use the internal LDO.
