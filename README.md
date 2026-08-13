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

### XIAO nRF54LM20B (SWD baseline)

The XIAO nRF54LM20B uses a pre-provisioned USB DFU boot chain.  The
MicroPython build produces only a signed application for its fixed slot0
partition; it does not rebuild or overwrite MCUboot.

Requirements:

- Python 3.10 or newer, CMake 3.20 or newer, Ninja, DTC and `west`.
- Nordic nRF Connect SDK v3.3.0 or newer.
- Zephyr SDK 0.17.0, including both `arm-zephyr-eabi` and
  `riscv64-zephyr-elf` toolchains. The RISC-V toolchain is needed for the
  nRF54LM20 FLPR child image; a host-only `arm-none-eabi-gcc` installation is
  not sufficient for sysbuild.
- A J-Link probe and J-Link Software v9.24 or newer. The validated J-Link
  device name is `nRF54LM20A_M33` because the 20B board uses nRF54LM20A/B
  compatible silicon and the `cpuapp` qualifier is `nrf54lm20b`.

Linux/macOS clean-environment setup and build:

```bash
python3 -m pip install --user west
git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git
cd micropython-seeed-boards
git submodule update --init --recursive

cd ..
west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.3.0 ncs-workspace
cd ncs-workspace
west update
west zephyr-export
source zephyr/zephyr-env.sh
cd ../micropython-seeed-boards

export PROJECT_DIR="$PWD"
# Path to the private key whose public part was provisioned into the device KMU.
# Keep this key outside the repository.
export MCUBOOT_SIGNING_KEY="/absolute/path/to/root-ed25519.pem"
west build "$PROJECT_DIR/lib/micropython/ports/zephyr" \
  --pristine \
  --no-sysbuild \
  --board xiao_nrf54lm20b/nrf54lm20b/cpuapp -- \
  -DBOARD_ROOT="$PROJECT_DIR" \
  -DEXTRA_DTC_OVERLAY_FILE="$PROJECT_DIR/boards/xiao_nrf54lm20b_nrf54lm20b_cpuapp.overlay" \
  -DEXTRA_CONF_FILE="$PROJECT_DIR/boards/xiao_nrf54lm20b_nrf54lm20b_cpuapp.conf" \
  -DCONFIG_MCUBOOT_SIGNATURE_KEY_FILE:STRING=\"${MCUBOOT_SIGNING_KEY}\"
```

Windows PowerShell clean-environment setup and build:

```powershell
py -m pip install west
git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git
Set-Location micropython-seeed-boards
git submodule update --init --recursive

Set-Location ..
west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.3.0 ncs-workspace
Set-Location ncs-workspace
west update
west zephyr-export
.\zephyr\zephyr-env.cmd
Set-Location ..\micropython-seeed-boards

$env:PROJECT_DIR = (Get-Location).Path
# The corresponding public key is already provisioned in KMU; do not add this
# private signing key to the repository.
$env:MCUBOOT_SIGNING_KEY = "D:/path/to/root-ed25519.pem"
west build "$env:PROJECT_DIR\lib\micropython\ports\zephyr" `
  --pristine `
  --no-sysbuild `
  --board xiao_nrf54lm20b/nrf54lm20b/cpuapp -- `
  "-DBOARD_ROOT=$env:PROJECT_DIR" `
  "-DEXTRA_DTC_OVERLAY_FILE=$env:PROJECT_DIR/boards/xiao_nrf54lm20b_nrf54lm20b_cpuapp.overlay" `
  "-DEXTRA_CONF_FILE=$env:PROJECT_DIR/boards/xiao_nrf54lm20b_nrf54lm20b_cpuapp.conf" `
  ('-DCONFIG_MCUBOOT_SIGNATURE_KEY_FILE:STRING="{0}"' -f $env:MCUBOOT_SIGNING_KEY)
