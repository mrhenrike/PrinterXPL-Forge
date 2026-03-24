#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Default Credentials Database
=============================================
Comprehensive database of known default credentials for network printers,
organized by vendor. Sources: official manuals, FCC filings, printerpasswords.com,
open-sez.me, vendor knowledge bases and security advisories.

Covers: HTTP web interface, EWS (Embedded Web Server), Telnet, FTP, SNMP.

Credential entries: (username, password, protocol, notes)
  - protocol: 'http', 'ftp', 'telnet', 'snmp', 'any'
  - password:  None = blank/empty,  '__SERIAL__' = device serial number,
               '__MAC6__' = last 6 digits of MAC,  '__MAC12__' = full MAC
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ── Credential entry type ────────────────────────────────────────────────────

@dataclass
class Cred:
    """Single credential entry."""
    username:  str
    password:  Optional[str]    # None = blank; special tokens: __SERIAL__, __MAC6__
    protocol:  str = 'http'    # http / ftp / telnet / snmp / any
    notes:     str = ''

    def __repr__(self) -> str:
        pwd = repr(self.password) if self.password is not None else '(blank)'
        return f"Cred({self.username!r}, {pwd}, {self.protocol})"


# ── Sentinel tokens for dynamic passwords ────────────────────────────────────
SERIAL_TOKEN = '__SERIAL__'    # replaced by device serial at runtime
MAC6_TOKEN   = '__MAC6__'      # replaced by last 6 chars of MAC address
MAC12_TOKEN  = '__MAC12__'     # replaced by full 12-char MAC (no separators)


# ── Vendor credential database ────────────────────────────────────────────────
# Key: lowercase vendor name or regex key.
# Value: list of Cred entries, most likely first.

