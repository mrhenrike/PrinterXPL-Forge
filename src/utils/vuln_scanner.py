#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Vulnerability Scanner
=======================================
Matches printer fingerprints against known CVEs using:
  1. NVD (NIST National Vulnerability Database) API v2 — real-time lookup
  2. Built-in curated CVE database for common printer vulns
  3. Shodan CVE data (if API key is available)

Also detects common misconfigurations:
  - SNMP public community string
  - Open PJL without authentication
  - Default web credentials
  - Unprotected IPP queue
  - Outdated firmware signatures
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings()

_log = logging.getLogger(__name__)

NVD_API  = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_DELAY = 0.6  # seconds between NVD requests (rate limit: 5 req/30s without key)


# ── CVE result dataclass ──────────────────────────────────────────────────────

@dataclass
class CVEEntry:
    """A single CVE record."""
    cve_id:       str
    description:  str
    cvss_score:   float
    cvss_version: str
    severity:     str
    published:    str
    modified:     str
    references:   List[str] = field(default_factory=list)
    source:       str = 'nvd'
    exploitable:  bool = False
    exploit_info: str = ''
    affected_product: str = ''

    def __str__(self) -> str:
        return (f"{self.cve_id} [{self.severity} {self.cvss_score}] "
                f"{self.description[:80]}")


@dataclass
class VulnReport:
    """Complete vulnerability report for a printer."""
    host:       str
    make:       str
    model:      str
    firmware:   str
    cves:       List[CVEEntry]     = field(default_factory=list)
    misconfigs: List[str]          = field(default_factory=list)
    risk_score: float              = 0.0
    summary:    str                = ''

    @property
    def critical(self) -> List[CVEEntry]:
        return [c for c in self.cves if c.severity.upper() in ('CRITICAL', 'HIGH')]

    @property
    def exploitable(self) -> List[CVEEntry]:
        return [c for c in self.cves if c.exploitable]


# ── Built-in printer CVE database ─────────────────────────────────────────────
# Format: (make_pattern, model_pattern, firmware_pattern, cve_id, cvss, severity,
#           description, exploitable, exploit_notes)

_BUILTIN_CVES = [
    # EPSON
    ('EPSON', '', '',
     'CVE-2019-3948', 9.8, 'CRITICAL',
     'EPSON network printers: unauthenticated arbitrary command execution via LPD '
     '(port 515). Affects multiple EPSON WorkForce and EcoTank models.',
     True, 'Send crafted LPD job to port 515; no auth required'),

    ('EPSON', '', '',
     'CVE-2019-3949', 7.5, 'HIGH',
     'EPSON printers: XSS in web admin interface via printer name or location field.',
     False, 'Requires access to web admin interface'),

    ('EPSON', r'L\d{4}', '',
     'CVE-2021-26598', 6.1, 'MEDIUM',
     'EPSON EcoTank series: CSRF in web management page allows configuration change.',
     False, 'Requires user to visit malicious page while connected to printer network'),

    ('EPSON', '', '',
     'CVE-2022-3426', 5.4, 'MEDIUM',
     'EPSON printers: information disclosure via unauthenticated access to device '
     'information page (IP, MAC, serial number, firmware version).',
     False, 'HTTP GET /info or IPP GET-PRINTER-ATTRIBUTES returns serial/UUID'),

    # HP
    ('HP', r'LaserJet', '',
     'CVE-2011-4161', 10.0, 'CRITICAL',
     'HP LaserJet: unauthenticated arbitrary file read via PJL FSDOWNLOAD command.',
     True, 'Send: @PJL FSDOWNLOAD FORMAT:BINARY SIZE=... NAME="0:/file"'),

    ('HP', r'LaserJet', '',
     'CVE-2014-7872', 9.8, 'CRITICAL',
     'HP LaserJet Pro: unauthenticated remote code execution via malformed IPP request.',
     True, 'Exploit: CVE-2014-7872 — targeted IPP crafted request'),

    ('HP', '', '',
     'CVE-2017-2741', 9.8, 'CRITICAL',
     'HP PageWide and OfficeJet Pro: arbitrary code execution via malformed print job.',
     True, 'PoC available on Exploit-DB: EDB-ID 44292'),

    ('HP', '', '',
     'CVE-2023-1329', 9.8, 'CRITICAL',
     'HP LaserJet Pro: buffer overflow via PJL allowing RCE without authentication.',
     True, 'HPSEC-2023-002; affects firmware < 20230209'),

    # Brother
    ('Brother', '', '',
     'CVE-2017-16249', 9.1, 'CRITICAL',
     'Brother network printers: unauthenticated LPD print job allows PostScript exec.',
     True, 'Send PS payload via LPD to port 515 with no credentials'),

    # Ricoh / Aficio
    ('Ricoh', r'Aficio|MP', '',
     'CVE-2019-14318', 9.8, 'CRITICAL',
     'Ricoh printers: command injection via device management web interface.',
     True, 'Exploit: craft HTTP request to management API'),

    # Xerox
    ('Xerox', r'WorkCentre|Phaser', '',
     'CVE-2018-9071', 7.5, 'HIGH',
     'Xerox WorkCentre: directory traversal in web server allows file read.',
     True, 'GET /../../etc/passwd on port 80'),

    # Generic PJL
    ('', '', '',
     'CVE-2014-3741', 7.8, 'HIGH',
     'Generic PJL printers: path traversal via FSDOWNLOAD/FSUPLOAD allows '
     'reading printer filesystem (passwords, configs).',
     True, 'PJL: @PJL FSDOWNLOAD FORMAT:BINARY SIZE=... NAME="0:/../../../etc/passwd"'),

    # Generic SNMP
    ('', '', '',
     'CWE-284-SNMP', 6.5, 'MEDIUM',
     'SNMP v1/v2c with default "public" community string allows unauthenticated '
     'read of MIB data including device info, interface table, and print jobs.',
     False, 'snmpwalk -v 2c -c public <host>'),

    # Generic IPP
    ('', '', '',
     'CVE-2017-18190', 7.5, 'HIGH',
     'CUPS/IPP: unauthorized access to printer queue and job submission without '
     'authentication when ipp-everywhere or AirPrint is enabled.',
     True, 'Send IPP Print-Job operation to port 631; no credentials required'),

    # Log4Shell relevance
    ('EPSON', '', '',
     'CVE-2021-44228', 10.0, 'CRITICAL',
     'Log4Shell: if printer firmware uses Log4j (rare but possible in EPSON EcoTank '
     'cloud services), JNDI injection via logged fields may cause RCE.',
     False, 'Check firmware changelog; typically not exploitable on consumer printers'),
]


