#!/usr/bin/env bash
# Assemble the self-contained XIAO STM32C5 release package.

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
VERSION=${1:-dev}
BUILD_DIR=${BUILD_DIR:-"$ROOT/build/xiao_stm32c5"}
OUTPUT_ROOT=${OUTPUT_ROOT:-"$ROOT/dist"}
PACKAGE_NAME="xiao-stm32c5-micropython-$VERSION"
PACKAGE_DIR="$OUTPUT_ROOT/$PACKAGE_NAME"
UF2="$BUILD_DIR/zephyr/micropython-xiao-stm32c5.uf2"

if [[ ! -f "$UF2" ]]; then
    echo "error: build the firmware first; missing $UF2" >&2
    exit 2
fi

rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR/firmware" "$PACKAGE_DIR/tests"
cp "$UF2" "$PACKAGE_DIR/firmware/"
cp "$ROOT/example/xiao_stm32c5_full_test.py" "$PACKAGE_DIR/tests/"
cp "$ROOT/release/xiao_stm32c5/README.md" "$PACKAGE_DIR/README.md"
sed "s/{{VERSION}}/$VERSION/g" \
    "$ROOT/release/xiao_stm32c5/RELEASE_NOTES.md" > "$PACKAGE_DIR/RELEASE_NOTES.md"
cp "$ROOT/LICENSE" "$PACKAGE_DIR/LICENSE"
cp "$ROOT/tools/xiao_stm32c5/flash.sh" "$PACKAGE_DIR/flash_xiao_stm32c5.sh"
chmod +x "$PACKAGE_DIR/flash_xiao_stm32c5.sh"

if command -v sha256sum >/dev/null 2>&1; then
    (cd "$PACKAGE_DIR" && sha256sum firmware/micropython-xiao-stm32c5.uf2 tests/xiao_stm32c5_full_test.py) \
        > "$PACKAGE_DIR/firmware/SHA256SUMS.txt"
else
    (cd "$PACKAGE_DIR" && shasum -a 256 firmware/micropython-xiao-stm32c5.uf2 tests/xiao_stm32c5_full_test.py) \
        > "$PACKAGE_DIR/firmware/SHA256SUMS.txt"
fi

ARCHIVE="$OUTPUT_ROOT/$PACKAGE_NAME.tar.gz"
tar -C "$OUTPUT_ROOT" -czf "$ARCHIVE" "$PACKAGE_NAME"
echo "Package directory: $PACKAGE_DIR"
echo "Package archive:   $ARCHIVE"
