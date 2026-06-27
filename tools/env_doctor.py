#!/usr/bin/env python3
# Author: André Henrique (@mrhenrike) | União Geek — https://github.com/Uniao-Geek
"""Environment diagnostics for PrinterXPL-Forge."""

from __future__ import annotations

import argparse
import importlib
import os
import platform
import shutil
import sys
from typing import Dict, List, Tuple

REQUIRED_DEPS: Tuple[Tuple[str, str], ...] = (
    ("requests", "requests"),
    ("urllib3", "urllib3"),
    ("colorama", "colorama"),
    ("pysnmp-lextudio", "pysnmp"),
    ("pyasn1", "pyasn1"),
    ("PyYAML", "yaml"),
)

OPTIONAL_DEPS: Tuple[Tuple[str, str, str], ...] = (
    ("pysmb", "pysmb", "SMB protocol modules"),
    ("impacket", "impacket", "SMB/Kerberos modules"),
    ("shodan", "shodan", "OSINT discovery"),
    ("censys", "censys", "OSINT discovery"),
    ("scikit-learn", "sklearn", "ML ranking"),
    ("joblib", "joblib", "ML models"),
)

OPTIONAL_BINARIES: Tuple[Tuple[str, str], ...] = (
    ("nmap", "Port scan (recommended for WAN/filtered targets)"),
    ("snmpget", "SNMP fingerprint fallback"),
)

CORE_SUBSYSTEMS: Tuple[Tuple[str, str], ...] = (
    ("core.osdetect", "OS detection"),
    ("core.discovery", "Network discovery"),
    ("core.capabilities", "Printer capabilities"),
    ("utils.exploit_manager", "Exploit manager"),
)


def _check_import(import_name: str) -> Tuple[bool, str]:
    try:
        mod = importlib.import_module(import_name)
        return True, str(getattr(mod, "__version__", "n/a"))
    except Exception as exc:
        return False, str(exc)


def _count_modules() -> Dict[str, int]:
    root = os.path.dirname(os.path.dirname(__file__))
    base = os.path.join(root, "src", "modules")
    counts: Dict[str, int] = {}
    if not os.path.isdir(base):
        return counts
    for category in sorted(os.listdir(base)):
        cat_path = os.path.join(base, category)
        if not os.path.isdir(cat_path):
            continue
        total = sum(
            1
            for f in os.listdir(cat_path)
            if f.endswith(".py") and f != "__init__.py"
        )
        if total:
            counts[category] = total
    xpl = os.path.join(root, "xpl")
    if os.path.isdir(xpl):
        n = sum(1 for d in os.listdir(xpl) if os.path.isdir(os.path.join(xpl, d)))
        if n:
            counts["xpl"] = n
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="PrinterXPL-Forge environment diagnostics")
    parser.add_argument("-q", "--quiet", action="store_true", help="Exit code only")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(__file__))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    if args.quiet:
        code = 0
        for _, imp in REQUIRED_DEPS:
            if not _check_import(imp)[0]:
                code = 2
        for mod, _ in CORE_SUBSYSTEMS:
            if not _check_import(mod)[0]:
                code = 2
        return code

    _W, _E, _G, _R, _B = "\033[33m", "\033[31m", "\033[32m", "\033[0m", "\033[1m"
    try:
        import colorama
        colorama.init()
    except ImportError:
        _W = _E = _G = _R = _B = ""

    print("{}PrinterXPL-Forge — Environment Doctor{}".format(_B, _R))
    print("python  = {}".format(platform.python_version()))
    print("exe     = {}".format(sys.executable))
    print()

    exit_code = 0
    print("{}___ Required ___{}".format(_B, _R))
    for pkg, imp in REQUIRED_DEPS:
        ok, info = _check_import(imp)
        mark = "{}OK{}".format(_G, _R) if ok else "{}FAIL{}".format(_E, _R)
        print("  [{}] {:22s} {}".format(mark, pkg, info if ok else info[:50]))
        if not ok:
            exit_code = 2

    print("\n{}___ Optional ___{}".format(_B, _R))
    for pkg, imp, desc in OPTIONAL_DEPS:
        ok, info = _check_import(imp)
        mark = "{}OK{}".format(_G, _R) if ok else "{}WARN{}".format(_W, _R)
        print("  [{}] {:22s} ({})".format(mark, pkg, desc))
        if not ok and exit_code == 0:
            exit_code = 1

    print("\n{}___ System tools ___{}".format(_B, _R))
    for binary, desc in OPTIONAL_BINARIES:
        ok = bool(shutil.which(binary))
        mark = "{}OK{}".format(_G, _R) if ok else "{}WARN{}".format(_W, _R)
        print("  [{}] {:22s} ({})".format(mark, binary, desc))
        if not ok and binary == 'nmap' and exit_code == 0:
            exit_code = 1

    print("\n{}___ Core subsystems ___{}".format(_B, _R))
    for mod, desc in CORE_SUBSYSTEMS:
        ok, _ = _check_import(mod)
        mark = "{}OK{}".format(_G, _R) if ok else "{}FAIL{}".format(_E, _R)
        print("  [{}] {} ({})".format(mark, mod, desc))
        if not ok:
            exit_code = 2

    counts = _count_modules()
    total = sum(counts.values())
    print("\n{}___ Modules ___{}".format(_B, _R))
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print("  {:12s} {:4d}".format(cat, n))
    print("  Total: {:,}".format(total))

    print("\n{}___ Summary ___{}".format(_B, _R))
    if exit_code == 0:
        print("  {}HEALTHY{}".format(_G, _R))
    elif exit_code == 1:
        print("  {}DEGRADED (optional deps missing){}".format(_W, _R))
    else:
        print("  {}BROKEN — run ./setup_venv.sh{}".format(_E, _R))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
