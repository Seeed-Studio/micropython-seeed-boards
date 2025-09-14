# MicroPython for Seeed board

This README provides instructions for building and running MicroPython firmware on the Seeed XIAO board using the Zephyr RTOS. The port is based on MicroPython's Zephyr port, which supports various Zephyr-compatible boards, including the XIAO nRF52840 and XIAO nRF54L15.

## Prerequisites

Before building the MicroPython firmware, ensure you have the following:

1. **Zephyr Development Environment**:
    - Install the Zephyr SDK and set up the development environment by following the [Zephyr Getting Started Guide](https://docs.zephyrproject.org/latest/getting_started/index.html).
    - Ensure you have Zephyr version 4.0 or later installed, as the Xiao nRF54L15 requires a recent version due to its nRF54L15 SoC.
    - Example command to initialize Zephyr v4.0.0:
      ```bash
      west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.0.2 ncs
      cd ncs
      west update
      west zephyr-export
      pip3 install -r zephyr/scripts/requirements.txt
      cd ..
      ```
    - Install Zephyr SDK:
      ```bash
      wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.17.0/zephyr-sdk-0.17.0_linux-x86_64.tar.xz
      mkdir -p ~/zephyr-sdk
      tar -xvf zephyr-sdk-0.17.0_linux-x86_64.tar.xz -C ~/zephyr-sdk
      cd ~/zephyr-sdk/zephyr-sdk-0.17.0
      ./setup.sh -t all -h
      ```
    - Source the Zephyr environment:
      ```bash
      source ncs/zephyr/zephyr-env.sh
      ```

2. **MicroPython Repository**:
    - Clone the MicroPython repository to your local machine:
      ```bash
      git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git
      cd micropython-seeed-boards/lib/micropython
      gh pr checkout 18030
      ```

3. **Dependencies**:
    - Install required tools: Python 3.10 or later, CMake 3.20.0 or later, and the Zephyr SDK toolchain.
    - Verify the installation by building a sample Zephyr application to confirm your setup.

## Building the Firmware

To build the MicroPython firmware for the Seeed Xiao nRF54L15 or Xiao nRF52840, run the following commands from the root of your project directory (where the `lib/micropython/ports/zephyr` directory exists):

### For Xiao nRF54L15
```bash
export PROJECT_DIR=$(pwd)
west build ./lib/micropython/ports/zephyr --pristine --board xiao_nrf54l15/nrf54l15/cpuapp --sysbuild -- -DBOARD_ROOT=$PROJECT_DIR/ -DEXTRA_DTC_OVERLAY_FILE=$PROJECT_DIR/boards/xiao_nrf54l15_nrf54l15_cpuapp.overlay -DPM_STATIC_YML_FILE=$PROJECT_DIR/boards/pm_static_xiao_nrf54l15_nrf54l15_cpuapp.yml -DEXTRA_CONF_FILE=$PROJECT_DIR/boards/xiao_nrf54l15_nrf54l15_cpuapp.conf
```

### For Xiao nRF52840
```bash
west build ./lib/micropython/ports/zephyr --pristine --board xiao_ble
```

### Command Breakdown
- `./lib/micropython/ports/zephyr`: Specifies the MicroPython Zephyr port directory as the application source.
- `--pristine`: Ensures a clean build by removing any previous build artifacts.
- `--board xiao_nrf54l15/nrf54l15/cpuapp`: Specifies the target board and CPU (nRF54L15 application core).
- `--sysbuild`: Enables Zephyr's sysbuild system for multi-image builds.
- `-DBOARD_ROOT=./`: Sets the board root directory to the current project directory, where the Xiao nRF54L15 board files are located.

### Optional: Minimal Build
For a smaller firmware size (below 128KB, with minimal features like UART REPL), use the `prj_minimal.conf` configuration:

#### For Xiao nRF54L15
```bash
export PROJECT_DIR=$(pwd)
west build ./lib/micropython/ports/zephyr --pristine --board xiao_nrf54l15/nrf54l15/cpuapp --sysbuild -- \
 -DBOARD_ROOT=$PROJECT_DIR/ -DEXTRA_DTC_OVERLAY_FILE=$PROJECT_DIR/boards/xiao_nrf54l15_nrf54l15_cpuapp.overlay -DCONF_FILE=./lib/micropython/ports/zephyr/prj_minimal.conf
```

#### For Xiao nRF52840
```bash
west build ./lib/micropython/ports/zephyr --pristine --board xiao_ble -- -DCONF_FILE=./lib/micropython/ports/zephyr/prj_minimal.conf
```

#### For Xiao esp32c5
* For the MicroPython firmware of the Seeed XIAO ESP32C5, a CI (Continuous Integration) automatic compilation workflow has been added. You only need to download the corresponding firmware from the release and use the appropriate flashing method.
* Here, the esptool tool is recommended for flashing. It should be noted that when flashing the MicroPython firmware, **the starting address must be specified as 0x2000.**
```bash
# e.g. Flashing the Firmware
esptool.py --chip esp32c5 --port /dev/cu.usbmodem11301 --baud 460800 write_flash -z 0x2000 micropython_xiao_esp32c5.bin
```

### Notes
- If you encounter issues with undefined Kconfig symbols (e.g., `NET_SOCKETS_POSIX_NAMES`), check the `lib/micropython/ports/zephyr/prj.conf` file and comment out or remove unsupported configurations.
- Ensure the Zephyr version matches the requirements of the MicroPython port (v4.0 is recommended).

## Flashing the Firmware

To flash the compiled firmware to the Xiao nRF54L15 board:

```bash
west flash
```

## Debugging
To flash the firmware and start a GDB debug session:

```bash
west debug
```

## Running MicroPython by Thonny IDE

Install and open thonny, then configure Thonny following the instruction:

```bash
pip install thonny
thonny
```

Go to Run-->Configure Interpreter, select "MicroPython (generic)" and port, then clicking OK, select the port in the lower right corner, usually showing as MicroPython(generic) · Virtual COM-Port @COMX.

Then go to File->Open, select MicroPython device, copy the example/boards folder to the file system, and click OK. You can then open the example program in the example directory through Thonny and press `F5` to run it:

```python
import time
from boards.xiao import XiaoPin

led = "led"

try:
    # Initialize LED
    led = XiaoPin(led, XiaoPin.OUT)
    while True:
        # LED 0.5 seconds on, 0.5 seconds off
        led.value(1)
        time.sleep(0.5)
        led.value(0)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nProgram interrupted by user")
except Exception as e:
    print("\nError occurred: %s" % {e})
finally:
    led.value(1)
```

## Features
The MicroPython Zephyr port supports:
- REPL over UART console.
- `machine.Pin` for GPIO control with IRQ support.
- `machine.I2C`, `machine.SPI`, and `machine.PWM` for peripheral control.
- `socket` module for networking (IPv4/IPv6, if enabled).
- Virtual filesystem with FAT or littlefs, backed by flash storage.
- Frozen modules for bundling Python code with the firmware.

Refer to the [MicroPython Zephyr port documentation](https://github.com/micropython/micropython/tree/master/ports/zephyr) for more details.

## Troubleshooting
- **Kconfig Errors**: If you see errors like `undefined symbol NET_SOCKETS_POSIX_NAMES`, edit `lib/micropython/ports/zephyr/prj.conf` and remove or comment out the problematic line.
- **Board Not Found**: Ensure the Xiao nRF54L15 board files are in `./boards/seeed/xiao_nrf54l15/`.
- **Build Failures**: Check `build/CMakeFiles/CMakeError.log` for detailed error messages.
- **Zephyr Version Mismatch**: Ensure you are using Zephyr v4.0 or later, as older versions may not support the nRF54L15 SoC.

For further assistance, consult the [Zephyr Documentation](https://docs.zephyrproject.org) or the MicroPython community.