```

The important build outputs are:

```text
build/xiao_nrf54lm20b/zephyr/zephyr.elf
build/xiao_nrf54lm20b/zephyr/zephyr.signed.bin
```

For SWD provisioning, flash the prebuilt bootloader package separately, then
program only the signed application at slot0.  For normal updates, upload
`zephyr.signed.bin` through the pre-provisioned USB DFU loader.

```text
JLinkExe -device nRF54LM20A_M33 -if SWD -speed 4000 -autoconnect 1
J-Link> r
J-Link> h
J-Link> loadfile build/xiao_nrf54lm20b/zephyr/zephyr.signed.hex
J-Link> r
J-Link> g
J-Link> q
```

After reset, the application exposes the MicroPython REPL over USB CDC ACM
(VID:PID `2886:8013`). Copy the test script to the MicroPython filesystem
with `mpremote`, then run:

Linux/macOS example:

```bash
python3 -m pip install mpremote
mpremote connect /dev/ttyACM0 fs cp example/xiao_nrf54lm20b_full_test.py :xiao_nrf54lm20b_full_test.py
```

Windows PowerShell example:

```powershell
py -m pip install mpremote
mpremote connect COM7 fs cp example\xiao_nrf54lm20b_full_test.py :xiao_nrf54lm20b_full_test.py
```

```python
import xiao_nrf54lm20b_full_test as test
test.main()
```

The test console supports `help`, `status`, `all`, `uart`, `adc`, `pwm`,
`i2c`, `led`, `io`, `imu`, `battery`, `ble`, `pdm`, `spi`, and `exit`.
UART21 loopback requires a jumper from P1.8 to P1.9. BLE visibility requires
a phone or another BLE scanner. The battery test reads the nPM1300 fuel-gauge
sensor when the charger device is available. It reports `SKIP` if the sensor
driver is unavailable; ADC7 must not be treated as VBAT without a board-level
mapping.

Formal firmware archives are intentionally not produced in this bring-up
phase. USB DFU, signed application packages, rollback and release packaging
are follow-up work.

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

## XIAO STM32C5 MicroPython

This repository includes a Zephyr/MicroPython port for the Seeed XIAO STM32C5.
The v1 user flow is TinyUF2 double-reset bootloader plus a USART1 REPL. USB
CDC REPL and 1200-bps automatic bootloader entry are not required for v1.

### Supported build environment

The reproducible build uses Python 3.12, west 1.5 or newer, CMake 3.20 or
newer, Ninja, device-tree compiler, and an ARM Cortex-M33 compiler. Zephyr
4.4.0 is the validated framework revision. Either a user-installed Zephyr SDK
or GNU Arm Embedded GCC may be used. No `sudo` is needed when these tools are
already available or installed under the user's home directory.

From a clean checkout, initialize the MicroPython submodule and a user-owned
Zephyr workspace:

```bash
git clone --recurse-submodules https://github.com/Seeed-Studio/micropython-seeed-boards.git
cd micropython-seeed-boards
python3 -m venv .venv/micropython-c5
source .venv/micropython-c5/bin/activate
python -m pip install --upgrade pip west jsonschema pyelftools requests PyYAML
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.4.0 zephyrproject
cd zephyrproject
west update
cd ..
export ZEPHYR_BASE="$PWD/zephyrproject/zephyr"
```

If using GNU Arm Embedded GCC, set its user/system prefix explicitly when it
is not in `PATH`:

```bash
export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
export GNUARMEMB_TOOLCHAIN_PATH="/path/to/arm-toolchain-prefix"
```

Build from the repository root:

```bash
source .venv/micropython-c5/bin/activate
ZEPHYR_BASE="$PWD/zephyrproject/zephyr" \
  PYTHON="$PWD/.venv/micropython-c5/bin/python" \
  WEST="$PWD/.venv/micropython-c5/bin/west" \
  tools/xiao_stm32c5/build.sh