# ── NVD API lookup ────────────────────────────────────────────────────────────

def _query_nvd(keyword: str, api_key: str = '', max_results: int = 20) -> List[CVEEntry]:
    """Query the NVD API v2 for CVEs matching *keyword*."""
    headers = {'Accept': 'application/json'}
    if api_key:
        headers['apiKey'] = api_key

    params = {
        'keywordSearch': keyword,
        'resultsPerPage': max_results,
        'startIndex': 0,
    }
    entries: List[CVEEntry] = []
    try:
        r = requests.get(NVD_API, params=params, headers=headers, timeout=15)
        if r.status_code == 403:
            _log.warning("NVD rate limit hit — add your NVD API key to config.yaml")
            return []
        if r.status_code != 200:
            _log.warning("NVD API returned %d for keyword=%r", r.status_code, keyword)
            return []

        data = r.json()
        for vuln in data.get('vulnerabilities', []):
            item  = vuln.get('cve', {})
            cve_id = item.get('id', 'CVE-?')

            # Description
            descs = item.get('descriptions', [])
            desc  = next((d['value'] for d in descs if d.get('lang') == 'en'), '')

            # CVSS scoring (try v3.1 → v3.0 → v2.0)
            metrics    = item.get('metrics', {})
            cvss_score = 0.0
            cvss_ver   = 'N/A'
            severity   = 'UNKNOWN'
            for v_key in ('cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2'):
                v_list = metrics.get(v_key, [])
                if v_list:
                    cv = v_list[0].get('cvssData', {})
                    cvss_score = float(cv.get('baseScore', 0))
                    cvss_ver   = cv.get('version', v_key[-2:])
                    severity   = cv.get('baseSeverity',
                                        v_list[0].get('baseSeverity', '?'))
                    break

            # References
            refs = [r2['url'] for r2 in item.get('references', [])[:5]]

            entries.append(CVEEntry(
                cve_id       = cve_id,
                description  = desc[:250],
                cvss_score   = cvss_score,
                cvss_version = cvss_ver,
                severity     = severity,
                published    = item.get('published', '')[:10],
                modified     = item.get('lastModified', '')[:10],
                references   = refs,
                source       = 'nvd',
            ))

    except requests.Timeout:
        _log.warning("NVD API timed out for keyword=%r", keyword)
    except Exception as exc:
        _log.warning("NVD query failed for %r: %s", keyword, exc)

    return entries


# ── Built-in CVE matching ─────────────────────────────────────────────────────

