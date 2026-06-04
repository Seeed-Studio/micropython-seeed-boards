#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flashing helper for Seeed XIAO nRF54LM20A.

Default path: OpenOCD over CMSIS-DAP, aligned with platform-seeedboards default uploader.
Fallback path: pyOCD (optional, for debugging only).
"""

import argparse
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_OPENOCD_CFG = os.path.join(SCRIPT_DIR, "openocd.cfg")
REPO_OPENOCD_CFG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))),
    "boards",
    "seeed",
    "xiao_nrf54lm20a",
    "support",
    "openocd.cfg",
)

PYOCD_SPEC = "pyocd @ git+https://github.com/StarSphere-1024/pyOCD.git@lm20_stable"
TARGET = "nrf54lm20a"
FREQUENCY = "4000000"


def auto_select_hex() -> str:
    cwd = os.getcwd()
    merged_path = os.path.join(cwd, "merged.hex")
    if os.path.isfile(merged_path):
        print(f"[INFO] Auto-selected HEX: {merged_path} (found merged.hex)")
        return merged_path

    hex_files = [f for f in os.listdir(cwd) if f.lower().endswith(".hex")]
    if not hex_files:
        print("[ERROR] No HEX file found in current directory.")
        sys.exit(1)
    if len(hex_files) == 1:
        candidate = os.path.join(cwd, hex_files[0])
        print(f"[INFO] Auto-selected HEX: {candidate} (only hex file)")
        return candidate

    hex_files_full = [os.path.join(cwd, f) for f in hex_files]
    hex_files_full.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    candidate = hex_files_full[0]
    print(f"[INFO] Auto-selected HEX: {candidate} (most recently modified)")
    return candidate


def find_openocd() -> str:
    candidates = [
        shutil.which("openocd"),
        r"C:\Users\seeed\AppData\Local\xPacks\OpenOCD\xpack-openocd-0.12.0-7\bin\openocd.exe",
        r"C:\ProgramData\chocolatey\bin\openocd.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    print("[ERROR] openocd executable not found.")
    sys.exit(1)


def find_openocd_cfg() -> str:
    for candidate in (LOCAL_OPENOCD_CFG, REPO_OPENOCD_CFG):
        if os.path.isfile(candidate):
            return candidate
    print("[ERROR] openocd.cfg not found. Expected one of:")
    print(f"  - {LOCAL_OPENOCD_CFG}")
    print(f"  - {REPO_OPENOCD_CFG}")
    sys.exit(1)


def ensure_expected_pyocd() -> None:
    if os.environ.get("SKIP_PYOCD_UPGRADE") == "1":
        print("[INFO] SKIP_PYOCD_UPGRADE=1 set; skipping pyOCD compatibility check.")
        return

    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "pyocd", "list", "--targets"],
            stderr=subprocess.STDOUT,
            text=True,
        )
        if TARGET in output.lower():
            print(f"[INFO] Detected pyOCD target support for {TARGET}.")
            return
    except Exception:
        pass

    print(f"[INFO] Installing pyOCD fork with {TARGET} support ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", PYOCD_SPEC, "libusb"], check=True)


def flash_with_openocd(hex_path: str, probe_id: str | None) -> int:
    openocd = find_openocd()
    openocd_cfg = find_openocd_cfg()
    cmd = [openocd]

    if probe_id:
        cmd.extend(["-c", f"cmsis_dap_serial {probe_id}"])

    cmd.extend(
        [
            "-f",
            openocd_cfg,
            "-c",
            "init",
            "-c",
            "nrf54l_mass_erase",
            "-c",
            f"nrf54lm20a-load {{{hex_path}}}",
            "-c",
            f"verify_image {{{hex_path}}}",
            "-c",
            "reset run",
            "-c",
            "shutdown",
        ]
    )

    print("[INFO] Running:", " ".join(cmd))
    return subprocess.run(cmd).returncode


def flash_with_pyocd(hex_path: str, probe_id: str | None) -> int:
    ensure_expected_pyocd()
    cmd = [
        sys.executable,
        "-m",
        "pyocd",
        "flash",
    ]
    if probe_id:
        cmd.extend(["--probe", probe_id])
    cmd.extend(
        [
            "--target",
            TARGET,
            "--frequency",
            FREQUENCY,
            hex_path,
        ]
    )
    print("[INFO] Running:", " ".join(cmd))
    return subprocess.run(cmd).returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Flash Seeed XIAO nRF54LM20A firmware.")
    parser.add_argument("--hex", help="Path to the HEX file to be programmed.")
    parser.add_argument("--probe", help="Specify the unique ID of the debug probe to use.")
    parser.add_argument(
        "--backend",
        choices=["openocd", "pyocd"],
        default="openocd",
        help="Flashing backend. Default uses OpenOCD to match platform-seeedboards.",
    )
    args = parser.parse_args()

    hex_path = args.hex or auto_select_hex()
    print(f"[INFO] Using HEX file: {hex_path}")

    if args.backend == "openocd":
        rc = flash_with_openocd(hex_path, args.probe)
    else:
        rc = flash_with_pyocd(hex_path, args.probe)
    if rc == 0:
        print("[INFO] Flash and verify completed successfully.")
    sys.exit(rc)


if __name__ == "__main__":
    main()
