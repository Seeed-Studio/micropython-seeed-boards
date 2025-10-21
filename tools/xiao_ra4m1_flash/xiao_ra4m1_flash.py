#!/usr/bin/env python3
"""
Utility script to erase and flash Renesas RA4M1 (Seeed XIAO RA4M1) using pyOCD.

Features:
- Auto-detect a single .hex file in current directory (unless --hex provided).
- Ensure pyocd is installed (auto-install if missing unless --no-install specified).
- Allow overriding target, pack path, hex path.
- Optional chip erase (enabled by default, disable with --no-erase).
- Dry-run option to show the commands without executing.
- Clear error messages and non-zero exit codes on failure.

Default target: R7FA4M1AB
Default pack:   ./Renesas.RA_DFP.6.1.0.pack

Cross-platform (Windows PowerShell friendly) and minimal dependencies.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
import shutil
from pathlib import Path

# Exit codes (distinct for easier CI parsing)
E_NO_HEX = 5
E_MULTI_HEX = 6
E_PACK_MISSING = 7
E_PYOCD_INSTALL = 3
E_PYOCD_DISABLED = 2
E_HEX_NOT_FOUND = 4


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
        sys.exit(E_PYOCD_DISABLED)
    print("pyocd not found. Installing pyocd...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pyocd"]
    rc = run(cmd, check=False)
    if rc != 0 or not which("pyocd"):
        print("ERROR: Failed to install pyocd.", file=sys.stderr)
        sys.exit(E_PYOCD_INSTALL)


def find_single_hex(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            print(f"ERROR: Provided hex file '{p}' not found.", file=sys.stderr)
            sys.exit(E_HEX_NOT_FOUND)
        return p
    hex_files = [p for p in Path.cwd().glob("*.hex") if p.is_file()]
    if not hex_files:
        print("ERROR: No .hex file found in current directory. Provide one with --hex.", file=sys.stderr)
        sys.exit(E_NO_HEX)
    if len(hex_files) > 1:
        names = ', '.join(f.name for f in hex_files)
        print(f"ERROR: Multiple .hex files found ({names}). Use --hex to specify one.", file=sys.stderr)
        sys.exit(E_MULTI_HEX)
    return hex_files[0]


def build_erase_command(target: str, pack: Path) -> list[str]:
    return [
        "pyocd", "erase",
        "--target", target,
        "--pack", str(pack),
        "--chip"
    ]


def build_flash_command(target: str, pack: Path, hex_file: Path) -> list[str]:
    return [
        "pyocd", "flash",
        "--target", target,
        str(hex_file),
        "--pack", str(pack)
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Erase + Flash RA4M1 via pyOCD")
    parser.add_argument("--hex", help="Path to hex file (if omitted auto-detect single .hex in CWD)")
    parser.add_argument("--target", default="R7FA4M1AB", help="pyOCD target name (default: %(default)s)")
    parser.add_argument("--pack", default="./Renesas.RA_DFP.6.1.0.pack", help="Path to DFP .pack file")
    parser.add_argument("--dry-run", action="store_true", help="Only print the pyocd commands without executing")
    parser.add_argument("--no-install", action="store_true", help="Do not auto-install pyocd if missing")
    parser.add_argument("--no-erase", action="store_true", help="Skip chip erase step before flashing")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors (placeholder; colors not currently used)")

    args = parser.parse_args(argv)

    hex_file = find_single_hex(args.hex)
    pack_path = Path(args.pack)
    if not pack_path.is_file():
        print(f"ERROR: Pack file '{pack_path}' not found.", file=sys.stderr)
        return E_PACK_MISSING

    ensure_pyocd(auto_install=not args.no_install)

    erase_cmd = build_erase_command(args.target, pack_path)
    flash_cmd = build_flash_command(args.target, pack_path, hex_file)

    if args.dry_run:
        print("Dry-run: would execute (in order):")
        if not args.no_erase:
            print(' '.join(erase_cmd))
        print(' '.join(flash_cmd))
        return 0

    if not args.no_erase:
        rc = run(erase_cmd, check=False)
        if rc != 0:
            print("ERROR: Erase failed; aborting flash.", file=sys.stderr)
            return rc

    rc = run(flash_cmd, check=False)
    if rc == 0:
        print(f"SUCCESS: Flashed '{hex_file.name}' to target '{args.target}'.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
