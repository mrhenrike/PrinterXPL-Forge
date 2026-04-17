#!/usr/bin/env bash
# PrinterXPL-Forge — launcher with local venv (Linux/macOS)
# Usage: ./run.sh <ip> --scan
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "[!] Venv not found. Creating..."
    python3 -m venv "$VENV" --prompt PrinterXPL-Forge
    "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/src/main.py" "$@"
