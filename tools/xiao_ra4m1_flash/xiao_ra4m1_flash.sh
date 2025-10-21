#!/usr/bin/env bash
# Cross-platform (Linux/macOS) flashing script for Seeed XIAO RA4M1 using pyOCD.
# Mirrors functionality of xiao_ra4m1_flash.py with simpler bash implementation.
#
# Features:
#  - Auto-detect single .hex file in current working directory if --hex not provided.
#  - Default target: R7FA4M1AB
#  - Default pack:   ./Renesas.RA_DFP.6.1.0.pack (relative to CWD or script dir fallback)
#  - Optional skip erase: --no-erase (erase is done via: pyocd erase --chip)
#  - Dry run: --dry-run prints commands only.
#  - Auto-install pyocd unless --no-install specified.
#  - Clear error codes and messages.
#
# Exit codes:
#   2: pyocd missing and auto-install disabled
#   3: pyocd installation failed
#   4: specified hex not found
#   5: no hex found for auto-detect
#   6: multiple hex files found
#   7: pack file missing
#
# Usage examples:
#   bash flash.sh
#   bash flash.sh --hex build/firmware.hex
#   bash flash.sh --no-erase
#   bash flash.sh --dry-run
#   bash flash.sh --pack /path/to/Renesas.RA_DFP.6.1.0.pack
#
set -euo pipefail

TARGET="R7FA4M1AB"
PACK="./Renesas.RA_DFP.6.1.0.pack"
HEX=""
DO_ERASE=1
DRY_RUN=0
AUTO_INSTALL=1

# Detect OS (macOS vs Linux) just for informational prints.
UNAME=$(uname -s || echo unknown)

print_help() {
  sed -n '1,/^set -euo pipefail/p' "$0" | sed 's/^# //; s/^#//' | grep -v "!/" || true
  cat <<EOF
Options:
  --hex <file>       Specify .hex file (auto-detect if omitted)
  --target <name>    pyOCD target name (default: $TARGET)
  --pack <file>      Path to DFP .pack file (default: $PACK)
  --no-erase         Skip chip erase step
  --dry-run          Show commands without executing
  --no-install       Do not attempt to install pyocd automatically
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hex)
      HEX="$2"; shift 2;;
    --target)
      TARGET="$2"; shift 2;;
    --pack)
      PACK="$2"; shift 2;;
    --no-erase)
      DO_ERASE=0; shift;;
    --dry-run)
      DRY_RUN=1; shift;;
    --no-install)
      AUTO_INSTALL=0; shift;;
    -h|--help)
      print_help; exit 0;;
    *)
      echo "Unknown argument: $1" >&2; print_help; exit 1;;
  esac
done

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# If PACK not found in CWD, try script_dir fallback
if [[ ! -f "$PACK" ]]; then
  if [[ -f "$script_dir/$(basename "$PACK")" ]]; then
    PACK="$script_dir/$(basename "$PACK")"
  fi
fi

ensure_pyocd() {
  if command -v pyocd >/dev/null 2>&1; then
    return 0
  fi
  if [[ $AUTO_INSTALL -eq 0 ]]; then
    echo "ERROR: pyocd not found and auto-install disabled (--no-install)." >&2
    exit 2
  fi
  echo "pyocd not found. Installing pyocd..."
  if ! python3 -m pip install --upgrade pyocd; then
    echo "ERROR: Failed to install pyocd." >&2
    exit 3
  fi
  if ! command -v pyocd >/dev/null 2>&1; then
    echo "ERROR: pyocd still not found after install." >&2
    exit 3
  fi
}

find_hex() {
  if [[ -n "$HEX" ]]; then
    if [[ ! -f "$HEX" ]]; then
      echo "ERROR: Provided hex file '$HEX' not found." >&2
      exit 4
    fi
    return 0
  fi
  mapfile -t hex_files < <(find . -maxdepth 1 -type f -name '*.hex' -printf '%f\n' 2>/dev/null || ls *.hex 2>/dev/null || true)
  if [[ ${#hex_files[@]} -eq 0 ]]; then
    echo "ERROR: No .hex file found in current directory. Provide one with --hex." >&2
    exit 5
  fi
  if [[ ${#hex_files[@]} -gt 1 ]]; then
    echo "ERROR: Multiple .hex files found (${hex_files[*]}). Use --hex to specify one." >&2
    exit 6
  fi
  HEX="${hex_files[0]}"
}

find_hex

if [[ ! -f "$PACK" ]]; then
  echo "ERROR: Pack file '$PACK' not found." >&2
  exit 7
fi

ensure_pyocd

erase_cmd=(pyocd erase --target "$TARGET" --pack "$PACK" --chip)
flash_cmd=(pyocd flash --target "$TARGET" "$HEX" --pack "$PACK")

echo "[info] OS: $UNAME"
echo "[info] Target: $TARGET"
echo "[info] Pack: $PACK"
echo "[info] Hex: $HEX"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Dry-run: would execute (in order):"
  if [[ $DO_ERASE -eq 1 ]]; then
    echo "${erase_cmd[*]}"
  fi
  echo "${flash_cmd[*]}"
  exit 0
fi

run_cmd() {
  echo "[cmd] $*"
  if ! "$@"; then
    echo "ERROR: Command failed: $*" >&2
    exit 8
  fi
}

if [[ $DO_ERASE -eq 1 ]]; then
  run_cmd "${erase_cmd[@]}"
fi
run_cmd "${flash_cmd[@]}"

echo "SUCCESS: Flashed '$HEX' to target '$TARGET'."
