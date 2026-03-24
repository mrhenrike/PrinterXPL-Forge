#!/usr/bin/env bash
# PrinterReaper — launcher with local venv (Linux/macOS)
# Usage: ./run.sh <ip> --scan
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "[!] Venv not found. Creating..."
    python3 -m venv "$VENV" --prompt PrinterReaper
    "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/src/main.py" "$@"
