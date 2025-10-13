#!/usr/bin/env bash
#!/usr/bin/env bash
# nRF54L15 one-click flash script (Linux/macOS)
# Behavior:
#   * Auto-upgrades pyocd & intelhex unless SKIP_PYOCD_UPGRADE=1
#   * Auto-detects HEX: merged.hex > only *.hex > newest modified
#   * Always performs mass erase before programming
#   * Supports optional: --hex <file>, --probe <id>
# Usage:
#   ./flash.sh
#   ./flash.sh --probe E2DAE686
#   ./flash.sh --hex app.hex --probe E2DAE686
# Skip upgrade: SKIP_PYOCD_UPGRADE=1 ./flash.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/xiao_nrf54l15_flash.py"
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
