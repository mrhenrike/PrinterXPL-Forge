#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Credential Type Definitions & Vendor Aliases
=============================================================
Defines the Cred dataclass, dynamic token constants, and vendor alias map.

All actual credential data lives in external wordlist files (wordlists/).
No credentials are hardcoded in this module.

To load credentials, use utils.wordlist_loader:
    from utils.wordlist_loader import load_for_vendor, load_wordlist
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ── Credential entry type ─────────────────────────────────────────────────────

@dataclass
class Cred:
    """Single credential entry."""
    username:  str
    password:  Optional[str]    # None = blank; special tokens: __SERIAL__, __MAC6__, __MAC12__
    protocol:  str = 'http'    # http / ftp / telnet / snmp / any
    notes:     str = ''

    def __repr__(self) -> str:
        pwd = repr(self.password) if self.password is not None else '(blank)'
        return f"Cred({self.username!r}, {pwd}, {self.protocol})"


# ── Sentinel tokens for dynamic passwords ─────────────────────────────────────
SERIAL_TOKEN = '__SERIAL__'    # replaced by device serial at runtime
MAC6_TOKEN   = '__MAC6__'      # replaced by last 6 chars of MAC address
MAC12_TOKEN  = '__MAC12__'     # replaced by full 12-char MAC (no separators)


# ── Vendor name aliases (normalisation) ───────────────────────────────────────
# Used by wordlist_loader.load_for_vendor() to map vendor strings to sections.
_ALIASES: Dict[str, str] = {
    # Konica Minolta
    'konica minolta':             'konica',
    'konicaminolta':              'konica',
    'develop ineo':               'develop',
    'ineo':                       'develop',
    # Fujifilm / Fuji Xerox
    'fujifilm':                   'fuji',
    'fuji xerox':                 'fuji',
    'fujifilm business innovation': 'fuji',
    'docucentre':                 'fuji',
    'apeosport':                  'fuji',
    # HP
    'hewlett':                    'hp',
    'hewlett-packard':            'hp',
    'hewlett packard':            'hp',
    'jetdirect':                  'hp',
    # Epson
    'epson seiko':                'epson',
    'seiko epson':                'epson',
    # Brother
    'brother industries':         'brother',
    # Zebra
    'zebra technologies':         'zebra',
    # Axis
    'axis communications':        'axis',
    # Ricoh / OEM brands
    'nrg':                        'ricoh',
    'nashuatec':                  'ricoh',
    'lanier':                     'ricoh',
    'savin':                      'ricoh',
    'gestetner':                  'ricoh',
    'infotec':                    'ricoh',
    # Minolta / QMS
    'qms':                        'minolta',
    'konica qms':                 'minolta',
    'minolta qms':                'minolta',
    # Tektronix / Xerox Phaser
    'tektronix':                  'xerox',
    'phaser':                     'xerox',
    # Lexmark Dell OEM
    'dell laser':                 'dell',
    # Sindoh
    'sindoh':                     'sindoh',
    # Canon brands
    'canon imagerunner':          'canon',
    'canon pixma':                'canon',
    # Samsung (now HP)
    'hp samsung':                 'samsung',
}


# ── Backward-compatible public API ────────────────────────────────────────────
# These functions delegate to wordlist_loader to avoid circular imports at
# module level. They exist so that existing call sites keep working without change.

def get_creds_for_vendor(vendor: str,
                          wordlist_path: Optional[str] = None) -> List[Cred]:
    """
    Return credential list for a vendor name (case-insensitive).

    Credentials are loaded from the external wordlist file, not hardcoded.
    Falls back to generic entries if vendor section not found.

    Args:
        vendor:        Vendor name (e.g. 'epson', 'hp', 'ricoh').
        wordlist_path: Optional path to a custom wordlist file.

    Returns:
        List of Cred objects ordered: vendor-specific first, then generic.
    """
    from utils.wordlist_loader import load_for_vendor
    return load_for_vendor(vendor, wordlist_path=wordlist_path)


def get_all_creds(wordlist_path: Optional[str] = None) -> List[Cred]:
    """
    Return flat list of all unique credential entries from the wordlist.

    Args:
        wordlist_path: Optional path to custom wordlist.

    Returns:
        List of Cred objects.
    """
    from utils.wordlist_loader import load_wordlist
    return load_wordlist(path=wordlist_path)
