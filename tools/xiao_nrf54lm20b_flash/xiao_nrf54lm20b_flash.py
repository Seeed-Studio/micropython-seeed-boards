#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB DFU flashing helper for Seeed XIAO nRF54LM20B (cross-platform).

Uploads a signed MCUboot app image over USB with `nrfutil mcu-manager`.
No SWD / J-Link / debug probe is required: the board enters the MCUboot USB
serial-recovery loader when you HOLD the USER button and press RESET; it then
enumerates as a USB CDC ACM device with VID:PID 2886:0013 (the application
itself uses 2886:8013).

nrfutil resolution (in order):
  1. a portable nrfutil.exe shipped alongside this script (release package),
  2. nrfutil on PATH (must have the `mcu-manager` plugin:
       `nrfutil install mcu-manager`).

Usage:
  python xiao_nrf54lm20b_flash.py [<signed.bin>] [--port PORT] [--mtu N]
"""

import argparse
import glob
import os
import subprocess
import sys
import time
from shutil import which

LOADER_VID = 0x2886
LOADER_PID = 0x0013   # mcuboot USB CDC ACM loader (app CDC is 2886:8013)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def auto_select_firmware():
    """Pick the firmware image: explicit arg > *.bin in cwd / sibling firmware/."""
    fw_dirs = [os.getcwd(), os.path.join(SCRIPT_DIR, "..", "firmware")]
    bins = []
    for d in fw_dirs:
        bins += glob.glob(os.path.join(d, "*.bin"))
    prefer = [f for f in bins if os.path.basename(f).lower().endswith("signed.bin")]
    candidates = prefer or bins
    if len(candidates) == 1:
        print("[INFO] Auto-selected image: %s" % candidates[0])
        return candidates[0]
    if not candidates:
        print("[ERROR] No signed image (.bin) found. Pass the path explicitly.")
    else:
        print("[ERROR] Multiple .bin files found; pass the one to flash explicitly:")
        for f in candidates:
            print("        %s" % f)
    return None


def find_loader_port():
    """Return (port_device, error_or_None). VID:PID match = loader."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return None, "pyserial not installed (pip install pyserial), or use --port"
    for p in list_ports.comports():
        if p.vid == LOADER_VID and p.pid == LOADER_PID:
            return p.device, None
    return None, None


def wait_for_loader(timeout=60):
    print("\n>> Enter DFU mode: HOLD the USER button, press RESET, then release USER.")
    print(">> Looking for loader USB CDC (%04x:%04x) ..." % (LOADER_VID, LOADER_PID))
    deadline = time.time() + timeout
    while time.time() < deadline:
        port, err = find_loader_port()
        if port:
            print("[OK] Loader found on %s" % port)
            return port
        if err:
            print("[ERROR] %s" % err)
            return None
        time.sleep(0.7)
    print("[ERROR] Timed out waiting for the loader. "
          "Make sure you held USER while pressing RESET.")
    return None


def resolve_nrfutil():
    """Prefer a portable nrfutil shipped alongside; fall back to PATH.

    Returns (exe, home_dir_or_None). home_dir is set when a bundled nrfutil
    with its own plugin home is used (NRFUTIL_HOME)."""
    candidates = [
        os.path.join(SCRIPT_DIR, "..", "tools", "nrfutil", "nrfutil.exe"),  # release pkg
        os.path.join(SCRIPT_DIR, "..", "nrfutil", "nrfutil.exe"),            # sibling dir
        os.path.join(SCRIPT_DIR, "nrfutil.exe"),                             # next to script
    ]
    for c in candidates:
        if os.path.isfile(c):
            exe = os.path.abspath(c)
            home = os.path.join(os.path.dirname(exe), "home")
            return exe, (home if os.path.isdir(home) else None)
    exe = which("nrfutil")
    return (exe, None) if exe else (None, None)


def run(cmd, env=None):
    print("+ " + " ".join('"%s"' % c if " " in c else c for c in cmd))
    subprocess.check_call(cmd, env=env)


def main():
    ap = argparse.ArgumentParser(
        description="XIAO nRF54LM20B USB DFU flasher (nrfutil mcu-manager).")
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
        print("[ERROR] Not found: %s" % firmware)
        return 1

    tool, home = resolve_nrfutil()
    if not tool:
        print("[ERROR] nrfutil not found. Install nrfutil + the mcu-manager plugin:")
        print("          nrfutil install mcu-manager")
        print("        or use a release package that bundles nrfutil.")
        return 1
    env = dict(os.environ)
    if home:
        env["NRFUTIL_HOME"] = home
    print("[INFO] nrfutil: %s%s" % (tool, ("  (NRFUTIL_HOME=%s)" % home) if home else ""))

    port = args.port
    if not port:
        port = wait_for_loader(timeout=0 if args.no_wait else 60)
    if not port:
        return 1

    upload = [tool, "mcu-manager", "serial", "image-upload",
              "--serial-port", port, "--timeout", "60", "--firmware", firmware]
    if args.mtu:
        upload += ["--mtu", str(args.mtu)]
    run(upload, env=env)

    try:
        run([tool, "mcu-manager", "serial", "reset", "--serial-port", port, "--timeout", "60"], env=env)
    except subprocess.CalledProcessError:
        print("[WARN] Upload finished, but reset did not complete. Press RESET manually.")

    print("\n[DONE] Upload complete. The board should boot the new application.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
