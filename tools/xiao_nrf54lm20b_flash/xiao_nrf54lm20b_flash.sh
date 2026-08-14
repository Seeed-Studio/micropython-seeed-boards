#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/xiao_nrf54lm20b_flash.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
  echo "[ERROR] Missing python script: ${PY_SCRIPT}" >&2
  exit 1
fi

choose_python() {
  for exe in python3 python python3.11 python3.10; do
    command -v "$exe" >/dev/null 2>&1 && { echo "$exe"; return 0; }
  done
  echo "[ERROR] No python interpreter found" >&2
  exit 2
}

PYTHON="${PYTHON:-$(choose_python)}"
echo "+ Running: $PYTHON $PY_SCRIPT $*"
exec "$PYTHON" "$PY_SCRIPT" "$@"
