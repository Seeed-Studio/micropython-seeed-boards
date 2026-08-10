# MicroPython for Seeed board

This README file provides instructions for building and running MicroPython firmware on select Seeed XIAO development boards.

## Install Development Environment 

Before building the MicroPython firmware, ensure you have the following:

1. **Zephyr Development Environment**:
    - Install required tools: Python 3.10 or later, CMake 3.20.0 or later, Ninja, DTC, `west`, and the Zephyr SDK toolchain.
    - Install dependences:
      ```bash
      sudo apt-get update
      sudo apt-get install -y git cmake ninja-build gperf ccache \
      dfu-util device-tree-compiler python3-dev python3-pip python3-setuptools \
      python3-tk python3-wheel xz-utils file libpython3-dev libffi-dev gh
      pip3 install west
      pip install requests
      pip install pyelftools
      ```
    - Install the Zephyr SDK and set up the development environment by following the [Zephyr Getting Started Guide](https://docs.zephyrproject.org/latest/getting_started/index.html).
    - Nordic `nRF54` boards are built with the **Nordic nRF Connect SDK (NCS)**, pinned per board so Zephyr and the Nordic SoC support stay aligned:
      - **XIAO nRF54LM20A**: NCS **v3.3.0** (validated; see `.github/workflows/build_micropython_xiao_nrf54lm20a.yml`).
      - **XIAO nRF54L15**: NCS **v3.0.2** (the revision its CI builds against; see `.github/workflows/build_micropython_xiao_nrf54l15.yml`).
    - Example commands to initialize a Nordic SDK workspace:
      ```bash
      # XIAO nRF54LM20A
      west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.3.0 zephyrproject
      west update && west zephyr-export

      # XIAO nRF54L15
      west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.0.2 zephyrproject
      west update && west zephyr-export

      # e.g. for XIAO MG24
      west init zephyrproject -m https://github.com/zephyrproject-rtos/zephyr --mr v4.2.0
      cd zephyrproject/zephyr && west update && west blobs fetch hal_silabs

      pip3 install -r zephyr/scripts/requirements.txt && cd ..
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
    - Clone the MicroPython repository to your local machine:
      ```bash
      git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git
      cd micropython-seeed-boards/lib/micropython
      gh pr checkout 18030
      ```
2. **ESP32 Developement Environment**:
    - Install required tools: Python 3.10 or later, CMake 3.20.0 or later, esptool, and the ESP32 toolchain.
    - Install dependences:
      ```bash
      sudo apt-get update
      sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 gh 
      ```
    - Install ESP-IDF:
      ```bash
      cd ~
      git clone -b v5.5 --recursive https://github.com/espressif/esp-idf.git
      cd ~/esp-idf
      git submodule update --init --recursive
      ./install.sh esp32
      . ./export.sh
      ```
    - Source the ESP-IDF environment:
      ```bash
      source ~/esp-idf/export.sh 
      ```
    - Clone the MicroPython repository to your local machine:
      ```bash
      git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git && cd micropython-seeed-boards/lib 
      rm -rf micropython
      git clone https://github.com/micropython/micropython.git
      cd micropython
      gh pr checkout 17912
      git submodule update --init --recursive
      git submodule update --init lib/berkeley-db-1.xx
      ```
3. **Renesas RA Developement Environment**:
    - Install dependences:
      ```bash
      sudo apt-get update
      sudo apt-get install -y git make cmake ninja-build gperf ccache gcc-arm-none-eabi dfu-util device-tree-compiler python3-dev python3-pip python3-setuptools python3-tk python3-wheel xz-utils file libpython3-dev libffi-dev gh
      ```
    - Clone the MicroPython repository to your local machine:
      ```bash
      cd lib && rm -r micropython || true
      git clone https://github.com/micropython/micropython.git
      cd micropython && git submodule update --init --recursive && gh pr checkout 16409
      ```

## Building the Firmware

To build the MicroPython firmware for the Zephyr boards or ESP32 boards, run the following commands from the root of your project directory (where the `lib/micropython/ports/zephyr` or `lib/micropython/ports/esp32` directory exists):

1. **Building for Zephyr Boards**:
    - The Nordic `nRF54` boards in this repository are built with `sysbuild` and board-specific overlay/config files.
    - Before building Nordic `nRF54` boards, make sure the Zephyr or NCS environment is active and `ZEPHYR_SDK_INSTALL_DIR` is set correctly for your machine.
    - For XIAO nRF54L15:
      ```bash
      cd micropython-seeed-boards && export PROJECT_DIR=$(pwd)
      west build ./lib/micropython/ports/zephyr --pristine --board xiao_nrf54l15/nrf54l15/cpuapp --sysbuild -- -DBOARD_ROOT=$PROJECT_DIR/ -DEXTRA_DTC_OVERLAY_FILE=$PROJECT_DIR/boards/xiao_nrf54l15_nrf54l15_cpuapp.overlay -DPM_STATIC_YML_FILE=$PROJECT_DIR/boards/pm_static_xiao_nrf54l15_nrf54l15_cpuapp.yml -DEXTRA_CONF_FILE=$PROJECT_DIR/boards/xiao_nrf54l15_nrf54l15_cpuapp.conf
      ```
    - For XIAO nRF54LM20A:
      ```bash
      cd micropython-seeed-boards && export PROJECT_DIR=$(pwd)
      west build ./lib/micropython/ports/zephyr --pristine --board xiao_nrf54lm20a/nrf54lm20a/cpuapp --sysbuild -- -DBOARD_ROOT=$PROJECT_DIR/ -DEXTRA_DTC_OVERLAY_FILE=$PROJECT_DIR/boards/xiao_nrf54lm20a_nrf54lm20a_cpuapp.overlay -DPM_STATIC_YML_FILE=$PROJECT_DIR/boards/pm_static_xiao_nrf54lm20a_nrf54lm20a_cpuapp.yml -DEXTRA_CONF_FILE=$PROJECT_DIR/boards/xiao_nrf54lm20a_nrf54lm20a_cpuapp.conf
      ```
    - For XIAO nRF52840:
      ```bash
      west build ./lib/micropython/ports/zephyr --pristine --board xiao_ble
      ```
    - For XIAO MG24:
      ```bash
      cd micropython-seeed-boards && export ZEPHYR_SDK_INSTALL_DIR="~/zephyr-sdk/zephyr-sdk-0.17.0"
      export PATH="$ZEPHYR_SDK_INSTALL_DIR:$PATH"
      export PROJECT_DIR=$(pwd)
      west build lib/micropython/ports/zephyr -b xiao_mg24 --pristine -- -DCONF_FILE=$PROJECT_DIR/boards/xiao_mg24.conf -DEXTRA_DTC_OVERLAY_FILE=$PROJECT_DIR/boards/xiao_mg24.overlay -DUSER_C_MODULES="$PROJECT_DIR/src/cmodules/modadc;$PROJECT_DIR/src/cmodules/modrtc;"
      ```
    - If you encounter issues with undefined Kconfig symbols, first confirm that your NCS or Zephyr version matches the board family you are building.
    - On Windows, if the build fails because of very long command lines during qstr generation, move the repository to a shorter path such as `C:\src\micropython-seeed-boards`.
    - Build artifacts for `nRF54` boards are generated under `build/<board-name>/`, including `merged.hex`, `zephyr.hex`, and `zephyr.elf`.
2. **Building for ESP32 Boards**:
    - Example For ESP32 Boards:
      ```bash
      cd micropython-seeed-boards/lib/micropython/ports/esp32
      rm -rf build-ESP32_GENERIC
      make BOARD=ESP32_GENERIC
      ```
3. **Building for Renesas RA Boards**:
    - Example For XIAO RA4M1 CORE and Other RA Boards:
      ```bash
      cd micropython-seeed-boards/lib/micropython/ports/renesas-ra
      make BOARD_DIR=../../../../boards/seeed/xiao_ra4m1
      ```

## Flashing the Firmware

The compiled firmware is available at https://github.com/Seeed-Studio/micropython-seeed-boards/releases. To flash the compiled firmware to the Zeyphr boards and ESP32 boards, run the following command from the root of your project directory:

1. **Flashing for Zephyr Boards**:
    - `nRF54` boards in this repository provide dedicated flash helpers under `tools/`.
    - Copy the compiled firmware into the corresponding flash tool folder before running the helper script:
      ```bash
      # e.g. for XIAO nRF54L15
      cd micropython-seeed-boards/tools/xiao_nrf54l15_flash
      # e.g. for Windows
      ./xiao_nrf54l15_flash.bat
      # e.g. for Linux and Mac
      chmod +x xiao_nrf54l15_flash.sh && ./xiao_nrf54l15_flash.sh
      
      # e.g. for XIAO MG24
      cd micropython-seeed-boards/tools/xiao_mg24_flash
      # e.g. for Windows
      python -m venv venv
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
      .\venv\Scripts\Activate.ps1
      ./xiao_mg24_flash.bat
      # e.g. for Linux and Mac
      chmod +x xiao_mg24_flash.sh && ./xiao_mg24_flash.sh
      ```
    - For XIAO nRF54LM20A:
      ```bash
      cd micropython-seeed-boards/tools/xiao_nrf54lm20a_flash

      # Windows
      ./flash.bat

      # Linux / macOS
      chmod +x ./xiao_nrf54lm20a_flash.sh
      ./xiao_nrf54lm20a_flash.sh
      ```
    - The XIAO nRF54LM20A flash helper uses **OpenOCD by default** to match the validated flashing flow used by Seeed's Nordic board support.
    - If `openocd` is already available in your system `PATH`, the script uses it first. If the detected version is not the validated version family, the script prints a warning and you can rerun with:
      ```bash
      python xiao_nrf54lm20a_flash.py --install-openocd
      ```
    - If `openocd` is not installed, the script automatically downloads and installs the validated OpenOCD package into a per-user default directory:
      - Windows: `%LOCALAPPDATA%\Seeed\OpenOCD`
      - macOS: `~/Library/Application Support/Seeed/OpenOCD`
      - Linux: `~/.local/share/seeed/openocd`
    - If multiple CMSIS-DAP probes are connected, list them first and then flash with the selected probe ID:
      ```bash
      python -m pyocd list --probes
      python xiao_nrf54lm20a_flash.py --probe <probe_id>
      ```
2. **Flashing for ESP32 Boards**:
    - The esptool tool is recommended for flashing. It should be noted that when flashing the MicroPython firmware, **the starting address must be specified as 0x2000.**
    - Example for ESP32 boards:
      ```bash
      # e.g. for Linux
      esptool.py --chip esp32 --port /dev/cu.usbmodem11301 --baud 460800 write_flash -z 0x2000 firmware.bin
      # e.g. for Windows
      esptool --chip esp32 --port COM7 --baud 460800 write_flash -z 0x2000 .\firmware.bin
      ```
3. **Flashing for Renesas RA Boards**:
    - You first need to put the compiled firmware into the flash tool folder of XIAO RA4M1, and then run the following command, the prerequisite is that you must use XIAO Debugger to connect to the XIAO RA4M1 board:
      ```bash
      cd micropython-seeed-boards/tools/xiao_ra4m1_flash
      # e.g. for Windows
      ./xiao_ra4m1_flash.bat
      # e.g. for Linux and Mac
      chmod +x xiao_ra4m1_flash.sh && ./xiao_ra4m1_flash.sh
      ```

## Running MicroPython by Thonny IDE

1. **Install Thonny IDE**:
    - Install and open thonny, then configure Thonny following the instruction:
      ```bash
      pip install thonny
      thonny
      ```
2. **Configure Thonny Interpreter**:
    - Go to Run-->Configure Interpreter, select "MicroPython (generic)" and port, then clicking OK, select the port in the lower right corner, usually showing as MicroPython(generic) · Virtual COM-Port @COMX.
    - On boards that ship with the frozen `boards.xiao` helper package, such as XIAO nRF54LM20A, you can use the helper APIs directly without uploading the `example/boards` directory first.
    - On older firmware builds that do not freeze `boards.xiao`, copy the `example/boards` folder to the device file system before running board helper examples.
    - You can then open the example program in the `example` directory through Thonny and press `F5` to run it:
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
- **Zephyr / NCS Version Mismatch**: Use a Zephyr or NCS release that already supports your target SoC. For `nRF54LM20A`, use Nordic nRF Connect SDK v3.3.0 or later.
- **Multiple Debug Probes Connected**: Run `python -m pyocd list --probes` and pass `--probe <probe_id>` to the nRF54LM20A flash script.
- **OpenOCD Flashing Issues on nRF54LM20A**: If your system `openocd` is too old or not built with `nRF54LM20A` support, rerun the script with `--install-openocd` to use the validated package managed by the script.

For further assistance, consult the [Zephyr Documentation](https://docs.zephyrproject.org) or the MicroPython community.
