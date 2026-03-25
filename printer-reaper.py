#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper v3.7.0 — Advanced Printer Penetration Testing Toolkit
====================================================================
Root entry point — forwards all arguments to src/main.py.

Usage:
    python printer-reaper.py [target] [mode] [options]
    python3 printer-reaper.py --help

Examples:
    python printer-reaper.py                          # interactive guided menu
    python printer-reaper.py 192.168.1.100 --scan     # passive recon
    python printer-reaper.py 192.168.1.100 pjl        # PJL interactive shell
    python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor epson
"""

# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import os
import sys

# Ensure src/ is on the path regardless of where the script is invoked from
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC  = os.path.join(_ROOT, "src")

if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

if __name__ == "__main__":
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(0)
    except ImportError as exc:
        print(f"[!] Import error: {exc}")
        print(f"    Make sure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
