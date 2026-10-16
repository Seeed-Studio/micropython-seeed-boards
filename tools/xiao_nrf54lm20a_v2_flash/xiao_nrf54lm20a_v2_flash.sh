#!/usr/bin/env bash
# XIAO nRF54LM20A V2 USB DFU flasher wrapper (Linux/macOS).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/xiao_nrf54lm20a_v2_flash.py" "$@"