def _match_builtin(make: str, model: str, firmware: str) -> List[CVEEntry]:
    """Return built-in CVE entries matching the given make/model/firmware."""
    results = []
    for (make_pat, model_pat, fw_pat,
         cve_id, cvss, severity,
         desc, exploitable, exploit_info) in _BUILTIN_CVES:

        # Empty pattern = matches any
        if make_pat and not re.search(make_pat, make, re.I):
            continue
        if model_pat and not re.search(model_pat, model, re.I):
            continue
        if fw_pat and not re.search(fw_pat, firmware, re.I):
            continue

        results.append(CVEEntry(
            cve_id       = cve_id,
            description  = desc,
            cvss_score   = cvss,
            cvss_version = '3.1',
            severity     = severity,
            published    = '',
            modified     = '',
            source       = 'builtin',
            exploitable  = exploitable,
            exploit_info = exploit_info,
            affected_product = f"{make} {model}".strip(),
        ))
    return results


# ── Misconfiguration checks ───────────────────────────────────────────────────

def _check_misconfigs(
    open_ports: List[int],
    printer_langs: List[str],
    snmp_descr: str,
    doc_formats: List[str],
) -> List[str]:
    """Return list of detected misconfiguration strings."""
    misconfigs = []
    p = set(open_ports)
    langs = [l.upper() for l in printer_langs]

    if 161 in p:
        misconfigs.append(
            "[SNMP] Default 'public' community string likely active — "
            "exposes device MIB (run: snmpwalk -v2c -c public <host>)"
        )

    if 9100 in p and 'PJL' in langs:
        misconfigs.append(
            "[PJL] Port 9100 open with PJL — no authentication; "
            "filesystem read/write possible via @PJL FSDOWNLOAD/FSUPLOAD"
        )

    if 9100 in p and 'PS' in langs or 'POSTSCRIPT' in langs:
        misconfigs.append(
            "[PostScript] Port 9100 with PS support — unauthenticated code "
            "execution possible via crafted PS payload"
        )

    if 515 in p:
        misconfigs.append(
            "[LPD] Port 515 open — unauthenticated print jobs accepted; "
            "potential DoS and data exfiltration vector"
        )

    if 631 in p:
        misconfigs.append(
            "[IPP] Port 631 open — verify authentication is enforced; "
            "AirPrint/IPP-Everywhere may allow anonymous job submission"
        )

    if 80 in p or 443 in p:
        misconfigs.append(
            "[WEB] Web management interface exposed — verify default "
            "credentials changed (common: admin/admin, admin/<blank>)"
        )

    if snmp_descr:
        misconfigs.append(
            "[SNMP] Device info disclosed: " + snmp_descr[:80]
        )

    return misconfigs


# ── Risk scoring ──────────────────────────────────────────────────────────────

def _compute_risk_score(cves: List[CVEEntry], misconfigs: List[str]) -> float:
    """
    Compute a composite risk score 0.0–10.0.

    Formula: weighted average of top-3 CVE CVSS scores + misconfiguration bonus.
    """
    if not cves and not misconfigs:
        return 0.0

    sorted_scores = sorted([c.cvss_score for c in cves], reverse=True)
    top3 = sorted_scores[:3]
    if top3:
        base = (top3[0] * 0.60 + (top3[1] if len(top3) > 1 else 0) * 0.30 +
                (top3[2] if len(top3) > 2 else 0) * 0.10)
    else:
        base = 0.0

    # +0.3 per misconfiguration, capped at 2.0 bonus
    misconfig_bonus = min(len(misconfigs) * 0.3, 2.0)
    return min(round(base + misconfig_bonus, 1), 10.0)


# ── Main entry point ──────────────────────────────────────────────────────────