```

The script stages the board root, temporarily applies the STM32C5 HAL2 USB
and XSPI backports, restores the Zephyr workspace on exit, and generates:

```text
build/xiao_stm32c5/zephyr/zephyr.elf
build/xiao_stm32c5/zephyr/zephyr.bin
build/xiao_stm32c5/zephyr/zephyr.hex
build/xiao_stm32c5/zephyr/micropython-xiao-stm32c5.uf2
```

The UF2 application address is `0x08008000`, the family ID is
`0x00C5C5C5`, and the TinyUF2 volume label is `XIAOC5BOOT`. Verify checksums
with `sha256sum` before distributing a file.

### Zephyr version and driver backports

The XIAO STM32C5 port is validated against **Zephyr 4.4.0**; `build.sh`
refuses to build against any other revision. STM32C5 HAL2 support in the
upstream UDC and XSPI flash drivers landed only after the 4.4.0 release
(Zephyr PR #105957), so this repository carries four backport patches under
`zephyr/patches/zephyr-4.4.0/`:

- `0001-udc-stm32-hal2-support.patch` - USB DRD UDC HAL2 support
- `0002-flash-stm32-xspi-hal2-support.patch` - XSPI flash HAL2 support (driver)
- `0003-flash-stm32-xspi-hal2-support.patch` - XSPI flash HAL2 support (header)
- `0004-adc-stm32-fix-pcsel-preselection.patch` - ADC PCSEL preselection fix

`tools/xiao_stm32c5/build.sh` backs up each target file, applies its patch
in place, builds, and restores the originals on exit (guarded by `flock` so
concurrent builds are safe). The CI workflow pins Zephyr to `--mr v4.4.0` so
the patches apply cleanly.

> **Maintainer note:** when upgrading to a newer Zephyr revision, regenerate
> or replace the `zephyr/patches/zephyr-4.4.0/` patches against the new tree
> (patch context lines move between revisions), and update the version check
> in `tools/xiao_stm32c5/build.sh` plus the `--mr v4.4.0` pin in
> `.github/workflows/build_micropython_xiao_stm32c5.yml`. A patch that fails
> to apply fails the build with a clear error rather than silently producing a
> broken image.

### Flashing and REPL

1. Connect the board with USB and double-click Reset.
2. Wait for the `XIAOC5BOOT` mass-storage volume.
3. Copy `micropython-xiao-stm32c5.uf2` to that volume. TinyUF2 processes the
   file and reboots the board automatically.
4. Connect a 3.3-V UART adapter to USART1: PA9 is TX, PA10 is RX, and GND is
   common. Use 115200 8-N-1. USB CDC REPL is not the v1 acceptance path.
5. Copy or paste `example/xiao_stm32c5_full_test.py` into the MicroPython
   filesystem and run the single full test entry point:

```python
import xiao_stm32c5_full_test as test
test.main()
```

This full script combines the base-peripheral and FDCAN coverage. It runs
LED, GPIO, ADC, PWM, I2C, IMU, battery, UART, RTC, LittleFS, and all 9 FDCAN
regression tests; tests requiring external wiring report `SKIP` when absent.

The user-side flash flow requires only the operating system's mass-storage
copy operation; it does not require PlatformIO, ST-Link, J-Link, Python, or a
local compiler.

### Test wiring and limitations

The interactive test accepts `help`, `status`, `all`, `uart`, `adc`, `pwm`,
`fdcan`, `i2c`, `led on|off|blink`, `io <pin> [count]`, `imu`, `battery`, and
`exit`. Every test reports `PASS`, `FAIL`, or `SKIP` and uses bounded waits.

- Header I2C1 is D4/PB7 SDA and D5/PB6 SCL.
- The onboard LSM6DS3TR-C is on I2C2, PB3/PB4, address `0x6A`.
- UART loopback connects PA9 to PA10; do not run it while relying on that
  same UART for the active REPL.
- PWM uses internal PA8/TIM1_CH1 and requires an oscilloscope, LED, or test
  point for waveform confirmation.
- FDCAN uses FDCAN2 on PB5/PB13 with PB14 as transceiver standby. Loopback
  needs no external bus; external testing needs a CAN transceiver and a
  correctly terminated 120-ohm bus.
- Battery testing requires a supported battery, BAT_EN on PE2, and the
  battery sense input on PA4/ADC1_IN4. The script reports `SKIP` when no
  voltage is present.
- D8-D10 are GPIO-capable in this mapping; no hardware SPI capability is
  promised for those pins.

### Release package

After a successful build, create the self-contained package with:

```bash
tools/xiao_stm32c5/package.sh 0.1.0
```

The output is placed under `dist/` and contains `firmware/`, `tests/`, a
standalone README, release notes, `LICENSE`, and `SHA256SUMS.txt`. A package
is not a formal release until the real-board TinyUF2, upgrade/rollback,
wrong-UF2 recovery, and ten-cycle acceptance records have been completed.

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
