#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/xiao_nrf54lm20b_flash.py"
for exe in python3 python; do
  if command -v "$exe" >/dev/null 2>&1; then
    exec "$exe" "$PY_SCRIPT" "$@"
  fi
done
echo "[ERROR] No Python interpreter found" >&2
exit 2
