#!/usr/bin/env bash
# Build the XIAO STM32C5 MicroPython image and its UF2 package.
# No root privileges are required. Zephyr driver backports are applied only
# for the duration of this build and restored on exit.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PYTHON=${PYTHON:-python3}
WEST=${WEST:-west}
ZEPHYR_BASE=${ZEPHYR_BASE:-"$HOME/zephyrproject/zephyr"}
BUILD_DIR=${BUILD_DIR:-"$ROOT/build/xiao_stm32c5"}
BOARD_ROOT="${BUILD_DIR}.board-root"
BACKUP_ROOT="${BUILD_DIR}.zephyr-backup"
PATCH_LOCK_FILE="$ZEPHYR_BASE/.xiao_stm32c5_patch.lock"

if [[ ! -d "$ZEPHYR_BASE" ]]; then
    echo "error: ZEPHYR_BASE does not exist: $ZEPHYR_BASE" >&2
    exit 2
fi

if [[ ! -f "$ZEPHYR_BASE/VERSION" ]]; then
    echo "error: ZEPHYR_BASE does not contain a Zephyr VERSION file: $ZEPHYR_BASE" >&2
    exit 2
fi

if ! command -v "$WEST" >/dev/null 2>&1; then
    echo "error: west was not found; activate the Zephyr Python environment first" >&2
    exit 2
fi

zephyr_version=$(sed -n \
    -e 's/^VERSION_MAJOR[[:space:]]*=[[:space:]]*//p' \
    -e 's/^VERSION_MINOR[[:space:]]*=[[:space:]]*//p' \
    -e 's/^PATCHLEVEL[[:space:]]*=[[:space:]]*//p' \
    "$ZEPHYR_BASE/VERSION" | paste -sd. -)
if [[ "$zephyr_version" != "4.4.0" ]]; then
    echo "error: this board requires Zephyr 4.4.0, found ${zephyr_version:-unknown} at $ZEPHYR_BASE" >&2
    exit 2
fi

if command -v flock >/dev/null 2>&1; then
    exec 9>"$PATCH_LOCK_FILE"
    flock 9
else
    echo "warning: flock is unavailable; concurrent builds sharing $ZEPHYR_BASE are unsafe" >&2
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

# Storage-recovery patch on the MicroPython submodule (official 19a1aa3).
# paullbuth's validated firmware ran 19a1aa3 + these storage changes; without
# them the board hangs before the console starts. The submodule gitlink stays
# on the repo-wide pin (v1.27.0, shared with nrf54lm20b); this build checks out
# 19a1aa3 inside the submodule for the duration of the build and restores it
# on exit, then applies the storage patch on top.
MP_BASE=9939565d50acfcd68429e86b6276a590197db951  # official micropython, 2025-08-26, ancestor of master
MP_DIR="$ROOT/lib/micropython"
if ! git -C "$MP_DIR" cat-file -e "$MP_BASE^{commit}" 2>/dev/null; then
    # The submodule checkout (actions/checkout fetch-depth:1) only holds the
    # pinned commit. $MP_BASE is an ancestor of official micropython/master,
    # so it can be reached by deepening the fetch of master. Plain fetch and
    # --unshallow both fail on this shallow clone setup, so deepen explicitly.
    for depth in 2000 8000 20000; do
        echo "  fetching micropython history (depth $depth)..."
        if git -C "$MP_DIR" fetch -q --depth="$depth" origin master; then
            git -C "$MP_DIR" cat-file -e "$MP_BASE^{commit}" 2>/dev/null && break
        fi
    done
    if ! git -C "$MP_DIR" cat-file -e "$MP_BASE^{commit}" 2>/dev/null; then
        # Last resort: unshallow completely.
        git -C "$MP_DIR" fetch -q --unshallow origin 2>&1 | head -3 || true
        git -C "$MP_DIR" fetch -q origin || true
    fi
    if ! git -C "$MP_DIR" cat-file -e "$MP_BASE^{commit}" 2>/dev/null; then
        echo "error: micropython $MP_BASE unreachable (fetch-deepen failed)" >&2
        exit 2
    fi
fi
MP_ORIG_REF=$(git -C "$MP_DIR" rev-parse HEAD 2>/dev/null || true)
if [[ -n "$MP_ORIG_REF" ]] && [[ "$MP_ORIG_REF" != "$MP_BASE" ]]; then
    git -C "$MP_DIR" checkout -q "$MP_BASE" || {
        echo "error: cannot checkout micropython $MP_BASE in $MP_DIR" >&2
        exit 2
    }
    restore_micropython() {
        git -C "$MP_DIR" checkout -q "$MP_ORIG_REF" 2>/dev/null || true
        git -C "$MP_DIR" submodule update --init --recursive >/dev/null 2>&1 || true
    }
    trap 'restore_micropython; restore_patches' EXIT
fi
echo "  micropython checkout: $(git -C "$MP_DIR" rev-parse --short HEAD)"

# Backup files the patch MODIFIES (new files are created by the patch
# itself; track them for removal on restore).
MP_PATCH_ROOT="$BUILD_DIR.micropython-backup"
rm -rf "$MP_PATCH_ROOT"
mkdir -p "$MP_PATCH_ROOT"
for mp_file in ports/zephyr/Kconfig ports/zephyr/main.c \
               ports/zephyr/machine_pwm.c ports/zephyr/zephyr_storage.c \
               ports/zephyr/CMakeLists.txt ports/zephyr/modbluetooth_zephyr.c \
               py/mkrules.cmake; do
    mp_target="$ROOT/lib/micropython/$mp_file"
    if [[ -f "$mp_target" ]]; then
        mkdir -p "$MP_PATCH_ROOT/$(dirname "$mp_file")"
        cp -a "$mp_target" "$MP_PATCH_ROOT/$mp_file"
        RESTORE_TARGETS+=("$mp_target")
    fi
done
# New files the patch creates — track them so we can rm on restore.
for mp_new in ports/zephyr/modules/_boot.py \
              ports/zephyr/modules/boards/__init__.py \
              ports/zephyr/modules/boards/xiao.py \
              ports/zephyr/modules/boards/xiao_nrf54lm20a.py \
              py/makeqstrdefs_preprocessed.py; do
    RESTORE_TARGETS+=("$ROOT/lib/micropython/$mp_new")
done
if ! patch -d "$ROOT/lib/micropython" -p1 -N -r /dev/null \
        < "$ROOT/micropython/patches/0001-stm32c5-storage-recovery.patch" 2>/dev/null; then
    if patch -d "$ROOT/lib/micropython" -p1 -N --dry-run -R \
            < "$ROOT/micropython/patches/0001-stm32c5-storage-recovery.patch" >/dev/null 2>&1; then
        echo "  micropython storage patch already applied, skipping"
    else
        echo "error: micropython storage patch failed to apply" >&2
        exit 2
    fi
else
    echo "  applied micropython storage patch"
fi

export ZEPHYR_BASE

if [[ -z "${ZEPHYR_TOOLCHAIN_VARIANT:-}" ]] && command -v arm-none-eabi-gcc >/dev/null 2>&1; then
    export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb
    toolchain_bin=$(command -v arm-none-eabi-gcc)
    export GNUARMEMB_TOOLCHAIN_PATH="${GNUARMEMB_TOOLCHAIN_PATH:-$(dirname "$(dirname "$toolchain_bin")")}"
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
