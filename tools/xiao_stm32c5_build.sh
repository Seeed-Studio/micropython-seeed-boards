#!/usr/bin/env bash
# Build the XIAO STM32C5 MicroPython image and its UF2 package.
# No root privileges are required. Zephyr driver backports are applied only
# for the duration of this build and restored on exit.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
WEST=${WEST:-west}
ZEPHYR_BASE=${ZEPHYR_BASE:-"$HOME/zephyrproject/zephyr"}
BUILD_DIR=${BUILD_DIR:-"$ROOT/build/xiao_stm32c5"}
BOARD_ROOT="${BUILD_DIR}.board-root"
BACKUP_ROOT="${BUILD_DIR}.zephyr-backup"

if [[ ! -d "$ZEPHYR_BASE" ]]; then
    echo "error: ZEPHYR_BASE does not exist: $ZEPHYR_BASE" >&2
    exit 2
fi

if ! command -v "$WEST" >/dev/null 2>&1; then
    echo "error: west was not found; activate the Zephyr Python environment first" >&2
    exit 2
fi

rm -rf "$BOARD_ROOT" "$BACKUP_ROOT"
mkdir -p "$BOARD_ROOT/boards/seeed" "$BACKUP_ROOT"
cp -a "$ROOT/boards/seeed/xiao_stm32c5" "$BOARD_ROOT/boards/seeed/"

declare -a RESTORE_TARGETS=()

apply_patch() {
    local patch_file="$1"
    local target="$2"

    if [[ ! -f "$patch_file" ]]; then
        echo "error: missing patch file: $patch_file" >&2
        exit 2
    fi
    if [[ ! -f "$target" ]]; then
        echo "error: missing target file: $target" >&2
        exit 2
    fi

    local backup="$BACKUP_ROOT/$(basename "$target")"
    cp -a "$target" "$backup"
    RESTORE_TARGETS+=("$target")

    if ! patch -p0 -N -r /dev/null "$target" "$patch_file" 2>/dev/null; then
        # Check if already applied (reversed)
        if patch -p0 -N --dry-run -R "$target" "$patch_file" >/dev/null 2>&1; then
            echo "  patch $(basename "$patch_file") already applied, skipping"
        else
            echo "error: patch $(basename "$patch_file") failed to apply to $target" >&2
            exit 2
        fi
    else
        echo "  applied $(basename "$patch_file")"
    fi
}

restore_patches() {
    local target
    for target in "${RESTORE_TARGETS[@]}"; do
        local backup="$BACKUP_ROOT/$(basename "$target")"
        if [[ -f "$backup" ]]; then
            cp "$backup" "$target"
        fi
    done
}

trap restore_patches EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

apply_patch "$ROOT/zephyr/patches/zephyr-4.4.0/0001-udc-stm32-hal2-support.patch" \
    "$ZEPHYR_BASE/drivers/usb/udc/udc_stm32.c"
apply_patch "$ROOT/zephyr/patches/zephyr-4.4.0/0002-flash-stm32-xspi-hal2-support.patch" \
    "$ZEPHYR_BASE/drivers/flash/flash_stm32_xspi.c"
apply_patch "$ROOT/zephyr/patches/zephyr-4.4.0/0003-flash-stm32-xspi-hal2-support.patch" \
    "$ZEPHYR_BASE/drivers/flash/flash_stm32_xspi.h"
apply_patch "$ROOT/zephyr/patches/zephyr-4.4.0/0004-adc-stm32-fix-pcsel-preselection.patch" \
    "$ZEPHYR_BASE/drivers/adc/adc_stm32.c"

export ZEPHYR_BASE

if [[ -z "${ZEPHYR_TOOLCHAIN_VARIANT:-}" ]] && command -v arm-none-eabi-gcc >/dev/null 2>&1; then
    export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
    export GNUARMEMB_TOOLCHAIN_PATH="${GNUARMEMB_TOOLCHAIN_PATH:-$(dirname "$(dirname "$(command -v arm-none-eabi-gcc)")")}"
fi

"$WEST" build \
    --build-dir "$BUILD_DIR" \
    "$ROOT/lib/micropython/ports/zephyr" \
    --pristine \
    --board xiao_stm32c5 \
    -- \
    -DBOARD_ROOT="$BOARD_ROOT" \
    -DEXTRA_CONF_FILE="$ROOT/boards/xiao_stm32c5.conf" \
    -DEXTRA_DTC_OVERLAY_FILE="$ROOT/boards/xiao_stm32c5.overlay" \
    -DUSER_C_MODULES="$ROOT/src/cmodules/modadc;$ROOT/src/cmodules/modrtc;$ROOT/src/cmodules/modcan"

BIN="$BUILD_DIR/zephyr/zephyr.bin"
UF2="$BUILD_DIR/zephyr/micropython-xiao-stm32c5.uf2"
if [[ ! -f "$BIN" ]]; then
    echo "error: expected build output is missing: $BIN" >&2
    exit 1
fi

"$PYTHON" "$ROOT/tools/uf2conv.py" \
    --input "$BIN" \
    --output "$UF2" \
    --base 0x08008000 \
    --family-id 0x00C5C5C5

echo "Build complete:"
echo "  ELF: $BUILD_DIR/zephyr/zephyr.elf"
echo "  BIN: $BIN"
echo "  HEX: $BUILD_DIR/zephyr/zephyr.hex"
echo "  UF2: $UF2"
