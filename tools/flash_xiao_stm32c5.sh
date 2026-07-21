#!/usr/bin/env sh
# Copy a UF2 to an already-mounted XIAO STM32C5 TinyUF2 volume.

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -gt 0 ]; then
    UF2=$1
elif [ -f "$SCRIPT_DIR/firmware/micropython-xiao-stm32c5.uf2" ]; then
    UF2="$SCRIPT_DIR/firmware/micropython-xiao-stm32c5.uf2"
else
    UF2="$SCRIPT_DIR/../dist/xiao-stm32c5-micropython-dev/firmware/micropython-xiao-stm32c5.uf2"
fi
LABEL=XIAOC5BOOT

if [ ! -f "$UF2" ]; then
    echo "error: UF2 file not found: $UF2" >&2
    exit 2
fi

MOUNT=
for candidate in \
    "/Volumes/$LABEL" \
    "/media/${USER:-unknown}/$LABEL" \
    "/run/media/${USER:-unknown}/$LABEL" \
    "/mnt/$LABEL"; do
    if [ -d "$candidate" ]; then
        MOUNT=$candidate
        break
    fi
done

if [ -z "$MOUNT" ]; then
    echo "error: $LABEL is not mounted; double-click Reset and try again" >&2
    exit 1
fi

cp "$UF2" "$MOUNT/"
sync
echo "Copied $UF2 to $MOUNT; TinyUF2 should reboot the board automatically."
