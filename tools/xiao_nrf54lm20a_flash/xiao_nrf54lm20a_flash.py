#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flashing helper for Seeed XIAO nRF54LM20A.

Default path: OpenOCD over CMSIS-DAP, aligned with platform-seeedboards default uploader.
Fallback path: pyOCD (optional, for debugging only).
"""

import argparse
import json
import os
import platform
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
PIO_OPENOCD_SPEC = "tool-openocd@~3.1200.0"
PIO_OPENOCD_VERSION = "3.1200.0"
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


def parse_version(version: str) -> tuple:
    parts = []
    for token in version.replace("-", ".").split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(token)
    return tuple(parts)


def default_openocd_root() -> str:
    system = platform.system().lower()
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, "Seeed", "OpenOCD")
    if system == "darwin":
        return os.path.expanduser("~/Library/Application Support/Seeed/OpenOCD")
    return os.path.expanduser("~/.local/share/seeed/openocd")


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def prompt_openocd_root(user_value: str | None) -> str:
    if user_value:
        return ensure_dir(os.path.abspath(os.path.expanduser(user_value)))

    default_root = ensure_dir(default_openocd_root())
    package_dir = os.path.join(default_root, "tool-openocd")
    if os.path.isdir(package_dir):
        return default_root

    print(f"[INFO] Verified OpenOCD install dir default: {default_root}")
    if sys.stdin and sys.stdin.isatty():
        entered = input("OpenOCD install dir (press Enter to use default): ").strip()
        if entered:
            return ensure_dir(os.path.abspath(os.path.expanduser(entered)))
    return default_root


def ensure_pio() -> str:
    pio = shutil.which("pio")
    if pio:
        return pio
    print("[INFO] PlatformIO not found. Installing platformio ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "platformio"], check=True)
    pio = shutil.which("pio")
    if not pio:
        print("[ERROR] Failed to locate PlatformIO after installation.")
        sys.exit(1)
    return pio


def install_verified_openocd(storage_dir: str) -> None:
    pio = ensure_pio()
    print(f"[INFO] Installing verified OpenOCD {PIO_OPENOCD_VERSION} into: {storage_dir}")
    subprocess.run(
        [pio, "pkg", "install", "-g", "-t", PIO_OPENOCD_SPEC, "--storage-dir", storage_dir, "--force"],
        check=True,
    )


def find_managed_openocd_root(storage_dir: str) -> str | None:
    candidates = []
    for entry in os.scandir(storage_dir):
        if not entry.is_dir():
            continue
        package_json = os.path.join(entry.path, "package.json")
        if not os.path.isfile(package_json):
            continue
        try:
            with open(package_json, "r", encoding="utf-8") as fp:
                meta = json.load(fp)
        except Exception:
            continue
        if meta.get("name") != "tool-openocd":
            continue
        candidates.append((parse_version(meta.get("version", "0")), entry.path, meta))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def ensure_verified_openocd(storage_dir: str) -> str:
    managed = find_managed_openocd_root(storage_dir)
    if managed:
        package_json = os.path.join(managed, "package.json")
        with open(package_json, "r", encoding="utf-8") as fp:
            meta = json.load(fp)
        if meta.get("version") == PIO_OPENOCD_VERSION:
            return managed

    install_verified_openocd(storage_dir)
    managed = find_managed_openocd_root(storage_dir)
    if not managed:
        print("[ERROR] Verified OpenOCD installation completed but package was not found.")
        sys.exit(1)
    return managed


def find_openocd(openocd_root: str) -> str:
    managed_root = ensure_verified_openocd(openocd_root)
    exe_name = "openocd.exe" if platform.system().lower() == "windows" else "openocd"
    candidate = os.path.join(managed_root, "bin", exe_name)
    if os.path.isfile(candidate):
        return candidate
    print("[ERROR] openocd executable not found in verified package:")
    print(f"  - {candidate}")
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


def flash_with_openocd(hex_path: str, probe_id: str | None, openocd_root: str) -> int:
    openocd = find_openocd(openocd_root)
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
    parser.add_argument("--openocd-dir", help="Directory used to install and manage the verified OpenOCD package.")
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
        openocd_root = prompt_openocd_root(args.openocd_dir)
        rc = flash_with_openocd(hex_path, args.probe, openocd_root)
    else:
        rc = flash_with_pyocd(hex_path, args.probe)
    if rc == 0:
        print("[INFO] Flash and verify completed successfully.")
    sys.exit(rc)


if __name__ == "__main__":
    main()
