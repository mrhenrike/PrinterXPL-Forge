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
        help="Run online discovery via Shodan/Censys (requires API keys)",
    )
    return parser


def get_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = build_parser()
    return parser.parse_args()
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program version and exit",
    )
    return parser.parse_args()


from itertools import zip_longest

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
        discovery(usage=True)
        sys.exit(0)

    if args.discover_online:
        try:
            from utils.discovery_online import OnlineDiscoveryManager
            mgr = OnlineDiscoveryManager()
            mgr.discover(max_results_per_query=25)
            mgr.export_results()
        except Exception as e:
            output().errmsg(f"Online discovery failed: {e}")
        finally:
            sys.exit(0)

    # Show banner first (respects --quiet).
    intro(args.quiet)

    # Verify host OS compatibility early.
    os_type = get_os()
    supported_os = ("linux", "windows", "wsl", "darwin", "bsd")
    if os_type not in supported_os:
        output().errmsg(f"[!] Unsupported OS: {os_type!r}.")
        output().message("    This tool currently supports Linux, WSL, Windows, macOS, and BSD.")
        sys.exit(1)
    
    # Show OS detection result in non-quiet mode
    if not args.quiet:
        os_names = {
            "linux": "Linux",
            "wsl": "Windows Subsystem for Linux (WSL)",
            "windows": "Windows",
            "darwin": "macOS",
            "bsd": "BSD"
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
