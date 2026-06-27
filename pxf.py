#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterXPL-Forge — root entry point (pxf)
=========================================
Forwards all arguments to src/main.py (XPL-Forge suite CLI pattern: exf, wxf, fxf, ixf, pxf).

Usage:
    python pxf.py [target] [mode] [options]
    pxf --help

Examples:
    python pxf.py                          # interactive guided menu
    python pxf.py 192.168.1.100 --scan     # passive recon
    python pxf.py 192.168.1.100 pjl        # PJL interactive shell
    python pxf.py 192.168.1.100 --bruteforce --bf-vendor epson
"""

# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.venv_bootstrap import ensure_runtime

ensure_runtime(__file__)

_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

if __name__ == "__main__":
    try:
        from main import main

        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(0)
    except ImportError as exc:
        print(f"[!] Import error: {exc}")
        print("    Run: ./setup_venv.sh   (Linux/macOS)  or  .\\setup_venv.ps1   (Windows)")
        print("    Or:  ./run.sh")
        print("    Check: pxf --doctor")
        sys.exit(1)
