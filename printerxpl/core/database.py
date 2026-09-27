"""PrinterXPL Operational Database.

Extends EmbedXPL XplDatabase base for PrinterXPL-specific usage.
Stored at ~/.printerxpl/pxf.db

Usage::

    from printerxpl.core.database import PxfDatabase

    db = PxfDatabase()
    db.workspace("pentest-x")
    db.add_host("192.168.1.1")
    db.add_vuln("192.168.1.1", module_path="printerxpl...", cve_ids=["CVE-..."])
    db.add_cred("192.168.1.1", "admin", "admin")
    db.stats()

Author: Andre Henrique (@mrhenrike) | Uniao Geek
# authorized use only
"""
from __future__ import annotations

from pathlib import Path

# XplDatabase base from EmbedXPL (shared infrastructure)
try:
    from embedxpl.core.database import XplDatabase
except ImportError:
    # Fallback: re-implement minimal base if EmbedXPL not installed
    import sys
    _SUITE = Path(__file__).resolve().parents[5]
    if str(_SUITE / "EmbedXPL-Forge") not in sys.path:
        sys.path.insert(0, str(_SUITE / "EmbedXPL-Forge"))
    from embedxpl.core.database import XplDatabase


class PxfDatabase(XplDatabase):
    """PrinterXPL operational database stored at ~/.printerxpl/pxf.db.

    Domain: Printers, MFP, plotters, PJL, PCL, PostScript
    """

    _DB_DIR  = Path.home() / ".printerxpl"
    _DB_FILE = "pxf.db"
    _TOOL    = "PrinterXPL"
