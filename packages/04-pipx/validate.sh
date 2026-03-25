#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v pipx >/dev/null 2>&1; then
  echo "[pipx] pipx not found. Install with: python -m pip install --user pipx"
  exit 1
fi

echo "[pipx] Installing local editable package..."
pipx install --force --editable .

echo "[pipx] Command check..."
printer-reaper --version
printer-reaper --help >/dev/null

echo "[pipx] OK"

