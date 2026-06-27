#!/usr/bin/env bash
# setup_venv.sh — Virtual environment for PrinterXPL-Forge
# Author: André Henrique (@mrhenrike)
# Compatible with Linux, macOS, and Android (Termux)

set -euo pipefail

VENV_DIR=".venv"
PYTHON_MIN="3.8"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "=== PrinterXPL-Forge — Virtual Environment Setup ==="
echo ""

OS="$(uname -s)"
case "$OS" in
    Linux*)
        if [ -d "/data/data/com.termux" ]; then
            PLATFORM="android-termux"
        else
            PLATFORM="linux"
        fi
        ;;
    Darwin*)  PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *)        PLATFORM="unknown" ;;
esac
echo "Platform detected: $PLATFORM"

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python >= ${PYTHON_MIN}."
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python version: $PY_VER"

_venv_python() {
    [ -x "$VENV_DIR/bin/python" ] && "$VENV_DIR/bin/python" -c "import sys" 2>/dev/null
}

if [ ! -d "$VENV_DIR" ] || ! _venv_python; then
    if [ -d "$VENV_DIR" ]; then
        echo "Removing broken venv at $VENV_DIR"
        rm -rf "$VENV_DIR"
    fi
    python3 -m venv "$VENV_DIR" --prompt PrinterXPL-Forge
    echo "venv created at $VENV_DIR"
else
    echo "venv already exists at $VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip --quiet

echo ""
echo "--- Installing core dependencies ---"
"$VENV_DIR/bin/pip" install -r requirements.txt

touch "$VENV_DIR/.printerxpl-venv-ready"

echo ""
echo "=== Environment ready! ==="
echo ""
echo "Run:      ./run.sh <target> [options]"
echo "Or:       python pxf.py              # auto-detects .venv"
echo "Activate: source .venv/bin/activate"
echo "PYTHONPATH: export PYTHONPATH=src   (only if running without bootstrap)"
echo ""
