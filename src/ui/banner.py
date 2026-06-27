#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified PrinterXPL-Forge banner (interactive + CLI)."""

from __future__ import annotations

import shutil

_RST = '\033[0m'
_BLD = '\033[1m'
_DIM = '\033[2;37m'
_CYN = '\033[1;36m'
_RED = '\033[1;31m'


def print_app_banner(*, quiet: bool = False, subtitle: str = '',
                      action: str = '', show_meta: bool = True) -> None:
    """Print the standard boxed banner used across interactive and CLI modes."""
    if quiet:
        return
    from version import __version__, __release_date__

    w = min(58, max(48, shutil.get_terminal_size((80, 24)).columns - 4))
    title = f"PrinterXPL-Forge v{__version__}"
    sub = subtitle or "Advanced Printer Penetration Testing Toolkit"
    meta = f"@{__release_date__} · @mrhenrike"

    def row(text: str, bold: str = '') -> None:
        pad = max(0, w - 4 - len(text))
        inner = f"  {bold}{text}{_RST}{' ' * pad}  "
        print(f"  {_CYN}║{_RST}{inner}{_CYN}║{_RST}")

    print()
    print(f"  {_CYN}╔{'═' * w}╗{_RST}")
    row(title, f"{_RED}{_BLD}")
    row(sub, _DIM)
    if show_meta:
        row(meta, _DIM)
    if action:
        print(f"  {_CYN}╠{'═' * w}╣{_RST}")
        row(action)
    print(f"  {_CYN}╚{'═' * w}╝{_RST}")
    print()
