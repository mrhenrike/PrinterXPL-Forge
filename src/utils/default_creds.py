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
    # Sources: Canon imageRUNNER/PRINT manuals, ij.manual.canon/en/PW/pw_default.html
    # Models with default password "canon" (username ADMIN):
    #   E460/E480, iB4000, MB2000/MB2300/MB5000/MB5300, MG2900/MG5600/MG6600/MG6700/MG7500,
    #   MX490, PRO-100S/PRO-10S series
    # All other models: serial number is default password
    # Printix Go integration: admin/Printix (must be set first time)
    'canon': [
        Cred('ADMIN',    'canon',        'http', 'E460/E480/iB4000/MB2000/MB5000/MG2900 series (ij.manual.canon)'),
        Cred('admin',    'canon',        'http', 'alias: lowercase admin'),
        Cred('ADMIN',    SERIAL_TOKEN,   'http', 'most other models: serial number is default password'),
        Cred('admin',    SERIAL_TOKEN,   'http', 'serial number alt login'),
        Cred('admin',    None,           'http', 'PRINT / MAXIFY / PIXMA: blank password'),
        Cred('admin',    'Printix',      'http', 'Printix Go integration default (Tungsten docs)'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    '7654321',      'http', 'imageRUNNER series'),
        Cred('admin',    '1111111',      'http', 'imageRUNNER series alt'),
        Cred('system',   'system',       'http', 'service access'),
        Cred('root',     None,           'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('root',     None,           'ftp'),
    ],

    # ── Ricoh ─────────────────────────────────────────────────────────────────
    # Sources: theinfocentric.com, ricoh KB, wikitwist.com, Tungsten Automation docs,
    #          Spiceworks community (supervisor backdoor), bizuns.com
    'ricoh': [
        Cred('admin',      None,         'http', 'most Aficio/MP: blank password'),
        Cred('admin',      'password',   'http', 'Web Image Monitor fallback'),
        Cred('admin',      'admin',      'http'),
        Cred('sysadmin',   'password',   'http', 'Aficio 2020D/2228c/2232C: service admin'),
        Cred('supervisor', None,         'http', 'UNDOCUMENTED backdoor — resets admin password (Spiceworks community)'),
        Cred('',           None,         'http', 'no auth / DSc338/NRG anonymous'),
        Cred('',           'password',   'http', 'NRG/DSc338 blank user + password'),
        Cred('admin',      '1234',       'http'),
        Cred('admin',      'ricoh',      'http', 'SOP Gen 2: Remote Installation Password default'),
        Cred('admin',      'Admin',      'http', 'some AP/IM series'),
        Cred('guest',      'guest',      'ftp',  'EDB-51755: FTP guest/guest on port 21'),
        Cred('public',     None,         'snmp'),
        Cred('private',    None,         'snmp'),
        Cred('admin',      None,         'ftp'),
    ],

    # ── Xerox ─────────────────────────────────────────────────────────────────
    # Sources: supertechman.com.au, open-sez.me/default-passwords-xerox.html,
    #          bizuns.com (DocuCentre 425: admin/22222, MFP: admin/2222),
    #          Tungsten Printix partner docs (admin/1111)
    'xerox': [
        Cred('admin',    '1111',         'http', 'VersaLink/AltaLink/WorkCentre 5300+; Tungsten Printix default'),
        Cred('admin',    '22222',        'http', 'DocuCentre 425 (bizuns.com)'),
        Cred('admin',    '2222',         'http', 'Multi Function Equipment series (bizuns.com)'),
        Cred('admin',    'admin',        'http'),
        Cred('11111',    'x-admin',      'http', 'DocuCentre/ApeosPort series'),
        Cred('admin',    'x-admin',      'http', 'Xerox 240a legacy (bizuns.com)'),
        Cred('admin',    None,           'http', 'Document Centre 425: no password'),
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

    # aliases — resolved dynamically via _ALIASES; empty lists here as placeholders
    'konica minolta': [],
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
    # Sources: Printix partner docs (Tungsten Automation), fujifilm.com KBs
    'fuji': [
        Cred('x-admin',  '11111',        'http', 'Fujifilm Business Innovation: Printix Go default (Tungsten docs)'),
        Cred('admin',    '1111',         'http', 'ApeosPort / DocuCentre'),
        Cred('11111',    'x-admin',      'http', 'DocuCentre legacy (Xerox/Fuji era)'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    None,           'http'),
        Cred('',         None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
        Cred('root',     None,           'ftp'),
    ],

    # alias
    'fujifilm': [],

    # ── Zebra Technologies ────────────────────────────────────────────────────
    # Sources: Zebra ZD421/ZD621 user guide, docs.zebra.com
    'zebra': [
        Cred('admin',    '1234',         'http',   'ZD421/ZD621/ZT-series print server default'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    None,           'http'),
        Cred('guest',    None,           'http',   'read-only guest'),
        Cred('public',   None,           'snmp',   'ZebraNet print server SNMP read'),
        Cred('private',  None,           'snmp',   'ZebraNet SNMP write'),
        Cred('admin',    '1234',         'ftp',    'ZebraNet bridge FTP'),
    ],

    # ── Axis Print Servers / Network Cameras ──────────────────────────────────
    # Sources: bizuns.com, Axis Communications KB
    'axis': [
        Cred('root',     'pass',         'http',   'ALL Axis Print Server default (bizuns.com)'),
        Cred('root',     'pass',         'ftp',    'Axis FTP default'),
        Cred('admin',    None,           'http'),
        Cred('admin',    'admin',        'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Dell Laser Printers ───────────────────────────────────────────────────
    # Sources: bizuns.com, Dell support KB
    'dell': [
        Cred('admin',    'password',     'http',   '3000cn/3100cn/5100cn EWS default'),
        Cred('admin',    None,           'http'),
        Cred('admin',    'admin',        'http'),
        Cred('admin',    '1234',         'http'),
        Cred('root',     'calvin',       'http',   'Dell iDRAC/Remote Access Card backdoor'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Minolta / QMS / Magicolor ─────────────────────────────────────────────
    # Sources: bizuns.com, Minolta Magicolor 3100 manual
    'minolta': [
        Cred('operator', None,           'http',   'Magicolor 3100: operator role'),
        Cred('admin',    None,           'http',   'Magicolor 3100: admin role'),
        Cred('admin',    '0',            'http',   'Di 2010f: numeric zero password'),
        Cred('',         '0',            'http',   'Di 2010f: blank user, zero password'),
        Cred('sysadm',   'sysadm',       'http',   'QMS 4100GN PagePro'),
        Cred('admin',    'admin',        'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Xerox (expanded) ──────────────────────────────────────────────────────
    # Already defined above as 'xerox'; alias entries below expand it.
    # DocuCentre 425 uses admin/22222 (bizuns.com)
    # Multi-Function Equipment uses admin/2222

    # ── IBM Printers / Infoprint ──────────────────────────────────────────────
    # Sources: bizuns.com
    'ibm': [
        Cred('root',     None,           'http',   'Infoprint 6700: root blank password'),
        Cred('admin',    'password',     'http'),
        Cred('USERID',   'PASSW0RD',     'http',   'IBM BladeCenter / Remote Supervisor'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # ── Develop / Ineo (Konica Minolta OEM) ──────────────────────────────────
    'develop': [
        Cred('admin',    '12345678',     'http',   'Ineo+/ineo series (KM OEM)'),
        Cred('admin',    None,           'http'),
        Cred('public',   None,           'snmp'),
        Cred('private',  None,           'snmp'),
    ],

    # alias
    'ineo': [],

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
    'fujifilm business innovation': 'fuji',
    'hewlett':        'hp',
    'hewlett-packard':'hp',
    'hewlett packard':'hp',
    'jetdirect':      'hp',
    'epson seiko':    'epson',
    'seiko epson':    'epson',
    'brother industries': 'brother',
    'zebra technologies': 'zebra',
    'axis communications': 'axis',
    'develop ineo':   'develop',
    'ineo':           'develop',
    'nrg':            'ricoh',      # NRG is a Ricoh brand
    'nashuatec':      'ricoh',      # Nashuatec is a Ricoh brand
    'lanier':         'ricoh',      # Lanier is a Ricoh brand
    'savin':          'ricoh',      # Savin is a Ricoh brand
    'gestetner':      'ricoh',      # Gestetner is a Ricoh brand
    'infotec':        'ricoh',      # Infotec is a Ricoh brand
    'docucentre':     'fuji',       # DocuCentre is Fuji Xerox / Fujifilm
    'apeosport':      'fuji',
    'qms':            'minolta',
    'konica qms':     'minolta',
    'minolta qms':    'minolta',
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
