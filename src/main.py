#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper - Advanced Printer Penetration Testing Toolkit
Main entry point.
"""

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
    # Discovery helpers
    parser.add_argument(
        "--discover-local",
        action="store_true",
        help="Run local SNMP discovery to find printers on your networks",
    )
    parser.add_argument(
        "--discover-online",
        action="store_true",
        help="Run online discovery via Shodan/Censys (requires API keys in config.yaml)",
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
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Show which API features are configured and exit",
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

    output().green(f"\n>> Reconnaissance scan: {target}")
    print()

    # 1. Banner grab
    fp = grab_all(target, timeout=timeout, verbose=True)
    print_fingerprint(fp)

    # 2. CVE / vuln scan
    output().green(">> Vulnerability Assessment:")
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

    # 3. Optional ML analysis
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
    # If called without any arguments, show an extended help/quick-start
    if len(sys.argv) == 1:
        parser = build_parser()
        parser.print_help()
        print()
        print("Quick Start:")
        print("  python src/main.py 15.204.211.244 auto --safe   # Auto-detect language and run")
        print("  python src/main.py 15.204.211.244 pjl            # Force PJL shell")
        print("  python src/main.py 15.204.211.244 ps             # Force PostScript shell")
        print("  python src/main.py 15.204.211.244 pcl            # Force PCL shell")
        print()
        print("Discovery:")
        print("  python src/main.py --discover-local               # SNMP scan local networks")
        print("  python -m src.utils.discovery_online              # Online discovery (Shodan/Censys)")
        print("       or: python src/main.py --discover-online")
        print()
        print("Examples:")
        print("  printerreaper 15.204.211.244 auto --debug --log session.log")
        print("  printerreaper 192.168.1.100 pjl -s -o raw.log")
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
            from utils.config import shodan_key, require_feature
            if not require_feature('shodan_search'):
                sys.exit(1)
            from utils.discovery_online import OnlineDiscoveryManager
            mgr = OnlineDiscoveryManager(shodan_key=shodan_key())
            mgr.discover(max_results_per_query=25)
            mgr.export_results()
        except SystemExit:
            pass
        except Exception as e:
            output().errmsg(f"Online discovery failed: {e}")
        finally:
            sys.exit(0)

    # ── --scan / --scan-ml: reconnaissance without payloads ─────────────────
    scan_requested = getattr(args, 'scan', False) or getattr(args, 'scan_ml', False)
    if scan_requested:
        if not args.target:
            output().errmsg("--scan requires a target: python src/main.py <ip> --scan")
            sys.exit(1)
        _run_scan(args)
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

    # Validate required positionals (unless using discovery flags)
    if not args.target or not args.mode:
        parser = build_parser()
        parser.print_help()
        print()
        print("Tip: Use --discover-local or --discover-online for discovery workflows.")
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