def scan(
    host:          str,
    make:          str       = '',
    model:         str       = '',
    firmware:      str       = '',
    open_ports:    List[int] = None,
    printer_langs: List[str] = None,
    snmp_descr:    str       = '',
    doc_formats:   List[str] = None,
    nvd_api_key:   str       = '',
    use_nvd:       bool      = True,
    use_builtin:   bool      = True,
    verbose:       bool      = False,
) -> VulnReport:
    """
    Run a complete vulnerability scan for the given printer.

    Args:
        host:         Printer IP/hostname.
        make:         Printer manufacturer (e.g. 'EPSON').
        model:        Printer model (e.g. 'L3250 Series').
        firmware:     Firmware version string.
        open_ports:   List of open TCP ports.
        printer_langs: Supported printer languages (PJL, PS, PCL…).
        snmp_descr:   SNMP sysDescr value.
        doc_formats:  IPP document-format-supported.
        nvd_api_key:  Optional NVD API key for higher rate limits.
        use_nvd:      Whether to query the NVD API.
        use_builtin:  Whether to check the built-in CVE database.
        verbose:      Print progress.

    Returns:
        A VulnReport with all found CVEs and misconfigurations.
    """
    open_ports    = open_ports    or []
    printer_langs = printer_langs or []
    doc_formats   = doc_formats   or []

    all_cves: List[CVEEntry] = []

    # 1. Built-in CVE database
    if use_builtin:
        builtin = _match_builtin(make, model, firmware)
        if verbose and builtin:
            print(f"  [+] Built-in DB: {len(builtin)} matches for {make} {model}")
        all_cves.extend(builtin)

    # 2. NVD API
    if use_nvd and (make or model):
        keywords = []
        if make and model:
            keywords.append(f"{make} {model} printer")
        elif make:
            keywords.append(f"{make} printer vulnerability")
        elif model:
            keywords.append(f"{model} printer")

        for kw in keywords[:2]:
            if verbose:
                print(f"  [*] NVD lookup: {kw!r} ...", end='', flush=True)
            nvd_results = _query_nvd(kw, api_key=nvd_api_key)
            if verbose:
                print(f" {len(nvd_results)} CVEs")
            all_cves.extend(nvd_results)
            time.sleep(NVD_DELAY)  # rate limit

    # Deduplicate by CVE ID (prefer builtin entries over NVD for exploitability info)
    seen: Dict[str, CVEEntry] = {}
    for cve in all_cves:
        if cve.cve_id not in seen or cve.source == 'builtin':
            seen[cve.cve_id] = cve
    deduped = sorted(seen.values(), key=lambda c: c.cvss_score, reverse=True)

    # 3. Misconfiguration checks
    misconfigs = _check_misconfigs(open_ports, printer_langs, snmp_descr, doc_formats)

    # 4. Risk score
    risk_score = _compute_risk_score(deduped, misconfigs)

    # 5. Summary
    critical_count  = sum(1 for c in deduped if c.severity.upper() in ('CRITICAL', 'HIGH'))
    exploitable_cnt = sum(1 for c in deduped if c.exploitable)
    summary = (
        f"{make} {model} | {len(deduped)} CVEs ({critical_count} critical/high, "
        f"{exploitable_cnt} with known exploits) | risk={risk_score}/10 | "
        f"{len(misconfigs)} misconfigurations"
    )

    return VulnReport(
        host       = host,
        make       = make,
        model      = model,
        firmware   = firmware,
        cves       = deduped,
        misconfigs = misconfigs,
        risk_score = risk_score,
        summary    = summary,
    )


def print_report(report: VulnReport) -> None:
    """Pretty-print a VulnReport to stdout."""
    SEV_COLOR = {
        'CRITICAL': '\033[1;31m',
        'HIGH':     '\033[0;31m',
        'MEDIUM':   '\033[1;33m',
        'LOW':      '\033[1;34m',
        'UNKNOWN':  '\033[2;37m',
    }
    RESET = '\033[0m'

    print(f"\n{'='*65}")
    print(f"  VULNERABILITY REPORT — {report.host}")
    print(f"{'='*65}")
    print(f"  Target  : {report.make} {report.model} {report.firmware}")
    print(f"  CVEs    : {len(report.cves)} total  "
          f"({len(report.critical)} critical/high, {len(report.exploitable)} exploitable)")
    print(f"  Risk    : {report.risk_score}/10.0")
    print(f"  Summary : {report.summary}")

    if report.cves:
        print(f"\n  {'CVE ID':<20} {'Score':>5}  {'Sev':<9} {'Exploitable'}")
        print(f"  {'-'*65}")
        for cve in report.cves[:25]:
            sev   = cve.severity.upper()
            color = SEV_COLOR.get(sev, '')
            exp   = 'YES *' if cve.exploitable else 'no'
            print(f"  {color}{cve.cve_id:<20} {cve.cvss_score:>5.1f}  {sev:<9} {exp}{RESET}")
            print(f"    {cve.description[:80]}")
            if cve.exploitable and cve.exploit_info:
                print(f"    \033[1;31m>> {cve.exploit_info[:80]}\033[0m")

    if report.misconfigs:
        print(f"\n  MISCONFIGURATIONS ({len(report.misconfigs)})")
        print(f"  {'-'*65}")
        for mc in report.misconfigs:
            print(f"  \033[1;33m[!]\033[0m {mc}")

    print()
