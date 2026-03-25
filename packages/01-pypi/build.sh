#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "[pypi] Building wheel + sdist..."
python -m pip install --upgrade pip build twine >/dev/null
rm -rf dist build *.egg-info
python -m build

echo "[pypi] Build artifacts:"
ls -lh dist/

echo "[pypi] Validating package metadata..."
python -m twine check dist/*

echo "[pypi] Done."

