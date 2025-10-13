#!/usr/bin/env bash
# Simple wrapper to flash EFR32MG24 using the Python helper.
# Mirrors Windows flash.bat behavior but forwards any args.
# Usage examples:
#   ./flash.sh
#   ./flash.sh --hex build/firmware.hex --dry-run
# Ensure executable: chmod +x flash.sh

set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

# If python3 not found fallback to python
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  else
    echo "ERROR: python interpreter not found (python3 or python)." >&2
    exit 1
  fi
fi

exec "$PYTHON_BIN" xiao_mg24_flash.py "$@"
