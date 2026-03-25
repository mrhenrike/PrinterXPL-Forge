#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d debian ]]; then
  echo "[deb] Missing root debian/. Run ./packages/02-deb/prepare.sh first."
  exit 1
fi

echo "[deb] Installing build dependencies (Debian/Ubuntu/Kali)..."
echo "      sudo apt install debhelper dh-python python3-all python3-setuptools"

echo "[deb] Building package..."
dpkg-buildpackage -us -uc -b

echo "[deb] Done. Artifacts are in parent directory:"
ls -lh ../*.deb 2>/dev/null || true

