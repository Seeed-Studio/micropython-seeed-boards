#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB DFU flashing helper for Seeed XIAO nRF54LM20B.

Flashes a signed MCUboot application image over USB with `nrfutil mcumgr`.
No SWD / J-Link / debug probe is required: the board enters the MCUboot USB
serial-recovery loader when you HOLD the USER button and press RESET.

How it works
------------
1. Build / obtain a signed MCUboot app image (zephyr.signed.bin) -- the
   bootloader and KMU public key are factory-flashed, so only the app is
   updated over USB.
2. Put the board into DFU mode: hold USER, press RESET, release USER.
   It enumerates as a USB CDC ACM device with VID:PID 2886:0013
   (the application itself uses 2886:8013).
3. This script auto-detects that loader port and uploads the image.

Prerequisites
-------------
  pip install nrfutil        # provides `nrfutil mcumgr` (bundles pyserial)

Usage
-----
  python xiao_nrf54lm20b_flash.py [<signed-image.bin>] [--port PORT] [--mtu N]

If no image is given, the script picks the lone *.bin in the current dir.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

# mcuboot USB CDC ACM loader identity (app CDC is 2886:8013).
LOADER_VID = 0x2886
LOADER_PID = 0x0013
BAUD = 115200
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def auto_select_firmware():
    """Pick the firmware image: explicit arg > cwd *.bin (prefer *signed.bin)."""
    bins = [f for f in glob.glob(os.path.join(os.getcwd(), "*.bin"))]
    prefer = [f for f in bins if os.path.basename(f).lower().endswith("signed.bin")]
    candidates = prefer or bins
    if len(candidates) == 1:
        print(f"[INFO] Auto-selected image: {candidates[0]}")
        return candidates[0]
    if not candidates:
        print("[ERROR] No signed image (.bin) found. Pass the path explicitly.")
    else:
        print("[ERROR] Multiple .bin files found; pass the one to flash explicitly:")
        for f in candidates:
            print(f"        {f}")
    return None


def find_loader_port():
    """Return (port_device, error_or_None). VID:PID match = loader."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return None, "pyserial not installed (run: pip install nrfutil)"
    for p in list_ports.comports():
        if p.vid == LOADER_VID and p.pid == LOADER_PID:
            return p.device, None
    return None, None


def wait_for_loader(timeout=60):
    print("\n>> Enter DFU mode: HOLD the USER button, press RESET, then release USER.")
    print(f">> Looking for loader USB CDC ({LOADER_VID:04x}:{LOADER_PID:04x}) ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        port, err = find_loader_port()
        if port:
            print(f"[OK] Loader found on {port}")
            return port
        if err:
            print(f"[ERROR] {err}")
            return None
        time.sleep(0.5)
    print("[ERROR] Timed out waiting for the loader. "
          "Make sure you held USER while pressing RESET.")
    return None


def run(cmd):
    print("+ " + " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    ap = argparse.ArgumentParser(
        description="XIAO nRF54LM20B USB DFU flasher (nrfutil mcumgr).")
    ap.add_argument("firmware", nargs="?", help="signed MCUboot app image (.bin)")
    ap.add_argument("--port", help="loader serial port (skip auto-detect)")
    ap.add_argument("--mtu", type=int, help="SMP MTU (try 128 if the upload stalls)")
    ap.add_argument("--no-wait", action="store_true",
                    help="don't wait for button+reset; detect once and fail if absent")
    args = ap.parse_args()

    firmware = args.firmware or auto_select_firmware()
    if not firmware:
        return 1
    if not os.path.isfile(firmware):
        print(f"[ERROR] Not found: {firmware}")
        return 1

    tool = shutil.which("nrfutil")
    if not tool:
        print("[ERROR] nrfutil not found on PATH. Install: pip install nrfutil")
        return 1

    port = args.port
    if not port:
        port = wait_for_loader(timeout=0 if args.no_wait else 60)
    if not port:
        return 1

    conn = "{},baud={}".format(port, BAUD)
    if args.mtu:
        conn += ",mtu={}".format(args.mtu)

    run([tool, "mcumgr", "--conntype", "serial",
         "--connstring", conn, "image", "upload", firmware])
    print("\n[DONE] Upload complete. Press RESET to boot the new application.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
