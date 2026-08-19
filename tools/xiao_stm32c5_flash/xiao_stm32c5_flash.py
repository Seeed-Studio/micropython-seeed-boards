#!/usr/bin/env python3
"""XIAO STM32C5 one-click flash (TinyUF2).

Puts nothing on the board by itself -- first put the board into bootloader mode
(double-click Reset) so it exposes the XIAOC5BOOT mass-storage volume, then this
script copies micropython-xiao-stm32c5.uf2 (from this folder) onto it. TinyUF2
processes the file and reboots the board automatically.

Cross-platform: macOS, Linux, and Windows. No toolchain / pyocd / openocd /
ST-Link / J-Link required.
"""
import argparse
import os
import shutil
import sys
import time

LABEL = "XIAOC5BOOT"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_UF2 = os.path.join(HERE, "micropython-xiao-stm32c5.uf2")


def _windows_candidates():
    out = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = "%s:\\" % letter
        if os.path.isdir(root):
            out.append(root)
    return out


def candidate_volumes():
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    return [
        "/Volumes/%s" % LABEL,            # macOS
        "/media/%s/%s" % (user, LABEL),   # Linux (udev)
        "/media/%s" % LABEL,              # Linux (fallback)
        "/run/media/%s/%s" % (user, LABEL),
        "/mnt/%s" % LABEL,
    ] + _windows_candidates()             # Windows drive letters


def find_volume():
    for vol in candidate_volumes():
        # Match the TinyUF2 volume by label where possible (Windows drive label)
        if os.path.isdir(vol):
            if sys.platform.startswith("win"):
                # On Windows, confirm the drive label is XIAOC5BOOT.
                import ctypes
                buf = ctypes.create_unicode_buffer(1024)
                ok = ctypes.windll.kernel32.GetVolumeInformationW(
                    ctypes.c_wchar_p(vol), buf, 1024, None, None, None, None, 0)
                if ok and buf.value == LABEL:
                    return vol
                continue
            return vol
    return None


def main():
    ap = argparse.ArgumentParser(description="Flash XIAO STM32C5 via TinyUF2 (copy UF2 to XIAOC5BOOT).")
    ap.add_argument("--uf2", default=DEFAULT_UF2,
                    help="UF2 image to flash (default: alongside this script).")
    ap.add_argument("--volume", help="XIAOC5BOOT mount path (auto-detected if omitted).")
    args = ap.parse_args()

    if not os.path.isfile(args.uf2):
        sys.exit("[ERROR] UF2 not found: %s" % args.uf2)

    vol = args.volume or find_volume()
    if not vol:
        print("[ERROR] %s is not mounted." % LABEL)
        print("        Double-click the Reset button on the board and run again.")
        sys.exit(1)

    dst = os.path.join(vol, os.path.basename(args.uf2))
    print("[INFO] Board volume : %s" % vol)
    print("[INFO] Copying UF2  : %s -> %s" % (args.uf2, dst))
    shutil.copyfile(args.uf2, dst)
    try:
        os.sync()  # Linux/macOS -- flush to the USB MSC device
    except (AttributeError, OSError):
        pass
    # Give TinyUF2 a moment to process the file before the volume disappears.
    time.sleep(1.0)
    print("[OK] Copied. TinyUF2 reboots the board automatically; MicroPython starts shortly.")


if __name__ == "__main__":
    main()
