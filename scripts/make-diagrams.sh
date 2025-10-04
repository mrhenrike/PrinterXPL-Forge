#!/usr/bin/env bash
set -euo pipefail
OUT_DIR=${1:-diagrams/png}

echo "Generating PNG diagrams to $OUT_DIR"
mkdir -p "$OUT_DIR"

# Ensure mermaid-cli via npx
if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required (Node.js). Please install Node.js." >&2
  exit 1
fi

for f in diagrams/*.mmd; do
  base=$(basename "$f" .mmd)
  out="$OUT_DIR/$base.png"
  echo "  -> $f -> $out"
  npx -y @mermaid-js/mermaid-cli --quiet -i "$f" -o "$out"
done

echo "Done."

