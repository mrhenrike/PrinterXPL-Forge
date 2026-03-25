#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Wordlist Loader
================================
Loads printer credential wordlists from external files.
No credentials are hardcoded in the Python source.

Wordlist format (user:pass per line):
  - Lines starting with # are comments
  - Lines matching `# ── VENDOR NAME ──` start a new vendor section
  - Empty password: `admin:` or `admin:` (trailing colon = blank)
  - Empty username: `:password`
  - Both empty: `:`
  - Token references: `admin:__SERIAL__`, `admin:__MAC6__`, `admin:__MAC12__`

Vendor section parsing example:
  # ── HP (Hewlett-Packard) ─────────
  admin:
  admin:admin

Priority:
  1. Custom wordlist (--bf-wordlist)
  2. Default wordlist: wordlists/printer_default_creds.txt (auto-located)
  3. Vendor-specific fallback if a line belongs to the detected vendor section
  4. UNIVERSAL / GENERIC entries always appended
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from utils.default_creds import Cred, SERIAL_TOKEN, MAC6_TOKEN, MAC12_TOKEN, _ALIASES

logger = logging.getLogger(__name__)

# ── Vendor section header regex ───────────────────────────────────────────────
# Matches: # ── HP (Hewlett-Packard) ───────────────────────────────────────────
_SECTION_RE = re.compile(r'^#\s*[-─]+\s*(.+?)\s*[-─]*\s*$')

# Sections treated as "generic" / always included
_GENERIC_SECTIONS = {
    'universal', 'generic', 'universal / generic', 'common', 'general',
    'common default serial number patterns', 'common default', '',
}

# ── Wordlist discovery ────────────────────────────────────────────────────────

