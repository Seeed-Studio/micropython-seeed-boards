# XIAO nRF54LM20B MicroPython delivery package

This package contains a MicroPython application image signed for the factory
MCUboot key, USB DFU flashing tools, and the board test console.

The bootloader and KMU provisioning are deliberately not included. The target
device must already contain the factory MCUboot verification material in KMU.
Only upload the supplied `firmware/zephyr.signed.bin`, or another image signed
with the matching key.

## Package layout

```text
firmware/zephyr.signed.bin       Signed application image to upload
flash/                           Cross-platform USB DFU flashing scripts
tools/nrfutil/                   Portable Windows nrfutil + mcu-manager plugin
test/                            Board test console and its instructions
SHA256SUMS                       SHA-256 hashes for every delivery file
```

## Put the board in USB DFU mode

The normal MicroPython USB CDC port is `2886:8013`. MCUboot USB recovery uses
`2886:0013`; use the latter for flashing.

1. Connect the board by USB.
2. Hold the **USER** button.
3. Press and release **RESET**.
4. Release **USER**.

The flasher waits for the recovery CDC port automatically. If it cannot find
the port, repeat the button sequence and check the USB cable.

## Windows (recommended)

Windows requires no Python installation and no Nordic tool installation. The
package includes a portable Windows `nrfutil` and the required `mcu-manager`
plugin.

From the package root, double-click `flash/flash_usb_dfu.cmd`, or run:

```powershell
.\flash\flash_usb_dfu.cmd
```

This is the recommended Windows entry point. It starts the primary Windows
flasher `xiao_nrf54lm20b_flash.ps1` with a process-local execution-policy
override, uploads `firmware/zephyr.signed.bin`, and requests a reset.

To select a specific firmware file or recovery COM port:

```powershell
.\flash\xiao_nrf54lm20b_flash.ps1 -Firmware .\firmware\zephyr.signed.bin -Port COM12
```

`COM12` is an example only. The DFU port is visible in Device Manager as a USB
serial device with VID:PID `2886:0013`.

## macOS

The included `tools/nrfutil/nrfutil.exe` is Windows-only. On macOS, install
Nordic **nRF Util** for macOS and make `nrfutil` available on `PATH`, then
install its MCU Manager plugin:

```sh
# Download/install nRF Util for macOS from Nordic, then:
nrfutil install mcu-manager
python3 -m pip install --user pyserial
chmod +x flash/xiao_nrf54lm20b_flash.sh
./flash/xiao_nrf54lm20b_flash.sh
```

Nordic download page: <https://www.nordicsemi.com/Products/Development-tools/nRF-Util/Download>

If automatic port discovery fails, specify the recovery port explicitly (often
`/dev/cu.usbmodem*`):

```sh
./flash/xiao_nrf54lm20b_flash.sh firmware/zephyr.signed.bin --port /dev/cu.usbmodemXXXX
```

On Apple Silicon, install the nRF Util build matching the host architecture.

## Linux

Install Nordic **nRF Util** for Linux and make `nrfutil` available on `PATH`.
Then install its MCU Manager plugin and the Python serial-port dependency:

```sh
# Download/install nRF Util for Linux from Nordic, then:
nrfutil install mcu-manager
python3 -m pip install --user pyserial
chmod +x flash/xiao_nrf54lm20b_flash.sh
./flash/xiao_nrf54lm20b_flash.sh
```

Nordic download page: <https://www.nordicsemi.com/Products/Development-tools/nRF-Util/Download>

If the recovery port is not detected automatically, pass it explicitly:

```sh
./flash/xiao_nrf54lm20b_flash.sh firmware/zephyr.signed.bin --port /dev/ttyACM0
```

On most distributions, a permission error for `/dev/ttyACM0` is resolved by
adding the user to the `dialout` group, then logging out and back in:

```sh
sudo usermod -aG dialout "$USER"
```

## About the cross-platform scripts

`flash/xiao_nrf54lm20b_flash.py` is the shared, cross-platform implementation.
`flash/xiao_nrf54lm20b_flash.sh` is the macOS/Linux entry point that finds
`python3` and calls that Python script. They require a locally installed
`nrfutil` with the `mcu-manager` plugin; `pyserial` is required only for
automatic USB-port discovery. Passing `--port` avoids the `pyserial`
requirement.

Windows users should use the PowerShell path above. It uses the bundled tool
and does not require Python. The Python script remains usable on Windows for
advanced use, but is not the recommended path.

## Run the board test console

See `test/README.md`. The test console is started from the MicroPython REPL:

```python
import xiao_nrf54lm20b_full_test as test
test.main()
```

## Integrity

`SHA256SUMS` contains hashes for all delivery files. Verify it after download
and do not replace the signed application image with an unsigned or
differently signed build.
