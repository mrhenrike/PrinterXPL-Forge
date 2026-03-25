#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DEBIAN_DIR="$ROOT_DIR/packages/02-deb/debian"
DST_DEBIAN_DIR="$ROOT_DIR/debian"
SRC_MAN="$ROOT_DIR/packages/man/printer-reaper.1"
DST_MAN_DIR="$ROOT_DIR/man/man1"

echo "[deb] Syncing Debian templates to repository root..."
rm -rf "$DST_DEBIAN_DIR"
mkdir -p "$DST_DEBIAN_DIR"
cp -a "$SRC_DEBIAN_DIR"/. "$DST_DEBIAN_DIR"/

mkdir -p "$DST_MAN_DIR"
cp -f "$SRC_MAN" "$DST_MAN_DIR/printer-reaper.1"
chmod +x "$DST_DEBIAN_DIR/rules"

echo "[deb] Ready: $DST_DEBIAN_DIR"

