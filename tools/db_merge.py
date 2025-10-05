#!/usr/bin/env python3
"""
Merge PRET model databases into PrinterReaper's model db with normalization.

Usage:
  python tools/db_merge.py --pret deleted/PRET/db/pjl.dat --out src/core/db/pjl.dat
"""
import argparse
import re
from pathlib import Path


def normalize_model(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def load_models(path: Path) -> set[str]:
    models = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Skip obviously too-short/ambiguous entries
        if len(line) < 3:
            continue
        models.add(normalize_model(line))
    return models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pret", required=True, help="Path to PRET pjl.dat")
    ap.add_argument("--out", required=True, help="Path to output pjl.dat")
    args = ap.parse_args()

    pret = Path(args.pret)
    out = Path(args.out)

    base_models = set()
    if out.exists():
        base_models = load_models(out)
    pret_models = load_models(pret)

    merged = sorted(base_models.union(pret_models))
    out.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"Merged {len(pret_models)} PRET models with {len(base_models)} base models → {len(merged)} total")


if __name__ == "__main__":
    main()


