#!/usr/bin/env python3
"""
Utility script to flash EFR32MG24 (Seeed XIAO MG24) using pyOCD.

Features:
- Auto-detect a single .hex file in current directory (unless --hex provided).
- Ensure pyocd is installed (auto-install if missing unless --no-install specified).
- Allow overriding target, pack path, hex path.
- Dry-run option to show the command without executing.
- Clear error messages and non-zero exit codes on failure.

Default target: efr32mg24b220f1536im48
Default pack:   ./SiliconLabs.GeckoPlatform_EFR32MG24_DFP.2025.6.0.pack

Windows PowerShell friendly; works cross-platform.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import shutil
import os
from pathlib import Path

def which(exe: str) -> str | None:
    return shutil.which(exe)

def run(cmd: list[str], check: bool = True) -> int:
    print(f"[cmd] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"ERROR: command failed with exit code {e.returncode}")
        return e.returncode

def ensure_pyocd(auto_install: bool = True) -> None:
    if which("pyocd"):
        return
    if not auto_install:
        print("ERROR: pyocd not found and auto-install disabled (--no-install).", file=sys.stderr)
        sys.exit(2)
    print("pyocd not found. Installing pyocd...")
    # Use current interpreter's pip
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pyocd"]
    rc = run(cmd, check=False)
    if rc != 0 or not which("pyocd"):
        print("ERROR: Failed to install pyocd.", file=sys.stderr)
        sys.exit(3)

def find_single_hex(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            print(f"ERROR: Provided hex file '{p}' not found.", file=sys.stderr)
            sys.exit(4)
        return p
    hex_files = [p for p in Path.cwd().glob("*.hex") if p.is_file()]
    if not hex_files:
        print("ERROR: No .hex file found in current directory. Provide one with --hex.", file=sys.stderr)
        sys.exit(5)
    if len(hex_files) > 1:
        names = ', '.join(f.name for f in hex_files)
        print(f"ERROR: Multiple .hex files found ({names}). Use --hex to specify one.", file=sys.stderr)
        sys.exit(6)
    return hex_files[0]

def build_command(target: str, pack: Path, hex_file: Path) -> list[str]:
    return [
        "pyocd", "flash",
        "--target", target,
        str(hex_file),
        "--pack", str(pack)
    ]

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Flash EFR32MG24 via pyOCD")
    parser.add_argument("--hex", help="Path to hex file (if omitted auto-detect single .hex in CWD)")
    parser.add_argument("--target", default="efr32mg24b220f1536im48", help="pyOCD target name (default: %(default)s)")
    parser.add_argument("--pack", default="./SiliconLabs.GeckoPlatform_EFR32MG24_DFP.2025.6.0.pack", help="Path to DFP .pack file")
    parser.add_argument("--dry-run", action="store_true", help="Only print the pyocd command without executing")
    parser.add_argument("--no-install", action="store_true", help="Do not auto-install pyocd if missing")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")

    args = parser.parse_args(argv)

    hex_file = find_single_hex(args.hex)
    pack_path = Path(args.pack)
    if not pack_path.is_file():
        print(f"ERROR: Pack file '{pack_path}' not found.", file=sys.stderr)
        return 7

    ensure_pyocd(auto_install=not args.no_install)

    cmd = build_command(args.target, pack_path, hex_file)

    if args.dry_run:
        print("Dry-run: would execute:")
        print(' '.join(cmd))
        return 0

    rc = run(cmd, check=False)
    if rc == 0:
        print(f"SUCCESS: Flashed '{hex_file.name}' to target '{args.target}'.")
    return rc

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
