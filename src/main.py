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
def get_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME.lower(),
        description=f"{APP_NAME} - Advanced Printer Penetration Testing Toolkit",
    )
    parser.add_argument("target", help="Printer IP address or hostname")
    parser.add_argument(
        "mode",
        choices=["pjl", "auto"],
        help="Printer language to abuse (PJL or auto-detect)",
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
    # If called without any arguments, drop to printer discovery helper.
    if len(sys.argv) == 1:
        discovery(usage=True)
        sys.exit(0)

    args = get_args()

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

    # Auto-detect PJL support if mode is 'auto'
    if args.mode == 'auto':
        output().info("Auto-detecting PJL support...")
        # Simple PJL detection - try to connect and check for PJL support
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((args.target, 9100))
            sock.close()
            
            if result == 0:
                args.mode = 'pjl2'  # Default to PJL v2.0
                output().info("PJL support detected. Using PJL v2.0")
            else:
                output().red("No PJL support detected. Exiting.")
                sys.exit(1)
        except Exception as e:
            output().red(f"Auto-detection failed: {e}")
            sys.exit(1)

    # Capability auto-detection (e.g., SNMP, USB IDs, PJL INFO, etc.)
    capabilities(args)

    # Map language option to the corresponding interactive shell class.
    shell_map: Dict[str, Callable[[argparse.Namespace], object]] = {
        "pjl": pjl,
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
