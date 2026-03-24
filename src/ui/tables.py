#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Terminal Table Renderer
========================================
Simple, dependency-free table rendering for CLI output.
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import shutil
from typing import Any, List, Optional, Tuple

_RST = '\033[0m'
_DIM = '\033[2;37m'
_BLD = '\033[1m'
_CYN = '\033[1;36m'
_GRN = '\033[1;32m'
_YEL = '\033[1;33m'
_RED = '\033[1;31m'


def _strip_ansi(s: str) -> str:
    """Return string length ignoring ANSI escape sequences."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)


def _vis_len(s: str) -> int:
    return len(_strip_ansi(s))


def box(title: str = '', lines: List[str] = None,
        width: Optional[int] = None, color: str = _CYN) -> str:
    """
    Render a bordered box with optional title and content lines.

    Example:
        ╔══════════════════════╗
        ║  Title               ║
        ╠══════════════════════╣
        ║  Line 1              ║
        ╚══════════════════════╝
    """
    term_w = shutil.get_terminal_size((80, 24)).columns
    w = min(width or 66, term_w - 2)
    inner = w - 2

    top     = f"  {color}╔{'═' * inner}╗{_RST}"
    div     = f"  {color}╠{'═' * inner}╣{_RST}"
    bot     = f"  {color}╚{'═' * inner}╝{_RST}"
    side    = lambda s: f"  {color}║{_RST} {s:<{inner - 1}}{color}║{_RST}"

    parts = [top]
    if title:
        parts.append(side(f'{_BLD}{title}{_RST}'))
        if lines:
            parts.append(div)
    for line in (lines or []):
        # Handle long lines
        visible = _strip_ansi(line)
        if len(visible) <= inner - 1:
            parts.append(side(line))
        else:
            # Truncate with ellipsis
            parts.append(side(line[:inner - 4] + '...'))
    parts.append(bot)
    return '\n'.join(parts)


def table(headers: List[str], rows: List[List[Any]],
          col_colors: List[str] = None,
          header_color: str = _CYN,
          indent: str = '  ') -> str:
    """
    Render a simple aligned table.

    Args:
        headers:     Column header labels.
        rows:        List of row data (each row is a list of values).
        col_colors:  Per-column ANSI color codes.
        header_color: Color for header row.
    """
    if not rows and not headers:
        return ''

    num_cols = len(headers)
    col_widths = [_vis_len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row[:num_cols]):
            col_widths[i] = max(col_widths[i], _vis_len(str(cell)))

    def fmt_row(cells: List[Any], colors: List[str] = None) -> str:
        parts = []
        for i, cell in enumerate(cells[:num_cols]):
            w   = col_widths[i]
            s   = str(cell)
            vis = _vis_len(s)
            pad = ' ' * max(0, w - vis)
            clr = (colors[i] if colors and i < len(colors) else '') if colors else ''
            rst = _RST if clr else ''
            parts.append(f"{clr}{s}{rst}{pad}")
        return f"{indent}  " + '  '.join(parts)

    sep_line = indent + '  ' + '  '.join('─' * w for w in col_widths)

    lines = []
    lines.append(fmt_row(
        [f"{header_color}{h}{_RST}" for h in headers],
    ))
    lines.append(sep_line)
    for row in rows:
        lines.append(fmt_row(row, col_colors))
    return '\n'.join(lines)


def section(title: str, color: str = _CYN, width: int = 60) -> str:
    """Render a section header line."""
    term_w = shutil.get_terminal_size((80, 24)).columns
    w = min(width, term_w - 4)
    bar = '─' * w
    return f"\n  {color}┌{'─' * 2} {title} {'─' * max(0, w - len(title) - 4)}┐{_RST}"


def summary_line(label: str, value: str, label_color: str = _DIM,
                 value_color: str = _RST) -> str:
    """Render a key-value summary line."""
    return f"  {label_color}{label:<18}{_RST} {value_color}{value}{_RST}"
