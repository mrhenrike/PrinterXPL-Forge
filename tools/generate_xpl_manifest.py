#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_xpl_manifest.py — PrinterXPL-Forge manifest regenerator.

Rebuilds src/data/xpl_manifest.json from the exploits currently on disk.
Called automatically by `pxf --xpl-update` and usable standalone:

    python tools/generate_xpl_manifest.py [--output PATH] [--dry-run]

Author: Andre Henrique (@mrhenrike) | Uniao Geek
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

# ── Resolve project root ───────────────────────────────────────────────────────
_TOOLS_DIR = Path(__file__).resolve().parent
_ROOT      = _TOOLS_DIR.parent
_SRC_DIR   = _ROOT / "src"

# Inject src/ so we can import from the project without installation
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ── Constants ─────────────────────────────────────────────────────────────────
_DEFAULT_OUTPUT = _SRC_DIR / "data" / "xpl_manifest.json"
_XPL_DIR        = _ROOT / "xpl"

_ERA_THRESHOLDS = {
    "legacy":   (None, 2019),   # up to 2019
    "modern":   (2020, None),   # 2020 onward
    "timeless": (None, None),   # no year — generic/scanner modules
}

_VENDOR_NORMALIZE: Dict[str, str] = {
    "hp": "hp", "hewlett": "hp", "laserjet": "hp",
    "ricoh": "ricoh",
    "lexmark": "lexmark",
    "brother": "brother",
    "canon": "canon",
    "epson": "epson",
    "xerox": "xerox",
    "kyocera": "kyocera",
    "samsung": "samsung",
    "konica": "konica", "konica minolta": "konica",
    "sharp": "sharp",
    "oki": "oki",
    "toshiba": "toshiba",
    "fujifilm": "fujifilm",
    "dell": "dell",
    "cups": "cups", "openprinting": "cups",
    "linux": "linux",
    "microsoft": "microsoft", "windows": "microsoft",
    "honeywell": "honeywell",
    "star": "star",
    "bixolon": "bixolon",
    "generic": "generic", "any": "generic", "all": "generic", "mfp": "generic",
}


def _era(year: Optional[int]) -> str:
    if year is None:
        return "timeless"
    if year >= 2020:
        return "modern"
    return "legacy"


def _normalize_vendors(raw: object) -> List[str]:
    """Normalise vendor field to a list of slug strings."""
    if not raw:
        return ["generic"]
    items: List[str] = [raw] if isinstance(raw, str) else list(raw)
    slugs: List[str] = []
    for item in items:
        key = item.lower().strip()
        slug = _VENDOR_NORMALIZE.get(key)
        if not slug:
            # partial match
            for k, v in _VENDOR_NORMALIZE.items():
                if k in key:
                    slug = v
                    break
        slugs.append(slug or "generic")
    return sorted(set(slugs)) if slugs else ["generic"]


def _detect_integration(directory: Path, metadata: Dict) -> str:
    """Infer integration type from directory contents and metadata."""
    source = str(metadata.get("source", "")).lower()
    if source == "metasploit":
        return "orchestration_msf"
    # Check for C source file
    if any(directory.glob("*.c")) or any(directory.glob("*.cpp")):
        return "native_poly_c"
    # MSF wrappers often contain 'msf' or 'metasploit' in title/id
    title_id = f"{metadata.get('id','')} {metadata.get('title','')}".lower()
    if "metasploit" in source or "msf" in title_id[:8]:
        return "orchestration_msf"
    return "native_python"


def _year_from_metadata(metadata: Dict) -> Optional[int]:
    """Extract year from metadata (cve id, date field, or None)."""
    year = metadata.get("year")
    if year:
        try:
            return int(str(year)[:4])
        except (ValueError, TypeError):
            pass
    # From CVE ID
    cve = str(metadata.get("cve", ""))
    if cve.startswith("CVE-"):
        parts = cve.split("-")
        if len(parts) >= 2:
            try:
                return int(parts[1])
            except ValueError:
                pass
    # From date field
    date = str(metadata.get("date", ""))
    if len(date) >= 4:
        try:
            return int(date[:4])
        except ValueError:
            pass
    return None


def build_manifest(root: Path = _ROOT) -> Dict:
    """Load all exploits from disk and build the manifest dict."""
    # Import the loader — works after sys.path setup
    from utils.exploit_manager import load_all_exploits

    # Temporarily bypass profile filtering to scan everything
    import os
    os.environ["PXF_PROFILE"] = "all"
    exploits = load_all_exploits()
    del os.environ["PXF_PROFILE"]

    modules: List[Dict] = []
    by_era: Dict[str, int]    = {"legacy": 0, "modern": 0, "timeless": 0}
    by_vendor: Dict[str, int] = {}
    by_integration: Dict[str, int] = {}

    for xpl in exploits:
        year = _year_from_metadata(xpl.metadata)
        era  = _era(year)
        vendors     = _normalize_vendors(xpl.metadata.get("vendor"))
        integration = _detect_integration(xpl.path, xpl.metadata)
        categories  = list({
            str(c).lower()
            for c in ([xpl.category] if xpl.category else [])
            + xpl.tags
            if c and len(str(c)) > 1
        })

        # Relative path from project root
        try:
            rel_path = str(xpl.path.relative_to(root)).replace("\\", "/")
        except ValueError:
            rel_path = f"xpl/{xpl.path.name}"

        entry = {
            "id":          f"{rel_path}/exploit.py" if xpl.path.is_dir() else rel_path,
            "path":        rel_path,
            "source":      xpl.metadata.get("source", "research"),
            "title":       xpl.title,
            "cve":         xpl.cve,
            "year":        year,
            "era":         era,
            "vendors":     vendors,
            "integration": integration,
            "categories":  categories,
            "severity":    xpl.severity,
            "cvss":        xpl.cvss,
        }
        modules.append(entry)

        by_era[era] = by_era.get(era, 0) + 1
        for v in vendors:
            by_vendor[v] = by_vendor.get(v, 0) + 1
        by_integration[integration] = by_integration.get(integration, 0) + 1

    manifest = {
        "_meta": {
            "generated":       time.strftime("%Y-%m-%d"),
            "total":           len(modules),
            "by_era":          by_era,
            "by_vendor":       dict(sorted(by_vendor.items())),
            "by_integration":  by_integration,
            "default_profile": "modern",
        },
        "modules": modules,
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate src/data/xpl_manifest.json from disk exploits.",
    )
    parser.add_argument(
        "--output", "-o",
        default=str(_DEFAULT_OUTPUT),
        help=f"Output path (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print summary without writing the file.",
    )
    args = parser.parse_args()

    print("[*] Loading exploits from disk...")
    manifest = build_manifest()
    total = manifest["_meta"]["total"]
    print(f"[+] Found {total} exploit modules")
    print(f"    Era   : {manifest['_meta']['by_era']}")
    print(f"    Integration: {manifest['_meta']['by_integration']}")

    if args.dry_run:
        print("[i] Dry-run mode — manifest not written.")
        return 0

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[+] Written: {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
