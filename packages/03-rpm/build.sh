#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SPEC_SRC="$ROOT_DIR/packages/03-rpm/printerxpl-forge.spec"
VERSION="$(python -c "import sys; sys.path.insert(0,'$ROOT_DIR/src'); import version; print(version.__version__)")"

echo "[rpm] Version detected: $VERSION"

rpmdev-setuptree >/dev/null 2>&1 || true
cp -f "$SPEC_SRC" "$HOME/rpmbuild/SPECS/printerxpl-forge.spec"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ARCHIVE="$HOME/rpmbuild/SOURCES/printerxpl-forge-$VERSION.tar.gz"
echo "[rpm] Creating source tarball: $ARCHIVE"

git -C "$ROOT_DIR" archive --format=tar.gz \
  --prefix="PrinterXPL-Forge-$VERSION/" \
  HEAD > "$ARCHIVE"

echo "[rpm] Building package..."
rpmbuild -ba "$HOME/rpmbuild/SPECS/printerxpl-forge.spec" \
  --define "version_override $VERSION"

echo "[rpm] Done. Outputs:"
ls -lh "$HOME/rpmbuild/RPMS/noarch/"printerxpl-forge-"$VERSION"* || true
ls -lh "$HOME/rpmbuild/SRPMS/"printerxpl-forge-"$VERSION"* || true