def _find_default_wordlist() -> Optional[Path]:
    """
    Locate the default printer_default_creds.txt wordlist.

    Searches (in order):
      1. wordlists/ relative to this file's location (src/utils/../..)
      2. wordlists/ relative to cwd
      3. ~/.printerreaper/wordlists/
    """
    candidates = [
        Path(__file__).parent.parent.parent / "wordlists" / "printer_default_creds.txt",
        Path.cwd() / "wordlists" / "printer_default_creds.txt",
        Path.home() / ".printerreaper" / "wordlists" / "printer_default_creds.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _find_snmp_wordlist() -> Optional[Path]:
    """Locate snmp_communities.txt wordlist."""
    candidates = [
        Path(__file__).parent.parent.parent / "wordlists" / "snmp_communities.txt",
        Path.cwd() / "wordlists" / "snmp_communities.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _find_ftp_wordlist() -> Optional[Path]:
    """Locate ftp_creds.txt wordlist."""
    candidates = [
        Path(__file__).parent.parent.parent / "wordlists" / "ftp_creds.txt",
        Path.cwd() / "wordlists" / "ftp_creds.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── Core parser ───────────────────────────────────────────────────────────────

def _normalize_vendor_from_section(header: str) -> str:
    """
    Extract and normalise vendor key from a section header string.

    Example: 'HP (Hewlett-Packard)' → 'hp'
    """
    # Strip parenthetical remarks
    clean = re.sub(r'\(.*?\)', '', header).strip().lower()
    # Remove trailing dashes/spaces
    clean = clean.rstrip('-─ ')
    return clean


def _parse_line(line: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parse a single wordlist line into (username, password).

    Returns None for blank/comment lines.
    Password == None means blank/empty password.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return None

    if ':' not in stripped:
        # Bare word → treat as username with blank password
        return (stripped, None)

    # Split on FIRST colon only
    idx = stripped.index(':')
    username = stripped[:idx]
    pwd_raw  = stripped[idx + 1:]

    password: Optional[str] = pwd_raw if pwd_raw else None
    return (username, password)


def load_wordlist(
    path: Optional[str | Path] = None,
    protocol: str = 'any',
) -> List[Cred]:
    """
    Load all credentials from a wordlist file.

    Args:
        path:     Path to wordlist file. If None, auto-finds the default.
        protocol: Protocol tag to assign to all loaded Cred entries.

    Returns:
        List of Cred objects (may be empty if file not found).
    """
    if path is None:
        path = _find_default_wordlist()

    if path is None:
        logger.warning("[wordlist] Default wordlist not found; returning empty list")
        return []

    path = Path(path)
    if not path.exists():
        logger.warning("[wordlist] Wordlist not found: %s", path)
        return []

    creds: List[Cred] = []
    seen: Set[Tuple[str, Optional[str]]] = set()
    current_section = 'generic'
    current_proto = protocol

    try:
        with open(path, encoding='utf-8', errors='ignore') as fh:
            for lineno, raw_line in enumerate(fh, 1):
                line = raw_line.rstrip('\n\r')

                # Check for section header: # ── Vendor ────
                m = _SECTION_RE.match(line)
                if m:
                    current_section = _normalize_vendor_from_section(m.group(1))
                    # Infer protocol from section name
                    if 'snmp' in current_section:
                        current_proto = 'snmp'
                    elif 'ftp' in current_section:
                        current_proto = 'ftp'
                    elif 'telnet' in current_section:
                        current_proto = 'telnet'
                    else:
                        current_proto = protocol
                    continue

                parsed = _parse_line(line)
                if parsed is None:
                    continue

                username, password = parsed
                key = (username, password)
                if key in seen:
                    continue
                seen.add(key)

                # Determine section vendor for the Cred notes field
                creds.append(Cred(
                    username=username,
                    password=password,
                    protocol=current_proto,
                    notes=current_section,
                ))

    except OSError as exc:
        logger.error("[wordlist] Failed to read %s: %s", path, exc)

    logger.debug("[wordlist] Loaded %d entries from %s", len(creds), path)
    return creds


def load_snmp_communities(path: Optional[str | Path] = None) -> List[str]:
    """
    Load SNMP community strings from snmp_communities.txt.

    Returns list of community strings (one per non-comment line).
    """
    if path is None:
        path = _find_snmp_wordlist()
    if path is None:
        return ["public", "private", "internal"]

    communities: List[str] = []
    seen: Set[str] = set()
    try:
        with open(path, encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                if s not in seen:
                    seen.add(s)
                    communities.append(s)
    except OSError:
        pass
    return communities


def load_ftp_creds(path: Optional[str | Path] = None) -> List[Cred]:
    """
    Load FTP credentials from ftp_creds.txt.

    Falls back to loading from the main wordlist FTP section if file not found.
    """
    if path is None:
        path = _find_ftp_wordlist()
    if path is None:
        # Pull from main wordlist
        return [c for c in load_wordlist() if c.protocol in ('ftp', 'any')]

    return load_wordlist(path=path, protocol='ftp')


# ── Vendor-aware loader ───────────────────────────────────────────────────────

def load_for_vendor(
    vendor: str,
    wordlist_path: Optional[str | Path] = None,
    include_generic: bool = True,
) -> List[Cred]:
    """
    Load credentials relevant to a specific vendor from a wordlist.

    The wordlist is parsed into sections; credentials from the matching
    vendor section are returned first, followed by GENERIC/UNIVERSAL entries.

    Args:
        vendor:         Vendor name (case-insensitive, e.g. 'epson', 'hp').
        wordlist_path:  Custom wordlist. If None, uses the default wordlist.
        include_generic: Whether to append GENERIC/UNIVERSAL section entries.

    Returns:
        Ordered list of Cred objects, deduplicated.
    """
    if wordlist_path is None:
        wl_path = _find_default_wordlist()
    else:
        wl_path = Path(wordlist_path)

    if wl_path is None or not wl_path.exists():
        logger.warning("[wordlist] Wordlist not found for vendor=%r; using empty list", vendor)
        return []

    # Normalize vendor key
    key = vendor.lower().strip()
    key = _ALIASES.get(key, key)

    # Partial match support
    all_keys = list(_ALIASES.values()) + list(_ALIASES.keys())
    if key not in all_keys:
        for alias_key in _ALIASES:
            if alias_key in key or key in alias_key:
                key = _ALIASES[alias_key]
                break

    # Parse the file into sections
    vendor_creds: List[Cred] = []
    generic_creds: List[Cred] = []
    seen: Set[Tuple[str, Optional[str]]] = set()

    current_section = 'generic'
    current_proto   = 'http'

    try:
        with open(wl_path, encoding='utf-8', errors='ignore') as fh:
            for raw_line in fh:
                line = raw_line.rstrip('\n\r')

                m = _SECTION_RE.match(line)
                if m:
                    current_section = _normalize_vendor_from_section(m.group(1))
                    if 'snmp' in current_section:
                        current_proto = 'snmp'
                    elif 'ftp' in current_section:
                        current_proto = 'ftp'
                    elif 'telnet' in current_section:
                        current_proto = 'telnet'
                    else:
                        current_proto = 'http'
                    continue

                parsed = _parse_line(line)
                if parsed is None:
                    continue

                username, password = parsed
                dedup_key = (username, password)

                cred = Cred(username=username, password=password,
                            protocol=current_proto, notes=current_section)

                # Determine if this section matches the requested vendor
                section_key = _ALIASES.get(current_section, current_section)
                is_vendor_match = (
                    section_key == key
                    or key in current_section
                    or current_section in key
                    or any(k in current_section for k in key.split())
                )
                is_generic = current_section in _GENERIC_SECTIONS

                if is_vendor_match and dedup_key not in seen:
                    seen.add(dedup_key)
                    vendor_creds.append(cred)
                elif is_generic and include_generic and dedup_key not in seen:
                    seen.add(dedup_key)
                    generic_creds.append(cred)

    except OSError as exc:
        logger.error("[wordlist] Failed to read %s: %s", wl_path, exc)

    # Token entries: always add __SERIAL__, __MAC6__, __MAC12__ variants
    # These are expanded at runtime in login_bruteforce.py
    token_entries = [
        Cred('admin',    SERIAL_TOKEN, 'http',  'serial number as password'),
        Cred('',         SERIAL_TOKEN, 'http',  'blank user + serial'),
        Cred('admin',    MAC6_TOKEN,   'http',  'last 6 of MAC'),
        Cred('admin',    MAC12_TOKEN,  'http',  'full MAC'),
    ]
    for tc in token_entries:
        k = (tc.username, tc.password)
        if k not in seen:
            seen.add(k)
            vendor_creds.append(tc)

    result = vendor_creds + generic_creds
    logger.debug("[wordlist] vendor=%r → %d vendor + %d generic = %d total",
                 vendor, len(vendor_creds), len(generic_creds), len(result))
    return result


# ── Convenience: default wordlist path ───────────────────────────────────────

def get_default_wordlist_path() -> Optional[str]:
    """Return the path to the default wordlist as a string, or None."""
    p = _find_default_wordlist()
    return str(p) if p else None


def wordlist_stats(path: Optional[str | Path] = None) -> Dict[str, int]:
    """
    Return stats about a wordlist file: total entries and count per vendor section.

    Args:
        path: Wordlist path. If None, uses the default wordlist.

    Returns:
        Dict mapping section name → count of credential entries.
    """
    if path is None:
        path = _find_default_wordlist()
    if path is None:
        return {}

    stats: Dict[str, int] = {}
    current_section = 'generic'
    try:
        with open(path, encoding='utf-8', errors='ignore') as fh:
            for line in fh:
                m = _SECTION_RE.match(line.rstrip())
                if m:
                    current_section = _normalize_vendor_from_section(m.group(1))
                    continue
                if _parse_line(line) is not None:
                    stats[current_section] = stats.get(current_section, 0) + 1
    except OSError:
        pass
    return stats
