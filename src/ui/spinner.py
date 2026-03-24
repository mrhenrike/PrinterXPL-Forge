#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Terminal Spinner
==================================
Thread-based spinner for long-running operations.
Works on Windows, Linux and macOS without external deps.
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager
from typing import Optional

_CYN = '\033[1;36m'
_GRN = '\033[1;32m'
_YEL = '\033[1;33m'
_RED = '\033[1;31m'
_DIM = '\033[2;37m'
_RST = '\033[0m'
_CLR = '\r\033[K'   # carriage return + clear line

_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
_FRAMES_ASCII = ['|', '/', '-', '\\']   # fallback for terminals without unicode


def _supports_unicode() -> bool:
    try:
        '⠋'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, LookupError, AttributeError):
        return False


class Spinner:
    """
    Context-manager spinner that shows animated activity during slow operations.

    Usage:
        with Spinner("Scanning...") as sp:
            do_slow_thing()
            sp.update("Still scanning...")
        # On exit: shows [DONE] or [FAIL] automatically
    """

    def __init__(self, message: str = '', color: str = _CYN,
                 interval: float = 0.08) -> None:
        self.message  = message
        self.color    = color
        self.interval = interval
        self._stop    = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frames  = _FRAMES if _supports_unicode() else _FRAMES_ASCII
        self._done    = False
        self._failed  = False

    def _spin(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = self._frames[i % len(self._frames)]
            sys.stdout.write(
                f'{_CLR}  {self.color}{frame}{_RST} {_DIM}{self.message}{_RST}'
            )
            sys.stdout.flush()
            time.sleep(self.interval)
            i += 1

    def start(self) -> 'Spinner':
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def update(self, message: str) -> None:
        """Update the spinner message while running."""
        self.message = message

    def stop(self, success: bool = True, final_msg: str = '') -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        icon  = f'{_GRN}✔{_RST}' if success else f'{_RED}✘{_RST}'
        label = final_msg or self.message
        sys.stdout.write(f'{_CLR}  {icon} {label}\n')
        sys.stdout.flush()

    def __enter__(self) -> 'Spinner':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop(success=(exc_type is None))
        return False   # re-raise exceptions


@contextmanager
def spinning(message: str, color: str = _CYN, done_msg: str = ''):
    """Convenience context manager."""
    sp = Spinner(message, color)
    sp.start()
    try:
        yield sp
        sp.stop(True, done_msg or message)
    except Exception:
        sp.stop(False, f'{message} — failed')
        raise
