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
from core.language_detector import LanguageDetector
from modules.pjl import pjl
from modules.postscript import postscript
from modules.pcl import pcl
from utils.helper import output

# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
APP_NAME: str = "PrinterReaper"
VERSION: str = "1.0.0"

# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def get_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME.lower(),
        description=f"{APP_NAME} - Advanced Printer Penetration Testing Toolkit",
    )
    parser.add_argument("target", help="Printer IP address or hostname")
    parser.add_argument(
        "mode",
        choices=["ps", "pjl", "pcl", "auto"],
        help="Printer language to abuse (PostScript, PJL, PCL, or auto-detect)",
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
        f"{APP_NAME} :: Vulnerability & Offensive Intrusion Device for PRINTers",
        f"Version {VERSION}",
        "Author : Andre Henrique",
        "Contact: X / LinkedIn @mrhenrike",
        "",
        "「 feast on paper, harvest vulnerabilities 」",
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
    # If called without any arguments, drop to printer discovery helper.
    if len(sys.argv) == 1:
        discovery(usage=True)
        sys.exit(0)

    args = get_args()

    # Show banner first (respects --quiet).
    intro(args.quiet)

    # Verify host OS compatibility early.
    os_type = get_os()
    if os_type not in ("linux", "windows", "wsl"):
        output().errmsg(f"[!] Unsupported OS: {os_type!r}.")
        output().message("    This tool currently supports Linux, WSL or Windows only.")
        sys.exit(1)

    # Basic startup message
    if not args.quiet:
        print()
        output().green(f">> Starting {APP_NAME} (Advanced Printer Penetration Testing)")
        print()

    # Auto-detect supported languages if requested or mode is 'auto'
    if args.auto_detect or args.mode == 'auto':
        detector = LanguageDetector(args.target)
        supported_languages = detector.detect_languages()
        detector.print_summary()
        
        if not supported_languages:
            output().red("No supported languages detected. Exiting.")
            sys.exit(1)
            
        # Use recommended language or first available
        recommended = detector.get_recommended_language()
        if recommended:
            args.mode = recommended
            output().info(f"Using recommended language: {recommended.upper()}")
        else:
            args.mode = supported_languages[0]
            output().info(f"Using first available language: {args.mode.upper()}")

    # Capability auto-detection (e.g., SNMP, USB IDs, PJL INFO, etc.)
    capabilities(args)

    # Map language option to the corresponding interactive shell class.
    shell_map: Dict[str, Callable[[argparse.Namespace], object]] = {
        "ps": postscript,
        "pjl": pjl,
        "pcl": pcl,
    }

    # Instantiate and run the chosen shell.
    shell_class = shell_map[args.mode]
    shell = shell_class(args)
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
