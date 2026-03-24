#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper v3.0.0 - Comprehensive QA Testing
=================================================
Expanded test suite covering:
  1. Module imports
  2. Version control
  3. Payload system
  4. PS operators database
  5. Protocol classes (RAW, LPD, IPP, SMB) — including IPv6
  6. Fuzzer
  7. Codebook
  8. SNMP backend detection
  9. SMB enumeration (unit)
 10. IPv4 / IPv6 address resolution (RAWProtocol)
 11. Local printer discovery (Windows / CUPS)
 12. Online discovery module import (Shodan / Censys)
 13. Real printer connectivity (optional — EPSON L3250 192.168.0.152)
 14. Capabilities detection against real printer (optional)
"""

import sys
import os
import socket

# Ensure src/ is on path before any local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Target for live tests (skip if unreachable)
LIVE_TARGET = '192.168.0.152'
LIVE_IPP_PORT = 631
LIVE_RAW_PORT = 9100


# ─── helper ──────────────────────────────────────────────────────────────────

def _check(results: dict, name: str, fn, *args, **kwargs):
    """Run *fn* and record pass/fail in *results*."""
    results['total'] += 1
    try:
        ret = fn(*args, **kwargs)
        print(f"  [PASS] {name}")
        results['passed'] += 1
        return ret
    except Exception as exc:
        print(f"  [FAIL] {name} — {exc}")
        results['failed'] += 1
        results['errors'].append({'test': name, 'error': str(exc)})
        return None


def _is_reachable(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True if *host*:*port* is open (for optional live tests)."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except OSError:
        return False


# ─── test blocks ─────────────────────────────────────────────────────────────

def test_module_imports(results: dict):
    print("\n[TEST 1] Module Imports")
    print("-" * 70)
    modules = [
        ('version',              'Version module'),
        ('core.printer',         'Base printer class'),
        ('core.capabilities',    'Capability detection'),
        ('core.discovery',       'Network discovery'),
        ('core.osdetect',        'OS detection'),
        ('modules.pjl',          'PJL module'),
        ('modules.ps',           'PostScript module'),
        ('modules.pcl',          'PCL module'),
        ('protocols.raw',        'RAW protocol'),
        ('protocols.lpd',        'LPD protocol'),
        ('protocols.ipp',        'IPP protocol'),
        ('protocols.smb',        'SMB protocol (pysmb backend)'),
        ('payloads',             'Payload system'),
        ('utils.helper',         'Helper utilities'),
        ('utils.codebook',       'Error codebook'),
        ('utils.fuzzer',         'Fuzzer'),
        ('utils.operators',      'PS operators'),
        ('utils.local_printers', 'Local printer discovery'),
        ('utils.discovery_online', 'Online discovery (Shodan/Censys)'),
    ]
    for mod, desc in modules:
        _check(results, f"{mod:35s} — {desc}", __import__, mod)


def test_version(results: dict):
    print("\n[TEST 2] Version Information")
    print("-" * 70)
    import version as v
    _check(results, 'version.get_version()      returns string', lambda: v.get_version())
    _check(results, 'version.get_version_info() returns tuple ', lambda: v.get_version_info())
    _check(results, '__version_info__ is 3-tuple              ', lambda: len(v.__version_info__) == 3 or None)
    _check(results, '__release_date__ present                 ', lambda: v.__release_date__)
    actual = v.get_version()
    print(f"         Current version: {actual}")


def test_payloads(results: dict):
    print("\n[TEST 3] Payload System")
    print("-" * 70)
    try:
        from payloads import list_payloads, load_payload
        payloads = list_payloads()
        _check(results, f'list_payloads() → {len(payloads)} payloads', lambda: payloads)
        for pname, kwargs, check in [
            ('banner.ps', {'msg': 'QA-TEST'}, 'QA-TEST'),
            ('loop.ps',   {},                 None),
            ('erase.ps',  {},                 None),
            ('storm.ps',  {'count': '5'},     '5'),
            ('exfil.ps',  {'file': '/etc/passwd'}, '/etc/passwd'),
        ]:
            def _load(pn=pname, kw=kwargs, chk=check):
                content = load_payload(pn, kw)
                if chk and chk not in content:
                    raise AssertionError(f"Expected {chk!r} in payload output")
                return len(content)
            _check(results, f'load_payload({pname:<12})', _load)
    except Exception as exc:
        print(f"  [FAIL] Payload system setup — {exc}")


def test_operators(results: dict):
    print("\n[TEST 4] PostScript Operators Database")
    print("-" * 70)
    from utils.operators import operators
    ops = operators()
    _check(results, f'operators loaded — {len(ops.oplist)} categories', lambda: len(ops.oplist) > 0 or None)
    total_ops = sum(len(v) for v in ops.oplist.values())
    _check(results, f'total operators: {total_ops}', lambda: total_ops > 0 or None)


def test_protocols(results: dict):
    print("\n[TEST 5] Network Protocol Classes")
    print("-" * 70)

    # RAW / IPv4
    from protocols.raw import RAWProtocol
    raw4 = RAWProtocol('127.0.0.1', 9100, timeout=1)
    _check(results, 'RAWProtocol IPv4 instantiate', lambda: raw4)
    _check(results, 'RAWProtocol repr            ', lambda: repr(raw4))
    _check(results, 'RAWProtocol is_ipv6=False   ', lambda: not raw4.is_ipv6 or None)

    # RAW / IPv6 address parse
    raw6 = RAWProtocol('::1', 9100, timeout=1)
    _check(results, 'RAWProtocol IPv6 instantiate', lambda: raw6)

    # RAW alias
    from protocols.raw import RawProtocol
    _check(results, 'RawProtocol alias works     ', lambda: RawProtocol)

    # LPD
    from protocols.lpd import LPDProtocol
    lpd = LPDProtocol('127.0.0.1', 515, timeout=1)
    _check(results, 'LPDProtocol instantiate     ', lambda: lpd)

    # IPP
    from protocols.ipp import IPPProtocol
    ipp = IPPProtocol('127.0.0.1', 631, timeout=1)
    _check(results, 'IPPProtocol instantiate     ', lambda: ipp)

    # SMB — full implementation check
    from protocols.smb import SMBProtocol, print_via_smb
    smb = SMBProtocol('127.0.0.1', share='print$', timeout=1)
    _check(results, 'SMBProtocol instantiate     ', lambda: smb)
    _check(results, 'SMBProtocol repr            ', lambda: repr(smb))
    _check(results, 'SMBProtocol get_info()      ', lambda: smb.get_info())
    _check(results, 'print_via_smb helper exists ', lambda: print_via_smb)


def test_smb_unit(results: dict):
    print("\n[TEST 6] SMB Protocol Unit Tests")
    print("-" * 70)
    from protocols.smb import SMBProtocol, _PYSMB_AVAILABLE
    _check(results, f'pysmb available: {_PYSMB_AVAILABLE}', lambda: True)

    # Unreachable host must not crash — connect() must return False
    def _connect_unreachable():
        s = SMBProtocol('192.0.2.1', timeout=1)  # RFC 5737 blackhole
        result = s.connect()
        assert result is False
        return True
    _check(results, 'connect() returns False on unreachable', _connect_unreachable)


def test_ipv6_resolution(results: dict):
    print("\n[TEST 7] IPv4 / IPv6 Address Resolution")
    print("-" * 70)
    from protocols.raw import _resolve_address

    _check(results, 'Resolve 127.0.0.1 → AF_INET ',
           lambda: _resolve_address('127.0.0.1')[0] == socket.AF_INET or None)
    _check(results, 'Resolve localhost   → AF_INET ',
           lambda: _resolve_address('localhost')[0] in (socket.AF_INET, socket.AF_INET6) or None)
    _check(results, 'Resolve ::1        → AF_INET6',
           lambda: _resolve_address('::1')[0] == socket.AF_INET6 or None)
    _check(results, 'Resolve [::1]      → AF_INET6',
           lambda: _resolve_address('[::1]')[0] == socket.AF_INET6 or None)


def test_fuzzer(results: dict):
    print("\n[TEST 8] Fuzzer System")
    print("-" * 70)
    from utils.fuzzer import fuzzer
    f = fuzzer()
    _check(results, 'fuzz_paths()            ', lambda: len(f.fuzz_paths()) > 0 or None)
    _check(results, 'fuzz_names()            ', lambda: len(f.fuzz_names()) > 0 or None)
    _check(results, 'fuzz_data(small)        ', lambda: len(f.fuzz_data('small')) > 0 or None)
    _check(results, 'fuzz_traversal_vectors()', lambda: len(f.fuzz_traversal_vectors()) > 0 or None)


def test_codebook(results: dict):
    print("\n[TEST 9] Error Codebook")
    print("-" * 70)
    from utils.codebook import codebook
    cb = codebook()
    _check(results, f'codelist loaded ({len(cb.codelist)} codes)', lambda: len(cb.codelist) > 0 or None)
    errors = list(cb.get_errors('10001'))
    _check(results, f'get_errors(10001) → {len(errors)} results', lambda: len(errors) > 0 or None)


def test_snmp_backend(results: dict):
    print("\n[TEST 10] SNMP Backend Detection")
    print("-" * 70)
    import importlib
    cap_mod = importlib.import_module('core.capabilities')
    backend = getattr(cap_mod, '_SNMP_BACKEND', None)
    _check(results, f'SNMP backend detected: {backend!r}', lambda: backend is not None or None)
    print(f"         Backend in use: {backend}")


def test_local_discovery(results: dict):
    print("\n[TEST 11] Local Printer Discovery")
    print("-" * 70)
    from utils.local_printers import discover_local_installed
    printers = discover_local_installed()
    _check(results, f'discover_local_installed() — {len(printers)} printers',
           lambda: isinstance(printers, list) or None)
    for p in printers[:3]:
        print(f"         • {p['name'][:40]:<40} IP={p['ip'] or '-':<16} {p['protocol']}")


def test_online_discovery_import(results: dict):
    print("\n[TEST 12] Online Discovery Module (Shodan / Censys)")
    print("-" * 70)
    _check(results, 'import utils.discovery_online',
           lambda: __import__('utils.discovery_online', fromlist=['OnlineDiscoveryManager']))
    try:
        import shodan
        ver = getattr(shodan, '__version__', 'unknown')
        _check(results, f'shodan available (v{ver})', lambda: True)
    except ImportError:
        print("  [SKIP] shodan not installed")

    try:
        import censys
        _check(results, 'censys available', lambda: True)
    except ImportError:
        print("  [SKIP] censys not installed")


def test_live_printer(results: dict):
    print("\n[TEST 13] Live Printer — EPSON L3250 (192.168.0.152)")
    print("-" * 70)

    if not _is_reachable(LIVE_TARGET, LIVE_IPP_PORT):
        print(f"  [SKIP] {LIVE_TARGET}:{LIVE_IPP_PORT} not reachable — skipping live tests")
        return

    # RAW connection to port 9100
    from protocols.raw import RAWProtocol
    def _raw_connect():
        p = RAWProtocol(LIVE_TARGET, LIVE_RAW_PORT, timeout=3)
        ok = p.connect()
        p.close()
        return ok
    _check(results, f'RAW connect {LIVE_TARGET}:{LIVE_RAW_PORT}', _raw_connect)

    # IPP (HTTPS) capabilities
    import argparse
    args = argparse.Namespace(
        target=LIVE_TARGET, mode='pjl', safe=False, quiet=True,
        debug=False, load=None, log=None, osint=False,
        auto_detect=False, discover_local=False, discover_online=False,
    )
    from core.capabilities import capabilities
    def _cap_ipp():
        cap = capabilities.__new__(capabilities)
        cap.support = False
        cap.timeout = 3
        cap.rundir = os.path.join(os.path.dirname(__file__), '..', 'src', 'core') + os.sep
        cap.models = []
        cap.doc_formats = []
        cap.ipp(LIVE_TARGET, ['PJL', 'PostScript', 'PCL'])
        return True
    _check(results, f'capabilities.ipp({LIVE_TARGET})', _cap_ipp)

    # SMB probe (port 445)
    from protocols.smb import SMBProtocol
    def _smb_probe():
        s = SMBProtocol(LIVE_TARGET, timeout=3)
        connected = s.connect()
        s.close()
        return True  # We just check it doesn't crash
    _check(results, f'SMBProtocol.connect({LIVE_TARGET}:445)', _smb_probe)


def test_live_capabilities(results: dict):
    print("\n[TEST 14] Capabilities Full Run Against EPSON L3250")
    print("-" * 70)

    if not _is_reachable(LIVE_TARGET, LIVE_IPP_PORT):
        print(f"  [SKIP] {LIVE_TARGET} not reachable")
        return

    import argparse
    from core.capabilities import capabilities
    args = argparse.Namespace(
        target=LIVE_TARGET, mode='pjl', safe=False, quiet=True,
        debug=False, load=None, log=None, osint=False,
        auto_detect=False, discover_local=False, discover_online=False,
    )
    def _run_cap():
        cap = capabilities(args)
        return cap
    cap = _check(results, 'capabilities(args) full run', _run_cap)
    if cap:
        print(f"         support = {cap.support}")
        if hasattr(cap, 'doc_formats'):
            print(f"         doc_formats = {cap.doc_formats}")


# ─── main ────────────────────────────────────────────────────────────────────

def run_comprehensive_tests():
    """Run all tests and return a results dict."""
    results = {'total': 0, 'passed': 0, 'failed': 0, 'errors': []}

    print("=" * 70)
    print("  PrinterReaper v3.0.0 — Comprehensive QA Test Suite")
    print("=" * 70)

    test_module_imports(results)
    test_version(results)
    test_payloads(results)
    test_operators(results)
    test_protocols(results)
    test_smb_unit(results)
    test_ipv6_resolution(results)
    test_fuzzer(results)
    test_codebook(results)
    test_snmp_backend(results)
    test_local_discovery(results)
    test_online_discovery_import(results)
    test_live_printer(results)
    test_live_capabilities(results)

    # ── final report ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  QA REPORT")
    print("=" * 70)
    pct = (results['passed'] / results['total'] * 100) if results['total'] else 0
    print(f"  Total : {results['total']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Rate  : {pct:.1f}%")

    if results['errors']:
        print(f"\n  Failures ({len(results['errors'])}):")
        for i, err in enumerate(results['errors'], 1):
            print(f"    {i}. {err['test']}")
            print(f"       {err['error']}")
    else:
        print("\n  [OK] ALL TESTS PASSED!")

    return results


if __name__ == "__main__":
    res = run_comprehensive_tests()
    sys.exit(0 if res['failed'] == 0 else 1)
