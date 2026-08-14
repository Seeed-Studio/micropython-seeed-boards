# XIAO nRF54LM20B MicroPython delivery package

This package contains the application image signed for the factory MCUboot
key, the USB DFU flasher, the board test console, and a portable Windows
`nrfutil`/`mcu-manager` runtime.

The bootloader and KMU provisioning are not included. Production devices must
already contain the matching factory verification material in KMU. The CI
signing key is used only during the trusted release job and is never placed in
this package.

## Flash the application

Enter MCUboot USB DFU mode by holding USER, pressing RESET, and releasing USER.
Then, from this package directory on Windows, run:

```powershell
.\flash\xiao_nrf54lm20b_flash.ps1
```

The script uploads `firmware/zephyr.signed.bin` and resets the board. The
application CDC port uses VID:PID `2886:8013`; the MCUboot loader uses
`2886:0013`.

## Run the board test console

See `test/README.md`. The test console is started from the MicroPython REPL:

```python
import xiao_nrf54lm20b_full_test as test
test.main()
```

## Integrity

`SHA256SUMS` contains hashes for all release files. Do not replace the signed
application image with an unsigned or differently signed build.
