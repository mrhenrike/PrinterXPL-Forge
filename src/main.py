#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper - Advanced Printer Penetration Testing Toolkit
Main entry point.
"""

# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import argparse
import sys
from typing import Callable, Dict

from core.osdetect import get_os
from core.discovery import discovery
from core.capabilities import capabilities
from modules.pjl import pjl
from modules.ps import ps
from modules.pcl import pcl
from utils.helper import output
from version import get_version_string

# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
APP_NAME: str = "PrinterReaper"
VERSION: str = get_version_string()

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser (shared by CLI and help)."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME.lower(),
        description=f"{APP_NAME} - Advanced Printer Penetration Testing Toolkit",
    )
    # Make positionals optional to allow --discover-* without target/mode
    parser.add_argument("target", nargs='?', help="Printer IP address or hostname")
    parser.add_argument(
        "mode",
        nargs='?',
        choices=["pjl", "ps", "pcl", "auto"],
        help="Printer language to abuse (PJL, PostScript, PCL, or auto-detect)",
    )
    parser.add_argument(
        "-s",
        "--safe",
        help="Verify if the chosen language is supported before attacking",
        action="store_true",
    )
    parser.add_argument(
        "-q", "--quiet", help="Suppress warnings and banner", action="store_true"
    )
    parser.add_argument(
        "-d", "--debug", help="Enter debug mode (show raw traffic)", action="store_true"
    )
    parser.add_argument(
        "-i", "--load", metavar="file", help="Load and run commands from file"
    )
    parser.add_argument(
        "-o", "--log", metavar="file", help="Log raw data sent to the target"
    )
    parser.add_argument(
        "--osint",
        help="Check target exposure on public search engines (passive OSINT)",
        action="store_true",
    )
    parser.add_argument(
        "--auto-detect",
        help="Automatically detect supported printer languages",
        action="store_true",
    )
    # ── Custom port overrides ──────────────────────────────────────────────────
    _port_group = parser.add_argument_group(
        "custom port overrides",
        "Override default protocol ports. When not specified, each module uses its own "
        "default (RAW=9100, IPP=631, LPD=515, SNMP=161, FTP=21, HTTP=80, HTTPS=443, SMB=445, Telnet=23). "
        "Use when the printer listens on non-standard ports."
    )
    _port_group.add_argument(
        "--port-raw",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for RAW/PJL/JetDirect (default: 9100). Example: --port-raw 3910",
    )
    _port_group.add_argument(
        "--port-ipp",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for IPP (default: 631). Example: --port-ipp 8631",
    )
    _port_group.add_argument(
        "--port-lpd",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for LPD/LPR (default: 515). Example: --port-lpd 5515",
    )
    _port_group.add_argument(
        "--port-snmp",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for SNMP (default: 161). Example: --port-snmp 1161",
    )
    _port_group.add_argument(
        "--port-ftp",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for FTP management (default: 21). Example: --port-ftp 2121",
    )
    _port_group.add_argument(
        "--port-http",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for HTTP embedded web server (default: 80). Example: --port-http 8080",
    )
    _port_group.add_argument(
        "--port-https",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for HTTPS embedded web server (default: 443). Example: --port-https 8443",
    )
    _port_group.add_argument(
        "--port-smb",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for SMB/CIFS (default: 445). Example: --port-smb 4445",
    )
    _port_group.add_argument(
        "--port-telnet",
        metavar="PORT",
        type=int,
        default=None,
        help="Custom port for Telnet management (default: 23). Example: --port-telnet 2323",
    )
    _port_group.add_argument(
        "--extra-ports",
        metavar="PORT",
        action="append",
        dest="extra_ports",
        default=[],
        type=int,
        help=(
            "Extra port(s) to include in banner scan sweeps (repeatable). "
            "Example: --extra-ports 9200 --extra-ports 7100"
        ),
    )
    # Discovery helpers
    parser.add_argument(
        "--discover-local",
        action="store_true",
        help="Run local SNMP discovery to find printers on your networks",
    )
    parser.add_argument(
        "--discover-online",
        action="store_true",
        help=(
            "Run online discovery via Shodan/Censys using structured dorks. "
            "Requires at least one --dork-* filter OR a direct target IP. "
            "Printer context is always implicit — no need to specify 'printer'. "
            "Requires API keys in config.json."
        ),
    )
    # Dork filters for --discover-online
    _dork_group = parser.add_argument_group("online discovery filters (--discover-online dorks)")
    _dork_group.add_argument(
        "--dork-vendor",
        metavar="VENDOR",
        action="append",
        dest="dork_vendors",
        default=[],
        help=(
            "Vendor to search for (repeatable). "
            "Examples: hp, epson, ricoh, brother, canon, kyocera, xerox, lexmark, samsung, oki, zebra. "
            "Example: --dork-vendor epson --dork-vendor ricoh"
        ),
    )
    _dork_group.add_argument(
        "--dork-model",
        metavar="MODEL",
        default=None,
        help=(
            "Model string to search for in banner. "
            "Example: --dork-model 'deskjet pro 5500'"
        ),
    )
    _dork_group.add_argument(
        "--dork-country",
        metavar="COUNTRY",
        action="append",
        dest="dork_countries",
        default=[],
        help=(
            "Country filter (ISO code or name, repeatable). "
            "Examples: BR, brazil, argentina, US, DE. "
            "Example: --dork-country BR --dork-country AR"
        ),
    )
    _dork_group.add_argument(
        "--dork-city",
        metavar="CITY",
        default=None,
        help="City filter. Example: --dork-city 'Sao Paulo'",
    )
    _dork_group.add_argument(
        "--dork-region",
        metavar="REGION",
        action="append",
        dest="dork_regions",
        default=[],
        help=(
            "Geographic region filter (repeatable). "
            "Valid regions: latin_america, south_america, central_america, north_america, "
            "europe, eastern_europe, asia, southeast_asia, middle_east, africa, north_africa, oceania. "
            "Example: --dork-region latin_america"
        ),
    )
    _dork_group.add_argument(
        "--dork-port",
        metavar="PORT",
        type=int,
        action="append",
        dest="dork_ports",
        default=[],
        help=(
            "Port filter (repeatable). Common: 9100 (RAW/PJL), 515 (LPD), 631 (IPP). "
            "Example: --dork-port 9100 --dork-port 515"
        ),
    )
    _dork_group.add_argument(
        "--dork-org",
        metavar="ORG",
        default=None,
        help="Organization/ISP filter. Example: --dork-org 'Telefonica'",
    )
    _dork_group.add_argument(
        "--dork-cpe",
        metavar="CPE",
        default=None,
        help=(
            "CPE filter (Censys only). "
            "Example: --dork-cpe 'cpe:/h:hp:laserjet'"
        ),
    )
    _dork_group.add_argument(
        "--dork-limit",
        metavar="N",
        type=int,
        default=100,
        help="Maximum results per query (default: 100).",
    )
    _dork_group.add_argument(
        "--dork-engine",
        metavar="ENGINE[,ENGINE]",
        default=None,
        help=(
            "Comma-separated list of search engines to use. "
            "Choices: shodan, censys, fofa, zoomeye, netlas. "
            "Default: all engines with configured API keys. "
            "Example: --dork-engine shodan,fofa,netlas"
        ),
    )
    # Reconnaissance / scanning
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Banner grab + CVE lookup + attack surface assessment (no payloads sent)",
    )
    parser.add_argument(
        "--scan-ml",
        action="store_true",
        help="Same as --scan but also runs ML-assisted fingerprinting and attack scoring",
    )
    parser.add_argument(
        "--no-nvd",
        action="store_true",
        help="Skip NVD API CVE lookup during --scan (faster, offline)",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="Path to config.json (default: config.json next to src/)",
    )
    # ── Attack modules for non-PJL/PS/PCL printers ────────────────────────────
    parser.add_argument(
        "--ipp",
        action="store_true",
        help="Full IPP security audit: anonymous job, queue purge, attr manipulation",
    )
    parser.add_argument(
        "--ipp-submit",
        action="store_true",
        help="Submit an anonymous IPP print job (dry-run by default; add --no-dry to actually print)",
    )
    parser.add_argument(
        "--no-dry",
        action="store_true",
        help="Disable dry-run on --ipp-submit (actually sends the print job)",
    )
    parser.add_argument(
        "--pivot",
        action="store_true",
        help="Lateral movement audit: SSRF via IPP/WSD, internal host discovery",
    )
    parser.add_argument(
        "--pivot-scan",
        metavar="INTERNAL_HOST",
        default=None,
        help="Port-scan INTERNAL_HOST via printer SSRF (e.g. --pivot-scan 192.168.1.1)",
    )
    parser.add_argument(
        "--storage",
        action="store_true",
        help="Printer storage audit: FTP, web file manager, SNMP MIB dump, saved jobs",
    )
    parser.add_argument(
        "--firmware",
        action="store_true",
        help="Firmware audit: version extraction, upload endpoint check, NVRAM probe",
    )
    parser.add_argument(
        "--firmware-reset",
        choices=["pjl", "web", "ipp"],
        default=None,
        help="Attempt factory reset via specified method (DANGEROUS — authorized labs only)",
    )
    parser.add_argument(
        "--payload",
        metavar="LANG:TYPE",
        default=None,
        help="Inject a language-specific payload: escpr:info, pjl:reset, ps:custom, etc.",
    )
    parser.add_argument(
        "--payload-data",
        metavar="STRING",
        default='',
        help="Custom payload string for --payload LANG:custom",
    )
    parser.add_argument(
        "--implant",
        metavar="KEY=VALUE",
        default=None,
        help="Persistent config implant (smtp_host=X, dns=Y, snmp_community=Z, etc.)",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Show which API features are configured and exit",
    )
    # ── Full attack campaign (BlackHat matrix) ─────────────────────────────────
    parser.add_argument(
        "--attack-matrix",
        action="store_true",
        help=(
            "Run the full attack matrix: DoS, Protection Bypass, Job Manipulation, "
            "Info Disclosure. Probes all vectors from Müller et al. (2017) + 2024-2025 "
            "CVEs. Use --no-dry to actually exploit (DANGEROUS)."
        ),
    )
    parser.add_argument(
        "--network-map",
        action="store_true",
        help=(
            "Build a complete network map from the printer's perspective: SNMP routing, "
            "PJL network vars, web config, subnet scan, WSD neighbors, attack paths."
        ),
    )
    parser.add_argument(
        "--xsp",
        metavar="ATTACK_TYPE",
        default=None,
        choices=["info", "capture", "dos", "nvram", "exfil"],
        help=(
            "Generate Cross-Site Printing (XSP) + CORS spoofing payload. "
            "Types: info (printer id), capture (job sniffer), dos (loop), "
            "nvram (NVRAM damage), exfil (retrieve captured jobs)."
        ),
    )
    parser.add_argument(
        "--xsp-callback",
        metavar="URL",
        default="",
        help="Attacker callback URL for XSP --exfil payloads",
    )
    # ── Auto exploit ───────────────────────────────────────────────────────────
    parser.add_argument(
        "--auto-exploit",
        action="store_true",
        help=(
            "Automatic exploit selection: fingerprints the target, matches all applicable "
            "exploit modules, verifies vulnerability with check(), pre-fills all required "
            "parameters (host, port, serial, mac, vendor), and runs the best confirmed exploit. "
            "Dry-run by default — add --no-dry to execute live. "
            "Use --xpl-source to restrict to a specific exploit source."
        ),
    )
    parser.add_argument(
        "--auto-exploit-limit",
        metavar="N",
        type=int,
        default=8,
        help="Maximum number of exploits to probe with check() during --auto-exploit (default: 8).",
    )
    parser.add_argument(
        "--auto-exploit-run",
        metavar="N",
        type=int,
        default=1,
        help="Number of confirmed-vulnerable exploits to execute during --auto-exploit (default: 1).",
    )
    parser.add_argument(
        "--auto-exploit-file",
        metavar="FILE",
        default=None,
        help=(
            "Path to a custom exploit .py file to force-run via --auto-exploit. "
            "The program pre-fills host/port/serial/vendor automatically. "
            "Example: --auto-exploit-file /path/to/my_exploit.py"
        ),
    )
    # ── Exploit module ─────────────────────────────────────────────────────────
    parser.add_argument(
        "--xpl-list",
        action="store_true",
        help="List all available exploits in xpl/ directory",
    )
    parser.add_argument(
        "--xpl-check",
        metavar="EXPLOIT_ID",
        default=None,
        help="Check if target is vulnerable to a specific exploit (non-destructive)",
    )
    parser.add_argument(
        "--xpl-run",
        metavar="EXPLOIT_ID",
        default=None,
        help="Run a specific exploit against the target (dry-run by default; add --no-dry to execute)",
    )
    parser.add_argument(
        "--xpl-update",
        action="store_true",
        help="Rebuild xpl/index.json from loaded exploits and re-scan xpl/ directory",
    )
    parser.add_argument(
        "--xpl-fetch",
        metavar="EDB_ID",
        default=None,
        help="Download a raw exploit from ExploitDB by ID (e.g. --xpl-fetch 45273)",
    )
    parser.add_argument(
        "--xpl",
        action="store_true",
        help="Run exploit matching after --scan: shows available exploits for detected printer",
    )
    parser.add_argument(
        "--xpl-source",
        metavar="SOURCE",
        default=None,
        choices=["metasploit", "exploit-db", "research", "custom"],
        help=(
            "Filter --xpl-list or --xpl-run by exploit source. "
            "Choices: metasploit, exploit-db, research, custom"
        ),
    )
    # ── Brute force login ──────────────────────────────────────────────────────
    parser.add_argument(
        "--bruteforce",
        action="store_true",
        help=(
            "Brute-force printer login using default vendor credentials. "
            "Tests HTTP web admin, FTP, SNMP, Telnet. "
            "Generates variations: normal, reverse, leet, CamelCase, UPPER."
        ),
    )
    parser.add_argument(
        "--bf-serial",
        metavar="SERIAL",
        default=None,
        help=(
            "Device serial number for brute-force (used as password for EPSON, HP, etc.). "
            "Auto-detected from --scan if available. "
            "Example: --bf-serial XAABT77481"
        ),
    )
    parser.add_argument(
        "--bf-mac",
        metavar="MAC",
        default=None,
        help=(
            "Device MAC address for brute-force (used for OKI, Brother, Kyocera KR2). "
            "Example: --bf-mac AA:BB:CC:DD:EE:FF"
        ),
    )
    parser.add_argument(
        "--bf-vendor",
        metavar="VENDOR",
        default=None,
        help=(
            "Override vendor for credential selection (e.g. 'epson', 'hp', 'ricoh'). "
            "Auto-detected from --scan if available."
        ),
    )
    parser.add_argument(
        "--bf-cred",
        metavar="USER:PASS",
        action="append",
        default=[],
        help=(
            "Extra credential to test (can repeat). "
            "Example: --bf-cred admin:MyPass --bf-cred root:"
        ),
    )
    parser.add_argument(
        "--bf-no-variations",
        action="store_true",
        help="Disable password variation generation (leet/reverse/camelcase). Faster but less thorough.",
    )
    parser.add_argument(
        "--bf-delay",
        metavar="SECS",
        type=float,
        default=0.3,
        help="Delay in seconds between login attempts (default: 0.3s). Increase to avoid lockouts.",
    )
    parser.add_argument(
        "--bf-wordlist",
        metavar="FILE",
        default=None,
        help=(
            "Custom wordlist file for brute-force (format: user:pass per line, # = comment). "
            "REPLACES the default wordlist (wordlists/printer_default_creds.txt). "
            "Supports vendor sections: '# ── Vendor ───'. "
            "Use --bf-cred to add individual credentials on top of the wordlist. "
            "Example: --bf-wordlist /path/to/my_creds.txt"
        ),
    )
    # ── Send print job ─────────────────────────────────────────────────────────
    parser.add_argument(
        "--send-job",
        metavar="FILE",
        default=None,
        help=(
            "Send a file to the printer for printing. "
            "Supported: .ps, .pcl, .pdf, .txt, .png, .jpg, .doc, .docx and any raw format. "
            "Example: --send-job report.pdf"
        ),
    )
    parser.add_argument(
        "--send-proto",
        metavar="PROTO",
        default="raw",
        choices=["raw", "ipp", "lpd"],
        help="Protocol for send-job: raw (9100), ipp (631), lpd (515). Default: raw",
    )
    parser.add_argument(
        "--send-copies",
        metavar="N",
        type=int,
        default=1,
        help="Number of copies to print (default: 1)",
    )
    parser.add_argument(
        "--send-queue",
        metavar="QUEUE",
        default="lp",
        help="LPD queue name for --send-job with --send-proto lpd (default: lp)",
    )
    # ── Interactive mode ───────────────────────────────────────────────────────
    parser.add_argument(
        "--interactive", "-I",
        action="store_true",
        help="Launch guided interactive menu (default when run with no arguments)",
    )
    return parser


def get_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = build_parser()
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program version and exit",
    )
    return parser.parse_args()


from itertools import zip_longest


# --------------------------------------------------------------------------- #
# Scan / recon mode
# --------------------------------------------------------------------------- #
def _ui_section(step: str, title: str, target: str = '') -> None:
    """Print a clean section header for multi-step operations."""
    _CYN = '\033[1;36m'
    _DIM = '\033[2;37m'
    _RST = '\033[0m'
    _BLD = '\033[1m'
    tgt  = f' — {_DIM}{target}{_RST}' if target else ''
    print(f"\n  {_CYN}┌── [{step}] {_BLD}{title}{_RST}{tgt}")
    print(f"  {_CYN}│{_RST}")


def _run_auto_exploit(args) -> None:
    """
    Automatic exploit pipeline:
    1. Quick fingerprint (banner grab)
    2. Match + verify exploits with check()
    3. Pre-fill parameters and run() on top confirmed vulnerable exploit
    """
    from utils.banner_grabber import grab_all, print_fingerprint
    from utils.exploit_manager import auto_exploit, print_auto_exploit_summary

    target  = args.target
    timeout = getattr(args, 'timeout', 8)
    dry_run = not getattr(args, 'no_dry', False)

    output().green(f"\n>> Auto Exploit — {target}")

    # Step 1: fingerprint
    fp = {}
    try:
        fp = grab_all(target, timeout=timeout, quiet=True)
        if not args.quiet:
            print_fingerprint(fp)
    except Exception as exc:
        output().warning(f"Fingerprint failed: {exc} — proceeding with empty fingerprint")

    make      = fp.get('make', '') or ''
    model     = fp.get('model', '') or ''
    firmware  = fp.get('firmware', '') or ''
    ports     = fp.get('open_ports', []) or []
    langs     = fp.get('langs', []) or []
    cves      = fp.get('cves', []) or []
    serial    = getattr(args, 'bf_serial', '') or ''
    mac       = getattr(args, 'bf_mac', '') or ''

    results = auto_exploit(
        target,
        make           = make,
        model          = model,
        firmware       = firmware,
        open_ports     = ports,
        langs          = langs,
        cves           = cves,
        serial         = serial,
        mac            = mac,
        source_filter  = getattr(args, 'xpl_source', None),
        custom_xpl_path= getattr(args, 'auto_exploit_file', None),
        dry_run        = dry_run,
        check_limit    = getattr(args, 'auto_exploit_limit', 8),
        run_top_n      = getattr(args, 'auto_exploit_run', 1),
        timeout        = float(timeout),
        verbose        = not getattr(args, 'quiet', False),
    )

    print_auto_exploit_summary(results)


def _run_scan(args) -> None:
    """
    Run banner grabbing + CVE scan + optional ML analysis on args.target.
    No payloads are sent — this is pure reconnaissance.
    """
    from utils.config import load_config, nvd_key, feature_available, warn_missing
    from utils.banner_grabber import grab_all, print_fingerprint
    from utils.vuln_scanner import scan as vuln_scan, print_report

    load_config(path=getattr(args, 'config', None))
    target   = args.target
    use_nvd  = not getattr(args, 'no_nvd', False)
    use_ml   = getattr(args, 'scan_ml', False)

    # Inform user about optional NVD key (works without, just rate-limited)
    if use_nvd and not feature_available('nvd_lookup'):
        output().warning(
            "NVD API key not configured — using public rate limit (5 req/30s). "
            "Add nvd.api_key to config.json for higher limits."
        )
    timeout  = 5.0

    _ui_section('1/3', 'Fingerprint & Banner Grab', target)

    # 1. Banner grab (with spinner)
    try:
        from ui.spinner import Spinner
        sp = Spinner(f'Probing {target} ...').start()
        try:
            fp = grab_all(target, timeout=timeout, verbose=False)
        finally:
            sp.stop(True, f'Fingerprint complete — {fp.make or "?"} {fp.model or ""}')
    except Exception:
        fp = grab_all(target, timeout=timeout, verbose=True)
    print_fingerprint(fp)

    # 2. CVE / vuln scan
    _ui_section('2/3', 'Vulnerability Assessment', target)
    report = vuln_scan(
        host          = target,
        make          = fp.make,
        model         = fp.model,
        firmware      = fp.firmware,
        open_ports    = fp.open_ports,
        printer_langs = fp.printer_langs,
        snmp_descr    = fp.snmp_descr,
        doc_formats   = fp.doc_formats,
        nvd_api_key   = nvd_key(),
        use_nvd       = use_nvd,
        verbose       = True,
    )
    print_report(report)

    # 3. Exploit matching (always shown if exploits available; --xpl forces it)
    _ui_section('3/3', 'Exploit Matching & Recommendations', target)
    xpl_active = getattr(args, 'xpl', False) or True  # always show on scan
    try:
        from utils.exploit_manager import get_matched_for_target, print_matched_exploits
        all_cve_entries = report.specific_cves + report.vendor_cves + report.generic_cves
        vuln_cves = []
        for c in all_cve_entries:
            if hasattr(c, 'cve_id'):
                vuln_cves.append(c.cve_id)
            elif hasattr(c, 'id'):
                vuln_cves.append(c.id)
            elif isinstance(c, dict):
                vuln_cves.append(c.get('id', c.get('cve_id', '')))
        matched_xpls = get_matched_for_target(
            make=fp.make, model=fp.model, firmware=getattr(fp, 'firmware', '') or getattr(fp, 'firmware_version', ''),
            open_ports=fp.open_ports, langs=fp.printer_langs,
            cves=vuln_cves,
        )
        if matched_xpls:
            print_matched_exploits(matched_xpls, target)
        else:
            output().message(f"  [xpl] No specific exploits matched for {fp.make} {fp.model}")
    except Exception as exc:
        output().warning(f"Exploit matching error: {exc}")

    # 4. Brute-force hint + next-steps summary
    _CYN = '\033[1;36m'; _DIM = '\033[2;37m'; _RST = '\033[0m'
    _GRN = '\033[1;32m'; _YEL = '\033[1;33m'
    try:
        from utils.default_creds import get_creds_for_vendor
        bf_vendor_hint = (fp.make or '').lower().split()[0] if fp.make else 'generic'
        vendor_creds   = get_creds_for_vendor(bf_vendor_hint)
        serial_hint    = fp.serial or '<SERIAL>'
        print(f"\n  {_CYN}┌── Next Steps ──────────────────────────────────────────────{_RST}")
        print(f"  {_CYN}│{_RST}")
        print(f"  {_CYN}│{_RST}  {_GRN}Brute-force{_RST} ({len(vendor_creds)} default creds for {bf_vendor_hint}):")
        print(f"  {_CYN}│{_RST}    {_DIM}python src/main.py {target} --bruteforce "
              f"--bf-vendor {bf_vendor_hint} --bf-serial {serial_hint}{_RST}")
        print(f"  {_CYN}│{_RST}")
        print(f"  {_CYN}│{_RST}  {_GRN}Attack matrix{_RST} (BlackHat 2017 + CVEs, dry-run):")
        print(f"  {_CYN}│{_RST}    {_DIM}python src/main.py {target} --attack-matrix{_RST}")
        print(f"  {_CYN}│{_RST}")
        print(f"  {_CYN}│{_RST}  {_GRN}Network mapping{_RST} (subnet scan, pivot paths):")
        print(f"  {_CYN}│{_RST}    {_DIM}python src/main.py {target} --network-map{_RST}")
        print(f"  {_CYN}│{_RST}")
        print(f"  {_CYN}│{_RST}  {_YEL}Interactive guided menu:{_RST}")
        print(f"  {_CYN}│{_RST}    {_DIM}python src/main.py  (no args){_RST}")
        print(f"  {_CYN}└─────────────────────────────────────────────────────────────{_RST}")
    except Exception:
        pass

    # 5. Optional ML analysis
    if use_ml:
        output().green(">> ML-Assisted Analysis:")
        try:
            from utils.ml_engine import quick_analyze
            all_banners = ' '.join(str(v) for v in fp.raw_banners.values())
            quick_analyze(
                banner_text = all_banners,
                open_ports  = fp.open_ports,
                verbose     = True,
            )
        except Exception as exc:
            output().warning(f"ML engine error: {exc}")

    # 4. Auto-mode recommendation
    print()
    output().green(">> Attack Mode Recommendation:")
    langs = [l.upper() for l in fp.printer_langs]
    if 'PJL' in langs:
        output().message("  Recommended: python src/main.py {target} pjl --safe")
    elif 'PS' in langs or 'POSTSCRIPT' in langs:
        output().message(f"  Recommended: python src/main.py {target} ps --safe")
    elif 'PCL' in langs:
        output().message(f"  Recommended: python src/main.py {target} pcl --safe")
    elif fp.doc_formats:
        output().warning(
            f"  Printer uses {fp.printer_langs} — not a PJL/PS/PCL laser printer.\n"
            f"  Attack surface: IPP job submission, web interface, LPD flooding."
        )
    else:
        output().warning("  Could not determine printer language. Try: auto mode")

# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Send job dispatcher
# --------------------------------------------------------------------------- #
def _run_send_job(args) -> None:
    """Send a file/text to the target printer for printing."""
    from modules.print_job import send_print_job

    _CYN = '\033[1;36m'; _GRN = '\033[1;32m'
    _RED = '\033[1;31m';  _DIM = '\033[2;37m'; _RST = '\033[0m'

    target   = args.target
    filepath = args.send_job
    proto    = getattr(args, 'send_proto',  'raw')
    copies   = getattr(args, 'send_copies', 1)
    queue    = getattr(args, 'send_queue',  'lp')
    port     = getattr(args, 'port', 0) or 0

    from utils.ports import PortConfig
    proto_ports  = {p: PortConfig.resolve(p) for p in ('raw', 'ipp', 'lpd')}
    display_port = port or proto_ports.get(proto, PortConfig.resolve('raw'))

    print(f"\n  {_CYN}[ Send Job ]{_RST}")
    print(f"  {_DIM}Target   : {target}:{display_port}{_RST}")
    print(f"  {_DIM}File     : {filepath}{_RST}")
    print(f"  {_DIM}Protocol : {proto.upper()}{_RST}")
    print(f"  {_DIM}Copies   : {copies}{_RST}")
    print()

    result = send_print_job(
        host=target, path=filepath,
        protocol=proto, port=display_port,
        copies=copies, queue=queue,
    )

    if result.success:
        print(f"  {_GRN}[+] Print job sent successfully{_RST}")
        print(f"  {_DIM}    {result.file_size} bytes  elapsed {result.elapsed_ms:.0f}ms{_RST}")
        if result.message:
            print(f"  {_DIM}    {result.message}{_RST}")
    else:
        print(f"  {_RED}[-] Send failed: {result.error}{_RST}")


# Attack module dispatcher
# --------------------------------------------------------------------------- #
def _run_attack_modules(args) -> None:
    """
    Dispatch to the appropriate attack/audit module based on CLI flags.

    Supports: --ipp, --ipp-submit, --pivot, --pivot-scan, --storage,
              --firmware, --firmware-reset, --payload, --implant.
    """
    from utils.config import load_config
    load_config(path=getattr(args, 'config', None))

    target  = args.target
    timeout = 10.0

    # ── IPP audit ─────────────────────────────────────────────────────────────
    if getattr(args, 'ipp', False):
        output().green(f"\n>> IPP Security Audit: {target}")
        try:
            from protocols.ipp_attacks import audit
            results = audit(target, timeout=timeout, verbose=True)
            if results['risk']:
                output().errmsg(f"[!] Risks found: {', '.join(results['risk'])}")
            else:
                output().green("[OK] No critical IPP vulnerabilities detected.")
        except Exception as exc:
            output().errmsg(f"IPP audit error: {exc}")

    # ── IPP job submission ─────────────────────────────────────────────────────
    if getattr(args, 'ipp_submit', False):
        dry = not getattr(args, 'no_dry', False)
        output().green(f"\n>> IPP Job Submission: {target} "
                       f"({'dry-run' if dry else 'LIVE — actual print'})")
        try:
            from protocols.ipp_attacks import discover_endpoints, submit_job
            eps = discover_endpoints(target, timeout)
            if not eps:
                output().errmsg("No IPP endpoint found")
            else:
                ep  = eps[0]
                res = submit_job(
                    target, ep['port'], ep['path'], ep['scheme'],
                    doc_fmt='image/pwg-raster', job_name='pentest-job',
                    dry_run=dry, timeout=timeout,
                )
                if res['accepted']:
                    output().errmsg(f"[!] Anonymous print ACCEPTED: {res['message']}")
                elif res['auth_required']:
                    output().green(f"[OK] Authentication required: {res['message']}")
                else:
                    output().warning(f"Result: {res['message']}")
        except Exception as exc:
            output().errmsg(f"IPP submit error: {exc}")

    # ── Pivot / lateral movement ───────────────────────────────────────────────
    if getattr(args, 'pivot', False):
        output().green(f"\n>> Lateral Movement / SSRF Pivot Audit: {target}")
        try:
            from protocols.ssrf_pivot import pivot_audit
            from protocols.ipp_attacks import discover_endpoints
            eps  = discover_endpoints(target, timeout)
            port = eps[0]['port'] if eps else 631
            path = eps[0]['path'] if eps else '/ipp/print'
            scheme = eps[0]['scheme'] if eps else 'https'
            results = pivot_audit(target, port, path, scheme, timeout, verbose=True)
            if results['risk']:
                output().errmsg(f"[!] Pivot risks: {', '.join(results['risk'])}")
                if results['internal_hosts']:
                    output().errmsg(
                        f"[!] Internal hosts reachable via SSRF: "
                        f"{', '.join(results['internal_hosts'])}"
                    )
            else:
                output().green("[OK] No SSRF pivot vectors confirmed.")
        except Exception as exc:
            output().errmsg(f"Pivot audit error: {exc}")

    # ── Pivot port scan ────────────────────────────────────────────────────────
    if getattr(args, 'pivot_scan', None):
        internal = args.pivot_scan
        output().green(f"\n>> SSRF Port Scan: {internal} via printer {target}")
        try:
            from protocols.ipp_attacks import discover_endpoints
            from protocols.ssrf_pivot import ssrf_port_scan
            eps    = discover_endpoints(target, timeout)
            port   = eps[0]['port'] if eps else 631
            path   = eps[0]['path'] if eps else '/ipp/print'
            scheme = eps[0]['scheme'] if eps else 'https'
            scan_results = ssrf_port_scan(
                target, port, path, internal,
                scheme=scheme, timeout=6, verbose=True,
            )
            open_ports = [p for p, s in scan_results.items() if s == 'open']
            if open_ports:
                output().errmsg(f"[!] Open ports on {internal}: {open_ports}")
            else:
                output().green(f"[OK] No open ports detected on {internal} via SSRF.")
        except Exception as exc:
            output().errmsg(f"Pivot scan error: {exc}")

    # ── Storage audit ─────────────────────────────────────────────────────────
    if getattr(args, 'storage', False):
        output().green(f"\n>> Printer Storage Audit: {target}")
        try:
            from protocols.storage import storage_audit
            results = storage_audit(target, timeout=timeout, verbose=True)
            if results['risk']:
                output().errmsg(f"[!] Storage risks: {'; '.join(results['risk'])}")
            else:
                output().green("[OK] No storage vulnerabilities found.")
        except Exception as exc:
            output().errmsg(f"Storage audit error: {exc}")

    # ── Firmware audit ────────────────────────────────────────────────────────
    if getattr(args, 'firmware', False):
        output().green(f"\n>> Firmware Security Audit: {target}")
        try:
            from protocols.firmware import firmware_audit
            results = firmware_audit(target, timeout=timeout, verbose=True)
            if results['risk']:
                output().errmsg(f"[!] Firmware risks: {', '.join(results['risk'])}")
            else:
                output().green("[OK] No firmware vulnerabilities found.")
        except Exception as exc:
            output().errmsg(f"Firmware audit error: {exc}")

    # ── Factory reset ─────────────────────────────────────────────────────────
    if getattr(args, 'firmware_reset', None):
        method = args.firmware_reset
        output().warning(f"\n[!] Factory reset via {method} on {target} — AUTHORIZED TARGET ONLY")
        try:
            from protocols.firmware import factory_reset
            ok = factory_reset(target, timeout=timeout, method=method, verbose=True)
            if ok:
                output().errmsg(f"[!] Factory reset command accepted via {method}")
            else:
                output().green(f"[OK] Reset command rejected or not supported")
        except Exception as exc:
            output().errmsg(f"Firmware reset error: {exc}")

    # ── Payload injection ─────────────────────────────────────────────────────
    if getattr(args, 'payload', None):
        spec = args.payload
        custom_data = getattr(args, 'payload_data', '')
        try:
            lang, kind = spec.split(':', 1)
        except ValueError:
            lang, kind = spec, 'info'
        output().green(f"\n>> Payload Injection: lang={lang} type={kind} target={target}")
        try:
            from protocols.firmware import make_payload
            payload = make_payload(lang, kind, custom_data)
            if not payload:
                output().warning(f"No payload generated for {lang}:{kind}")
            else:
                from utils.ports import PortConfig as _PC
                import socket as _sock
                _raw_port = _PC.resolve('raw')
                s = _sock.create_connection((target, _raw_port), timeout=timeout)
                s.sendall(payload)
                _sock.setdefaulttimeout(2)
                resp = b''
                try:
                    resp = s.recv(4096)
                except Exception:
                    pass
                s.close()
                output().green(f"[+] Payload sent ({len(payload)} bytes)")
                if resp:
                    output().message(f"    Response: {resp[:200]}")
        except Exception as exc:
            output().errmsg(f"Payload error: {exc}")

    # ── Persistent implant ────────────────────────────────────────────────────
    if getattr(args, 'implant', None):
        raw = args.implant
        output().warning(f"\n[!] Persistent implant on {target}: {raw}")
        try:
            pairs = dict(kv.split('=', 1) for kv in raw.split(',') if '=' in kv)
            from protocols.firmware import implant_config
            results = implant_config(
                target,
                smtp_host      = pairs.get('smtp_host', ''),
                smtp_email     = pairs.get('smtp_email', ''),
                ntp_host       = pairs.get('ntp_host', ''),
                dns_server     = pairs.get('dns', ''),
                snmp_community = pairs.get('snmp_community', ''),
                timeout=timeout, verbose=True,
            )
            for k, ok in results.items():
                status = '\033[1;31m[IMPLANTED]\033[0m' if ok else '[failed]'
                output().message(f"  {status} {k}")
        except Exception as exc:
            output().errmsg(f"Implant error: {exc}")

    # ── Exploit module handlers ────────────────────────────────────────────────

    # --xpl-list: list all exploits
    if getattr(args, 'xpl_list', False):
        try:
            from utils.exploit_manager import load_all_exploits, print_exploit_list
            src_filter = getattr(args, 'xpl_source', None)
            xpls = load_all_exploits(source_filter=src_filter)
            src_label  = f' [{src_filter}]' if src_filter else ''
            print_exploit_list(
                xpls,
                title=f'PrinterReaper Exploit Library{src_label} ({len(xpls)} exploits)'
            )
        except Exception as exc:
            output().errmsg(f"xpl-list error: {exc}")

    # --xpl-update: rebuild index
    if getattr(args, 'xpl_update', False):
        try:
            from utils.exploit_manager import load_all_exploits, update_index
            xpls = load_all_exploits()
            update_index(xpls)
            output().green(f"[+] Exploit index updated ({len(xpls)} exploits)")
        except Exception as exc:
            output().errmsg(f"xpl-update error: {exc}")

    # --xpl-fetch: download raw from ExploitDB
    if getattr(args, 'xpl_fetch', None):
        edb_id = args.xpl_fetch
        output().green(f"\n>> Fetching EDB-{edb_id} from exploit-db.com ...")
        try:
            from utils.exploit_manager import fetch_exploit_db_raw
            path = fetch_exploit_db_raw(edb_id)
            if path:
                output().green(f"[+] Saved to {path}")
            else:
                output().warning("Download failed — check EDB ID or connection")
        except Exception as exc:
            output().errmsg(f"xpl-fetch error: {exc}")

    # --xpl-check: check if target is vulnerable to specific exploit
    if getattr(args, 'xpl_check', None):
        xpl_id = args.xpl_check
        if not args.target:
            output().errmsg("--xpl-check requires a target IP/host")
        else:
            output().green(f"\n>> Exploit Check: {xpl_id} against {target}")
            try:
                from utils.exploit_manager import load_all_exploits
                xpls = {x.id.upper(): x for x in load_all_exploits()}
                xpl  = xpls.get(xpl_id.upper())
                if not xpl:
                    output().errmsg(f"Exploit '{xpl_id}' not found in xpl/. Run --xpl-list.")
                else:
                    output().message(f"  [{xpl.severity.upper()}] {xpl.title}")
                    vuln = xpl.check(target, timeout=timeout)
                    if vuln:
                        output().errmsg(f"[VULNERABLE] Target appears vulnerable to {xpl_id}")
                        output().message(f"  Run with --xpl-run {xpl_id} to exploit")
                    else:
                        output().green(f"[OK] Target does not appear vulnerable to {xpl_id}")
            except Exception as exc:
                output().errmsg(f"xpl-check error: {exc}")

    # --xpl-run: execute specific exploit
    if getattr(args, 'xpl_run', None):
        xpl_id  = args.xpl_run
        dry     = not getattr(args, 'no_dry', False)
        if not args.target:
            output().errmsg("--xpl-run requires a target IP/host")
        else:
            output().green(
                f"\n>> Running Exploit: {xpl_id} against {target} "
                f"[{'DRY-RUN' if dry else 'LIVE EXPLOIT'}]"
            )
            if not dry:
                output().warning(
                    "[!] LIVE mode — ensure explicit written authorization before proceeding."
                )
            try:
                from utils.exploit_manager import load_all_exploits, print_run_result
                xpls = {x.id.upper(): x for x in load_all_exploits()}
                xpl  = xpls.get(xpl_id.upper())
                if not xpl:
                    output().errmsg(f"Exploit '{xpl_id}' not found. Run --xpl-list.")
                else:
                    output().message(f"  Title    : {xpl.title}")
                    output().message(f"  CVE      : {xpl.cve or 'N/A'}")
                    output().message(f"  Severity : {xpl.severity.upper()} (CVSS {xpl.cvss})")
                    output().message(f"  Protocol : {xpl.protocol} port {xpl.port}")
                    result = xpl.run(target, timeout=timeout, dry_run=dry)
                    print_run_result(result, xpl_id)
            except Exception as exc:
                output().errmsg(f"xpl-run error: {exc}")

    # ── Brute-force login ─────────────────────────────────────────────────────
    if getattr(args, 'bruteforce', False):
        from modules.login_bruteforce import bruteforce as bf_run, print_report as bf_print
        from utils.wordlist_loader import get_default_wordlist_path, wordlist_stats

        # Resolve vendor: CLI override > auto-detect from scan
        bf_vendor = getattr(args, 'bf_vendor', None) or ''
        bf_serial = getattr(args, 'bf_serial', None) or ''
        bf_mac    = getattr(args, 'bf_mac', None) or ''
        bf_delay  = getattr(args, 'bf_delay', 0.3)
        bf_novary = getattr(args, 'bf_no_variations', False)

        # Auto-detect vendor from fingerprint if not overridden
        if not bf_vendor:
            try:
                from utils.banner_grabber import grab_all
                fp = grab_all(target, timeout=5, verbose=False)
                bf_vendor = (fp.make or '').lower().split()[0]
                if not bf_serial and fp.serial:
                    bf_serial = fp.serial
                output().message(f"  [bf] Auto-detected vendor: {bf_vendor or 'unknown'}")
                if bf_serial:
                    output().message(f"  [bf] Serial from scan: {bf_serial}")
            except Exception:
                pass

        if not bf_vendor:
            bf_vendor = 'generic'

        # --bf-wordlist: use as the credential source (replaces default wordlist)
        # --bf-cred: additional credentials prepended (highest priority)
        bf_wordlist = getattr(args, 'bf_wordlist', None)

        # Validate custom wordlist path
        if bf_wordlist:
            import os
            if not os.path.exists(bf_wordlist):
                output().warning(f"  [bf] Wordlist not found: {bf_wordlist}")
                bf_wordlist = None
            else:
                stats = wordlist_stats(bf_wordlist)
                total_entries = sum(stats.values())
                output().message(f"  [bf] Custom wordlist: {bf_wordlist} ({total_entries} entries)")
        else:
            # Show info about default wordlist
            default_wl = get_default_wordlist_path()
            if default_wl:
                stats = wordlist_stats(default_wl)
                total_entries = sum(stats.values())
                output().message(f"  [bf] Default wordlist: {default_wl} ({total_entries} entries)")
            else:
                output().warning("  [bf] No wordlist found — place printer_default_creds.txt in wordlists/")

        # Parse extra credentials from --bf-cred USER:PASS (prepended, highest priority)
        extra_creds = []
        for cred_str in getattr(args, 'bf_cred', []) or []:
            if ':' in cred_str:
                u, p = cred_str.split(':', 1)
                extra_creds.append((u, p if p else None))
            else:
                extra_creds.append((cred_str, None))

        if extra_creds:
            output().message(f"  [bf] Extra credentials (--bf-cred): {len(extra_creds)} entries")

        output().green(
            f"\n>> Brute Force Login: {target} | vendor={bf_vendor} | "
            f"serial={bf_serial or '?'} | variations={'off' if bf_novary else 'on'}"
        )

        report = bf_run(
            host              = target,
            vendor            = bf_vendor,
            serial            = bf_serial,
            mac               = bf_mac,
            open_ports        = None,
            delay             = bf_delay,
            enable_variations = not bf_novary,
            stop_on_first     = True,
            extra_creds       = extra_creds,
            wordlist_path     = bf_wordlist,  # None → use default wordlist automatically
            verbose           = True,
        )
        bf_print(report)

        # Write to log
        try:
            import pathlib, datetime
            log_dir = pathlib.Path('.log')
            log_dir.mkdir(exist_ok=True)
            with open(log_dir / 'terminal-output.log', 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.datetime.now().isoformat()}] "
                        f"bruteforce {target} vendor={bf_vendor} "
                        f"serial={bf_serial} found={len(report.found)}\n")
                for r in report.found:
                    f.write(f"  FOUND {r.protocol.upper()} {r.username!r}/{r.password_display()!r}\n")
        except Exception:
            pass

    # ── Full attack matrix campaign ────────────────────────────────────────────
    if getattr(args, 'attack_matrix', False):
        dry   = not getattr(args, 'no_dry', False)
        nm    = getattr(args, 'network_map', False)
        output().green(
            f"\n>> Attack Matrix Campaign: {target} "
            f"[{'DRY-RUN' if dry else 'LIVE EXPLOIT'}]"
        )
        if not dry:
            output().warning(
                "[!] LIVE EXPLOIT MODE — destructive actions WILL be executed. "
                "Ensure you have explicit written authorization."
            )
        try:
            # Quick banner grab to get printer context
            langs:   list = []
            ports:   list = []
            make_:   str  = ''
            model_:  str  = ''
            fw_:     str  = ''
            try:
                from utils.banner_grabber import grab_all
                fp = grab_all(target, timeout=timeout)
                langs  = fp.printer_langs
                ports  = fp.open_ports
                make_  = fp.make
                model_ = fp.model
                fw_    = fp.firmware_version
            except Exception:
                pass

            from core.attack_orchestrator import run_campaign, print_campaign_report
            report = run_campaign(
                host=target, make=make_, model=model_, firmware=fw_,
                printer_langs=langs, open_ports=ports,
                dry_run=dry, timeout=timeout,
                run_netmap=nm, verbose=True,
            )
            print_campaign_report(report)
        except Exception as exc:
            output().errmsg(f"Attack matrix error: {exc}")

    # ── Network map ────────────────────────────────────────────────────────────
    if getattr(args, 'network_map', False) and not getattr(args, 'attack_matrix', False):
        output().green(f"\n>> Network Map from Printer Perspective: {target}")
        try:
            from protocols.network_map import build_network_map, print_network_map
            nm = build_network_map(target, timeout=timeout, verbose=True)
            print_network_map(nm)
        except Exception as exc:
            output().errmsg(f"Network map error: {exc}")

    # ── XSP payload generation ────────────────────────────────────────────────
    if getattr(args, 'xsp', None):
        attack = args.xsp
        cb     = getattr(args, 'xsp_callback', '')
        output().green(
            f"\n>> Cross-Site Printing (XSP) Payload Generator: {target} [{attack}]"
        )
        try:
            from protocols.network_map import generate_xsp_payload
            from utils.ports import PortConfig as _PC2
            payloads = generate_xsp_payload(
                printer_ip=target, printer_port=_PC2.resolve('raw'),
                attack_type=attack, callback_url=cb, exfil_url=cb,
            )
            # Save HTML to .log/
            import os as _os
            log_dir = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), '.log'
            )
            _os.makedirs(log_dir, exist_ok=True)
            html_path = _os.path.join(log_dir, f'xsp_{attack}_{target}.html')
            with open(html_path, 'w', encoding='utf-8') as fh:
                fh.write(payloads['html'])
            js_path = _os.path.join(log_dir, f'xsp_{attack}_{target}.js')
            with open(js_path, 'w', encoding='utf-8') as fh:
                fh.write(payloads['javascript'])
            output().green(f"[+] XSP HTML payload  → {html_path}")
            output().green(f"[+] XSP JS payload    → {js_path}")
            output().message("\n[PostScript payload preview]")
            print(payloads['postscript'][:300])
        except Exception as exc:
            output().errmsg(f"XSP error: {exc}")


# --------------------------------------------------------------------------- #
# Banner
# --------------------------------------------------------------------------- #
def intro(quiet: bool) -> None:
    """Print the PrinterReaper banner (ASCII art on the left, project info on the right)."""
    if quiet:
        return

    # ASCII art for an MFP-style printer (left column)
    art = [
        "   _____________________________________________________________   ",
        "  /___________________________________________________________/|   ",
        " | |=========================================================| |   ",
        " | |                                                         | |   ",
        " | |  ____________   __________   ________________________   | |   ",
        " | | | [] [] []  | |  ________ | |  . . .  . . .  . . .  |   | |   ",
        " | | |___________| | |  ____  || |________________________|  | |   ",
        " | |---------------| | |____| || |-------------------------- | |   ",
        " | |  ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___    | |   ",
        " | | |___|___|___|___|___|___|___|___|___|___|___|___|___|   | |   ",
        " | |_________________________________________________________| |   ",
        " | |-------------------  OUTPUT TRAY  ---------------------- | |   ",
        " | |_________________________________________________________|/|   ",
        " |  ______________________   ___________________________       |   ",
        " | |                     |   |                          |      |   ",
        " | |      PAPER BIN      |   |      SUPPLY DRAWER       |      |   ",
        " | |_____________________|   |__________________________|      |   ",
        " |___________________________________________________________|/   ",
        "|___________________[====   PAPER   ====]___________________/   ",
        "",
    ]

    # Project information (right column)
    info = [
        "",
        "",
        "",
        "",
        "",
        f"{APP_NAME} :: Advanced Printer Penetration Testing Toolkit",
        f"Version {VERSION}",
        "Author : Andre Henrique",
        "Contact: X / LinkedIn @mrhenrike",
        "",
        "feast on paper, harvest vulnerabilities",
        "",
        "(ASCII art by ChatGPT)",
    ]

    gap = 4  # spaces between the two columns
    art_width = max(len(line) for line in art)

    for left, right in zip_longest(art, info, fillvalue=""):
        print(f"{left:<{art_width}}{' ' * gap}{right}")

# --------------------------------------------------------------------------- #
# Main logic
# --------------------------------------------------------------------------- #
def main() -> None:
    """Main program flow."""
    # If called without any arguments → interactive guided menu
    if len(sys.argv) == 1:
        try:
            from ui.interactive import run_interactive
            run_interactive()
        except KeyboardInterrupt:
            print()
        sys.exit(0)

    args = get_args()

    # Handle discovery shortcuts that do not require positionals
    if args.discover_local:
        # 1. Show locally installed printers on this host
        try:
            from utils.local_printers import discover_local_installed, print_local_printers
            output().green("\n>> Locally Installed Printers (this host):")
            local_printers = discover_local_installed()
            print_local_printers(local_printers)
        except Exception as exc:
            output().errmsg(f"Local printer enumeration failed: {exc}")

        # 2. SNMP network scan for printers on reachable subnets
        output().green(">> Network Discovery (SNMP scan):")
        discovery(usage=True)
        sys.exit(0)

    # ── Load config first (honors --config flag) ─────────────────────────────
    try:
        from utils.config import load_config, check_all_features, require_feature
        load_config(path=getattr(args, 'config', None))
    except Exception as _cfg_err:
        pass  # config is optional — tool runs without it

    # ── Apply custom port overrides globally (must happen before any module connects)
    try:
        from utils.ports import PortConfig
        PortConfig.configure_from_args(args)
    except Exception:
        pass

    # ── --check-config: print feature availability and exit ───────────────────
    if getattr(args, 'check_config', False):
        try:
            from utils.config import check_all_features
            check_all_features(print_report=True)
        except Exception as exc:
            print(f"[!] {exc}")
        sys.exit(0)

    if args.discover_online:
        try:
            from utils.discovery_online import OnlineDiscoveryManager, DiscoveryParams
            from utils.config import (shodan_key as _sk, censys_credentials as _cc,
                                       fofa_credentials as _fc, zoomeye_key as _zk,
                                       netlas_key as _nk)

            # Build DiscoveryParams from --dork-* CLI flags
            dork_params = DiscoveryParams(
                vendors   = getattr(args, 'dork_vendors',   []) or [],
                model     = getattr(args, 'dork_model',     None),
                countries = getattr(args, 'dork_countries', []) or [],
                city      = getattr(args, 'dork_city',      None),
                regions   = getattr(args, 'dork_regions',   []) or [],
                ports     = getattr(args, 'dork_ports',     []) or [],
                org       = getattr(args, 'dork_org',       None),
                cpe       = getattr(args, 'dork_cpe',       None),
                limit     = getattr(args, 'dork_limit',     100),
            )

            # Enforce: at least one dork filter required when no IP target given
            if not dork_params.has_filters() and not getattr(args, 'target', None):
                output().errmsg(
                    "--discover-online requires at least one filter:\n"
                    "  --dork-vendor VENDOR     (e.g. hp, epson, ricoh)\n"
                    "  --dork-country COUNTRY   (e.g. BR, brazil, argentina)\n"
                    "  --dork-region REGION     (e.g. latin_america, europe)\n"
                    "  --dork-port PORT         (e.g. 9100, 515, 631)\n"
                    "  --dork-city CITY         (e.g. 'Sao Paulo')\n"
                    "  --dork-org ORG           (e.g. 'Telefonica')\n"
                    "  --dork-cpe CPE           (Censys/Netlas only)\n"
                    "  --dork-model MODEL       (e.g. 'deskjet pro 5500')\n\n"
                    "Or provide a direct IP target: python printer-reaper.py <IP> --scan"
                )
                sys.exit(1)

            # Parse --dork-engine whitelist
            _engine_arg = getattr(args, 'dork_engine', None)
            _engines    = [e.strip().lower() for e in _engine_arg.split(',') if e.strip()] \
                          if _engine_arg else None

            # Validate engine names
            _VALID_ENGINES = {'shodan', 'censys', 'fofa', 'zoomeye', 'netlas'}
            if _engines:
                _bad = [e for e in _engines if e not in _VALID_ENGINES]
                if _bad:
                    output().errmsg(
                        f"Unknown engine(s): {', '.join(_bad)}\n"
                        f"Valid choices: {', '.join(sorted(_VALID_ENGINES))}"
                    )
                    sys.exit(1)

            # Load credentials for all engines
            try:
                _shodan_key = _sk()
            except Exception:
                _shodan_key = None
            try:
                _cid, _csec = _cc()
            except Exception:
                _cid, _csec = None, None
            try:
                _femail, _fkey = _fc()
            except Exception:
                _femail, _fkey = None, None
            try:
                _zykey = _zk()
            except Exception:
                _zykey = None
            try:
                _nlkey = _nk()
            except Exception:
                _nlkey = None

            mgr  = OnlineDiscoveryManager(
                shodan_key    = _shodan_key,
                censys_id     = _cid,
                censys_secret = _csec,
                fofa_email    = _femail,
                fofa_key      = _fkey,
                zoomeye_key   = _zykey,
                netlas_key    = _nlkey,
            )
            hits = mgr.targeted_search(dork_params, engines=_engines)
            mgr.print_results(hits)
            saved = mgr.export_results(hits)
            if saved:
                output().green(f"[+] Next: python printer-reaper.py <IP> --scan  (test an individual target)")

        except SystemExit:
            pass
        except Exception as e:
            output().errmsg(f"Online discovery failed: {e}")
        finally:
            sys.exit(0)

    # ── --interactive: always launch guided menu ──────────────────────────────
    if getattr(args, 'interactive', False):
        try:
            from ui.interactive import run_interactive
            run_interactive()
        except KeyboardInterrupt:
            print()
        sys.exit(0)

    # ── --xpl-list / --xpl-update / --xpl-fetch (no target needed) ─────────
    if getattr(args, 'xpl_list', False):
        try:
            from utils.exploit_manager import load_all_exploits, print_exploit_list
            src_filter = getattr(args, 'xpl_source', None)
            xpls = load_all_exploits(source_filter=src_filter)
            src_label = f' [{src_filter}]' if src_filter else ''
            print_exploit_list(
                xpls,
                title=f'PrinterReaper Exploit Library{src_label} ({len(xpls)} exploits)'
            )
        except Exception as exc:
            output().errmsg(f"xpl-list error: {exc}")
        sys.exit(0)

    if getattr(args, 'xpl_update', False):
        try:
            from utils.exploit_manager import load_all_exploits, update_index
            xpls = load_all_exploits()
            update_index(xpls)
            output().green(f"[+] Exploit index updated ({len(xpls)} exploits)")
        except Exception as exc:
            output().errmsg(f"xpl-update error: {exc}")
        sys.exit(0)

    if getattr(args, 'xpl_fetch', None):
        edb_id = args.xpl_fetch
        output().green(f"\n>> Fetching EDB-{edb_id} from exploit-db.com ...")
        try:
            from utils.exploit_manager import fetch_exploit_db_raw
            path = fetch_exploit_db_raw(edb_id)
            if path:
                output().green(f"[+] Saved to {path}")
            else:
                output().warning("Download failed — check EDB ID or connection")
        except Exception as exc:
            output().errmsg(f"xpl-fetch error: {exc}")
        sys.exit(0)

    # ── --auto-exploit: automatic exploit selection, verification & execution ──
    if getattr(args, 'auto_exploit', False):
        if not getattr(args, 'target', None):
            output().errmsg("--auto-exploit requires a target IP: python printer-reaper.py <IP> --auto-exploit")
            sys.exit(1)
        _run_auto_exploit(args)
        sys.exit(0)

    # ── --send-job: send file/text to printer ────────────────────────────────
    if getattr(args, 'send_job', None):
        if not args.target:
            output().errmsg("--send-job requires a target: python src/main.py <ip> --send-job <file>")
            sys.exit(1)
        _run_send_job(args)
        sys.exit(0)

    # ── --scan / --scan-ml: reconnaissance without payloads ─────────────────
    scan_requested = getattr(args, 'scan', False) or getattr(args, 'scan_ml', False)
    if scan_requested:
        if not args.target:
            output().errmsg("--scan requires a target: python src/main.py <ip> --scan")
            sys.exit(1)
        _run_scan(args)
        sys.exit(0)

    # ── Attack / audit dispatchers ────────────────────────────────────────────
    _needs_target = ('ipp', 'ipp_submit', 'pivot', 'storage', 'firmware',
                     'firmware_reset', 'payload', 'implant',
                     'attack_matrix', 'network_map', 'xsp',
                     'xpl_check', 'xpl_run', 'bruteforce', 'auto_exploit')
    _any_attack = any(getattr(args, a.replace('-', '_'), None)
                      for a in _needs_target)
    if _any_attack:
        if not args.target:
            output().errmsg("Attack flags require a target IP/host.")
            sys.exit(1)
        _run_attack_modules(args)
        sys.exit(0)

    # Show banner first (respects --quiet).
    intro(args.quiet)

    # Verify host OS compatibility early.
    os_type = get_os()
    supported_os = ("linux", "windows", "wsl", "darwin", "bsd", "android")
    if os_type not in supported_os:
        output().errmsg(f"[!] Unsupported OS: {os_type!r}.")
        output().message("    This tool supports Linux, WSL, Windows, macOS, BSD, and Android (Termux).")
        sys.exit(1)

    # Show OS detection result in non-quiet mode
    if not args.quiet:
        os_names = {
            "linux":   "Linux",
            "wsl":     "Windows Subsystem for Linux (WSL)",
            "windows": "Windows",
            "darwin":  "macOS",
            "bsd":     "BSD",
            "android": "Android (Termux)",
        }
        output().message(f">> Detected OS: {os_names.get(os_type, os_type)}")

    # Basic startup message
    if not args.quiet:
        print()
        output().green(f">> Starting {APP_NAME} (Advanced Printer Penetration Testing)")
        print()

    # ── No meaningful args → launch interactive guided menu ──────────────────
    if not args.target and not args.mode:
        try:
            from ui.interactive import run_interactive
            run_interactive()
        except KeyboardInterrupt:
            print()
        sys.exit(0)

    # Auto-detect printer language support if mode is 'auto'
    if args.mode == 'auto':
        output().info("Auto-detecting printer language support...")
        # Try to detect via capabilities
        cap = capabilities(args)
        
        # Priority: PJL > PostScript > PCL
        if cap.support:
            if 'PJL' in str(cap.support):
                args.mode = 'pjl'
                output().info("✅ PJL support detected. Using PJL mode")
            elif 'PostScript' in str(cap.support) or 'PS' in str(cap.support):
                args.mode = 'ps'
                output().info("✅ PostScript support detected. Using PS mode")
            elif 'PCL' in str(cap.support):
                args.mode = 'pcl'
                output().info("✅ PCL support detected. Using PCL mode")
            else:
                output().warning("⚠️  Unknown language detected. Defaulting to PJL")
                args.mode = 'pjl'
        else:
            # Fallback to PJL
            output().warning("⚠️  Could not detect language. Defaulting to PJL")
            args.mode = 'pjl'

    # Capability auto-detection (e.g., SNMP, USB IDs, PJL INFO, etc.)
    capabilities(args)

    # Map language option to the corresponding interactive shell class.
    shell_map: Dict[str, Callable[[argparse.Namespace], object]] = {
        "pjl": pjl,
        "ps": ps,
        "pcl": pcl,
    }

    # Instantiate and run the chosen shell.
    shell_class = shell_map[args.mode]
    shell = shell_class(args)
    
    # Only enter interactive loop if not exiting from loaded commands
    if not shell.should_exit:
        shell.cmdloop()

# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        output().warning("[!] Execution interrupted by user.")
        print()
        sys.exit(0)