_DB: Dict[str, List[Cred]] = {

    # ── EPSON ─────────────────────────────────────────────────────────────────
    # Sources: L3250 manual, EpsonNet Config docs, chiplessprinters.com
    # Default password for Web Config = product serial number (newer models)
    # Older models: blank or 'epson'
    'epson': [
        Cred('admin',    SERIAL_TOKEN,  'http', 'L3250/ET-2810 series: serial number is initial password'),
        Cred('admin',    None,           'http', 'older models: blank password'),
        Cred('admin',    'epson',        'http'),
        Cred('EpsonNet', None,           'http', 'EpsonNet Web interface (legacy)'),
        Cred('admin',    'admin',        'http'),
        Cred('root',     None,           'telnet'),
        Cred('public',   None,           'snmp', 'SNMP read community'),
        Cred('private',  None,           'snmp', 'SNMP write community'),
        Cred('epson',    None,           'ftp',  'FTP on port 21'),
        Cred('admin',    'password',     'http'),
        Cred('',         None,           'http', 'anonymous / no auth'),
        Cred('',         SERIAL_TOKEN,   'http', 'blank username + serial'),
    ],

    # ── HP / Hewlett-Packard ──────────────────────────────────────────────────
    # Sources: JetDirect manual, HP EWS docs, printerpasswords.com
    'hp': [
        Cred('admin',    None,           'http', 'most HP LaserJet/OfficeJet Pro: blank password'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    SERIAL_TOKEN,   'http', 'some models: last 8 chars of serial'),
        Cred('admin',    MAC6_TOKEN,     'http', 'some PageWide/OfficeJet: last 6 digits of MAC'),
        Cred('',         None,           'http', 'no auth required (early FW)'),
        Cred('JetDirect', None,          'http', 'HP JetDirect legacy'),
        Cred('admin',    '12345678',     'http', 'HP Enterprise defaults'),
        Cred('admin',    '1234',         'http'),
        Cred('admin',    'password',     'http'),
        Cred('root',     '',             'telnet', 'HP JetDirect telnet'),
        Cred('root',     None,           'ftp',  'FTP on port 21'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Brother ───────────────────────────────────────────────────────────────
    # Sources: brother-usa.com/app/answers/detail/a_id/152494, supertechman.com.au
    'brother': [
        Cred('admin',    'initpass',     'http', 'newer models 2019+: default Web Based Mgmt'),
        Cred('admin',    'access',       'http', 'older models: Web Based Management'),
        Cred('admin',    None,           'http', 'blank password (many models)'),
        Cred('admin',    '0000',         'http', 'numeric default'),
        Cred('admin',    MAC6_TOKEN,     'http', 'Init Password = last 6 of MAC on label'),
        Cred('admin',    'admin',        'http'),
        Cred('',         None,           'http', 'no auth'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('root',     None,           'ftp'),
    ],

    # ── Canon ─────────────────────────────────────────────────────────────────
    # Sources: Canon imageRUNNER/PRINT manuals, geeksinsneaks.com
    'canon': [
        Cred('admin',    None,           'http', 'most PRINT / MAXIFY: blank password'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    'canon',        'http'),
        Cred('admin',    '7654321',      'http', 'imageRUNNER series'),
        Cred('admin',    '1111111',      'http', 'imageRUNNER series alt'),
        Cred('system',   'system',       'http', 'service access'),
        Cred('root',     None,           'http'),
        Cred('ADMIN',    SERIAL_TOKEN,   'http', 'some models use serial'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('root',     None,           'ftp'),
    ],

    # ── Ricoh ─────────────────────────────────────────────────────────────────
    # Sources: theinfocentric.com, ricoh KB, wikitwist.com
    'ricoh': [
        Cred('admin',    None,           'http', 'most Aficio/MP: blank password'),
        Cred('admin',    'password',     'http', 'Web Image Monitor fallback'),
        Cred('admin',    'admin',        'http'),
        Cred('sysadmin', 'password',     'http', 'service admin'),
        Cred('supervisor', None,         'http'),
        Cred('',         None,           'http', 'no auth'),
        Cred('admin',    '1234',         'http'),
        Cred('admin',    'ricoh',        'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('admin',    None,           'ftp'),
    ],

    # ── Xerox ─────────────────────────────────────────────────────────────────
    # Sources: supertechman.com.au, open-sez.me/default-passwords-xerox.html
    'xerox': [
        Cred('admin',    '1111',         'http', 'VersaLink/AltaLink/WorkCentre 5300+'),
        Cred('admin',    'admin',        'http'),
        Cred('11111',    'x-admin',      'http', 'DocuCentre/ApeosPort series'),
        Cred('admin',    'x-admin',      'http', 'legacy models'),
        Cred('admin',    None,           'http'),
        Cred('admin',    '1234',         'http'),
        Cred('admin',    'password',     'http'),
        Cred('service',  '1111',         'http', 'service login'),
        Cred('customer', None,           'http', 'customer level (read-only)'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Kyocera ───────────────────────────────────────────────────────────────
    # Sources: open-sez.me/kyocera, Kyocera Command Center RX manual
    'kyocera': [
        Cred('Admin',    'Admin',        'http', 'most ECOSYS/TASKalfa: Command Center RX'),
        Cred('admin',    'Admin',        'http'),
        Cred('admin',    'admin',        'http'),
        Cred('',         'admin00',      'http', 'FS series: no username, pass=admin00'),
        Cred('',         'Admin',        'http'),
        Cred('Admin',    'admin00',      'http', 'TASKalfa 250ci/300ci'),
        Cred('',         '3500',         'http', 'ECOSYS M2035dn control panel'),
        Cred('',         '2800',         'http', 'FS-1028MFP panel'),
        Cred('',         '4000',         'http', 'FS-3040MFP panel'),
        Cred('',         '2500',         'http', 'FS-6025MFP panel'),
        Cred('root',     'root',         'telnet', 'IB-20/21 print server'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Konica Minolta ────────────────────────────────────────────────────────
    # Sources: copytechnet.com/forum, logmeonce.com/resources
    'konica': [
        Cred('admin',    '12345678',     'http', 'bizhub C3100p/C3350/C3850 and many others'),
        Cred('admin',    '1234567812345678', 'http', 'newer i-series: C224/C284/C364/C454+'),
        Cred('admin',    '000000',       'http', 'bizhub C20/C25/C35'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    'access',       'http', 'bizhub 20/20p'),
        Cred('administrator', None,      'http', 'C20p/C25p/C40p'),
        Cred('administrator', 'admin',   'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # alias
    'konica minolta': [],  # resolved dynamically to 'konica'
    'konicaminolta': [],

    # ── Samsung ───────────────────────────────────────────────────────────────
    # Sources: iTropics.net, Samsung CLX series manuals
    'samsung': [
        Cred('admin',    'sec00000',     'http', 'CLX-3180/CLX-6220 SyncThru Web Service'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    None,           'http'),
        Cred('admin',    '1234',         'http'),
        Cred('admin',    'samsung',      'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── OKI ───────────────────────────────────────────────────────────────────
    # Sources: cxsecurity.com, dimasio.com/oki-administrator, scribd/Oki-Passwords
    'oki': [
        Cred('admin',    MAC6_TOKEN,     'http', 'last 6 digits of MAC (default since 2010)'),
        Cred('root',     MAC6_TOKEN,     'http', 'older models: root + last 6 MAC'),
        Cred('admin',    'aaaaaa',       'http', 'C301DN new generation'),
        Cred('root',     'aaaaaa',       'http', 'B401/B411/B431'),
        Cred('root',     'aaaaaaaaaaaa000000', 'http', 'MB470/MB480'),
        Cred('admin',    '123456',       'http', 'MB760/MB770'),
        Cred('admin',    None,           'http'),
        Cred('admin',    'admin',        'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Lexmark ───────────────────────────────────────────────────────────────
    # Sources: theinfocentric.com/lexmark-default-admin-password
    'lexmark': [
        Cred('admin',    None,           'http', 'most modern models: blank password'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    '1234',         'http'),
        Cred('admin',    'password',     'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('root',     None,           'ftp'),
    ],

    # ── Sharp ─────────────────────────────────────────────────────────────────
    # Sources: open-sez.me/default-passwords-sharp.html
    'sharp': [
        Cred('admin',    'admin',        'http', 'MX-2600N/MX-5111N'),
        Cred('admin',    'Sharp',        'http', 'AR-M205/AR-M257/AR-M355N/AR-M550'),
        Cred('Administrator', 'admin',   'http', 'MX-4501N'),
        Cred('admin',    None,           'http'),
        Cred('admin',    'Admin',        'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Toshiba / Toshiba e-Studio ────────────────────────────────────────────
    'toshiba': [
        Cred('admin',    '123456',       'http', 'e-Studio 2051/2820c/3555x'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    None,           'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Panasonic ─────────────────────────────────────────────────────────────
    'panasonic': [
        Cred('admin',    '12345',        'http', 'KX-MB/DP-MB series'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    None,           'http'),
        Cred('',         None,           'http'),
        Cred('user',     'user',         'http', 'user-level login'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Fuji Xerox / Fujifilm ─────────────────────────────────────────────────
    'fuji': [
        Cred('admin',    '1111',         'http', 'ApeosPort / DocuCentre'),
        Cred('11111',    'x-admin',      'http', 'DocuCentre legacy'),
        Cred('admin',    'admin',        'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # alias
    'fujifilm': [],

    # ── Generic / Unknown vendor ──────────────────────────────────────────────
    # Tried when vendor cannot be determined
    'generic': [
        Cred('admin',    None,           'any', 'most common default'),
        Cred('admin',    'admin',        'any'),
        Cred('admin',    'password',     'any'),
        Cred('admin',    '1234',         'any'),
        Cred('admin',    '12345',        'any'),
        Cred('admin',    '123456',       'any'),
        Cred('admin',    '1234567',      'any'),
        Cred('admin',    '12345678',     'any'),
        Cred('',         None,           'any', 'blank user + blank pass'),
        Cred('',         'admin',        'any'),
        Cred('',         '1234',         'any'),
        Cred('root',     None,           'any'),
        Cred('root',     'root',         'any'),
        Cred('root',     'admin',        'any'),
        Cred('root',     'password',     'any'),
        Cred('user',     'user',         'any'),
        Cred('guest',    None,           'any'),
        Cred('guest',    'guest',        'any'),
        Cred('service',  'service',      'any'),
        Cred('support',  'support',      'any'),
        Cred('printer',  'printer',      'any'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('internal', None,           'snmp'),
        Cred('manager',  None,           'snmp'),
        Cred('SNMP_trap', None,          'snmp'),
    ],
}

# Resolve aliases to their canonical vendor
_ALIASES: Dict[str, str] = {
    'konica minolta': 'konica',
    'konicaminolta':  'konica',
    'fujifilm':       'fuji',
    'fuji xerox':     'fuji',
    'hewlett':        'hp',
    'hewlett-packard':'hp',
    'hewlett packard':'hp',
    'jetdirect':      'hp',
    'epson seiko':    'epson',
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_creds_for_vendor(vendor: str) -> List[Cred]:
    """
    Return credential list for a vendor name (case-insensitive).

    Falls back to 'generic' if vendor is unknown.
    Always appends generic entries not already present.
    """
    key = vendor.lower().strip()
    key = _ALIASES.get(key, key)

    # Partial match if exact key not found
    if key not in _DB:
        for k in _DB:
            if k and k != 'generic' and k in key:
                key = k
                break
        else:
            key = 'generic'

    specific = list(_DB.get(key, []))

    # Append generic entries not already covered
    seen = {(c.username, c.password, c.protocol) for c in specific}
    for g in _DB['generic']:
        if (g.username, g.password, g.protocol) not in seen:
            specific.append(g)
            seen.add((g.username, g.password, g.protocol))

    return specific


def get_all_creds() -> List[Cred]:
    """Return flat list of all unique credential entries across all vendors."""
    seen: set = set()
    result: List[Cred] = []
    for creds in _DB.values():
        for c in creds:
            key = (c.username, c.password, c.protocol)
            if key not in seen:
                seen.add(key)
                result.append(c)
    return result


def known_vendors() -> List[str]:
    """Return list of known vendor names (canonical keys)."""
    return [k for k in _DB if k and k not in _ALIASES]
