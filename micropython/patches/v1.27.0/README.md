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
