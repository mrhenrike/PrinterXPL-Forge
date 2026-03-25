#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Interactive Guided CLI
=======================================
Provides a guided menu-driven interface for operators who prefer
not to memorize CLI flags. Every option maps directly to a CLI
command shown on screen before execution.

Launch: python src/main.py  (no arguments)
        python src/main.py --interactive
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import textwrap
from typing import List, Optional, Tuple

# ── ANSI palette ──────────────────────────────────────────────────────────────
_RST = '\033[0m'
_BLD = '\033[1m'
_DIM = '\033[2;37m'
_CYN = '\033[1;36m'
_GRN = '\033[1;32m'
_YEL = '\033[1;33m'
_RED = '\033[1;31m'
_MGT = '\033[1;35m'
_BLU = '\033[1;34m'
_WHT = '\033[1;37m'

W = shutil.get_terminal_size((80, 24)).columns

# ── Session state (persists across menu actions) ──────────────────────────────
_session: dict = {
    'target': '',
    'vendor': '',
    'serial': '',
}


# ── Low-level I/O helpers ────────────────────────────────────────────────────

def _clr() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def _hr(char: str = '─', color: str = _DIM) -> None:
    print(f"  {color}{char * min(64, W - 4)}{_RST}")


def _ask(prompt: str, default: str = '') -> str:
    """Prompt for input, returning default on blank enter."""
    hint = f" [{_DIM}{default}{_RST}]" if default else ''
    try:
        val = input(f"  {_CYN}?{_RST} {prompt}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return val or default


def _ask_yn(prompt: str, default: bool = False) -> bool:
    hint = f"[{_GRN}Y{_RST}/{_DIM}n{_RST}]" if default else f"[{_DIM}y{_RST}/{_GRN}N{_RST}]"
    try:
        val = input(f"  {_CYN}?{_RST} {prompt} {hint}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not val:
        return default
    return val.startswith('y')


def _choose(options: List[Tuple[str, str]], title: str = '',
            allow_back: bool = True) -> Optional[str]:
    """
    Display numbered menu and return the selected key.

    Args:
        options: List of (key, label) pairs.
        title:   Section title.
        allow_back: Whether to add a [B]ack/[Q]uit option.
    Returns:
        key string, or None if user chose back/quit.
    """
    if title:
        print(f"\n  {_CYN}{_BLD}{title}{_RST}")
        _hr()

    for i, (key, label) in enumerate(options, 1):
        print(f"  {_YEL}[{i}]{_RST}  {label}")

    if allow_back:
        print(f"\n  {_DIM}[0]  ← Back / Main menu{_RST}")

    print()
    while True:
        try:
            raw = input(f"  {_CYN}▶{_RST} Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if raw in ('0', 'b', 'B', 'q', 'Q', ''):
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print(f"  {_DIM}  Invalid choice — try again{_RST}")


def _print_cmd(cmd: List[str]) -> None:
    """Show the equivalent CLI command before execution."""
    print()
    print(f"  {_DIM}Running command:{_RST}")
    print(f"  {_BLU}$  python src/main.py {' '.join(cmd)}{_RST}")
    print()


def _run_cmd(cmd: List[str], pause: bool = True) -> None:
    """Execute a main.py command in subprocess and show output."""
    _print_cmd(cmd)
    py = sys.executable
    full = [py, '-W', 'ignore', 'src/main.py'] + cmd
    try:
        subprocess.run(full, check=False)
    except KeyboardInterrupt:
        print(f"\n  {_YEL}[!] Interrupted{_RST}")
    if pause:
        print()
        try:
            input(f"  {_DIM}Press Enter to continue...{_RST}")
        except (EOFError, KeyboardInterrupt):
            pass


# ── Sections ──────────────────────────────────────────────────────────────────

def _banner_mini() -> None:
    """Compact banner for interactive mode."""
    from version import __version__, __release_date__
    print()
    print(f"  {_RED}██████{_RST}{_WHT}╗ {_RED}███████╗{_RST}{_WHT}╗{_RST}  PrinterReaper  "
          f"{_DIM}v{__version__} ({__release_date__}){_RST}")
    print(f"  {_RED}██╔══██{_RST}{_WHT}╗{_RED}██╔════╝{_RST}  "
          f"{_DIM}Advanced Printer Penetration Testing{_RST}")
    print(f"  {_RED}██████╔╝{_RED}█████╗  {_RST}  "
          f"{_DIM}@mrhenrike · linkedin.com/in/mrhenrike{_RST}")
    print()
    _hr('═', _CYN)
    print()


def _target_prompt(current: str = '') -> str:
    """Ask for target IP/hostname, reusing the session target if already set.

    If a target was used in a previous menu action this session, it becomes
    the default — the user can press Enter to confirm it, or type a new one.
    """
    effective = current or _session.get('target', '')
    while True:
        t = _ask("Target IP or hostname", effective or '192.168.x.x')
        if t and t not in ('192.168.x.x', ''):
            _session['target'] = t
            return t
        print(f"  {_DIM}  Please enter a valid IP or hostname{_RST}")


def _serial_prompt() -> str:
    val = _ask("Serial number (leave blank if unknown)", _session.get('serial', ''))
    if val:
        _session['serial'] = val
    return val


def _vendor_prompt(auto: str = '') -> str:
    hint = auto or _session.get('vendor', '') or 'epson'
    val = _ask(
        "Printer vendor (epson/hp/ricoh/xerox/kyocera/brother/canon/generic)",
        hint,
    )
    if val:
        _session['vendor'] = val
    return val


# ── Menu sections ─────────────────────────────────────────────────────────────

def _menu_discover() -> None:
    choice = _choose([
        ('local',  'Local network discovery  (SNMP scan — finds printers on LAN)'),
        ('online', 'Online discovery         (Shodan/Censys — requires API keys)'),
        ('local_installed', 'Locally installed printers (installed on this machine/OS)'),
    ], title='Discover Printers')
    if choice is None:
        return

    if choice == 'local':
        _run_cmd(['--discover-local'])
    elif choice == 'online':
        _run_cmd(['--discover-online'])
    elif choice == 'local_installed':
        _run_cmd(['--discover-local'])


def _menu_scan() -> None:
    target = _target_prompt()
    choice = _choose([
        ('quick',  'Quick scan     (banner + CVEs, no NVD API — fast, offline)'),
        ('full',   'Full scan      (banner + NVD CVE lookup + exploit matching)'),
        ('ml',     'Full + ML scan (full + ML-assisted fingerprint & scoring)'),
    ], title=f'Scan  →  {target}', allow_back=True)
    if choice is None:
        return

    if choice == 'quick':
        _run_cmd([target, '--scan', '--no-nvd'])
    elif choice == 'full':
        _run_cmd([target, '--scan'])
    elif choice == 'ml':
        _run_cmd([target, '--scan-ml'])


def _menu_bruteforce() -> None:
    target = _target_prompt()
    print()
    print(f"  {_DIM}Brute-force tests default vendor credentials against HTTP, FTP, SNMP, Telnet.{_RST}")
    print(f"  {_DIM}Password variations generated: normal, reverse, leet, CamelCase, UPPER, lower.{_RST}")
    print()

    vendor = _vendor_prompt()
    serial = _serial_prompt()
    mac    = _ask("MAC address (for OKI/Brother/Kyocera KR2 — leave blank if unknown)", '')
    delay  = _ask("Delay between attempts in seconds (0.3 = default, increase to avoid lockouts)", '0.3')
    variations = _ask_yn("Enable password variations (reverse, leet, CamelCase...)?", True)

    cmd = [target, '--bruteforce', '--bf-vendor', vendor]
    if serial:
        cmd += ['--bf-serial', serial]
    if mac:
        cmd += ['--bf-mac', mac]
    if delay and delay != '0.3':
        cmd += ['--bf-delay', delay]
    if not variations:
        cmd.append('--bf-no-variations')

    _run_cmd(cmd)


def _menu_attack() -> None:
    target = _target_prompt()
    choice = _choose([
        ('ipp',     'IPP attacks         (job submit/purge, queue dump, attr manipulation)'),
        ('matrix',  'Full attack matrix  (BlackHat 2017 + 2024-2025 CVEs — all categories)'),
        ('pivot',   'Network pivot       (SSRF internal host discovery, port scan via printer)'),
        ('storage', 'Storage access      (FTP filesystem, web file mgr, SNMP MIB dump)'),
        ('firmware','Firmware audit      (version, upload check, NVRAM probe)'),
        ('xsp',     'Cross-Site Printing (XSP + CORS spoofing payload generator)'),
        ('netmap',  'Network mapping     (subnet scan, SNMP routing, WSD neighbors)'),
        ('payload', 'Inject payload      (PJL/PS/ESC-P payload, display message)'),
        ('implant', 'Persistent implant  (SMTP/DNS/NTP config change, NVRAM write)'),
    ], title=f'Attack  →  {target}', allow_back=True)
    if choice is None:
        return

    dry_note = (
        f"\n  {_YEL}[!]{_RST}  Default: DRY-RUN mode — no destructive actions.\n"
        f"  {_YEL}    {_RST}  Use --no-dry to execute live (authorized labs only).\n"
    )

    if choice == 'ipp':
        print(dry_note)
        _run_cmd([target, '--ipp'])

    elif choice == 'matrix':
        print(dry_note)
        nodry = _ask_yn("Enable LIVE mode (execute exploits, not just probe)?", False)
        cmd = [target, '--attack-matrix']
        if nodry:
            cmd.append('--no-dry')
        _run_cmd(cmd)

    elif choice == 'pivot':
        internal = _ask("Internal host to port-scan via printer SSRF (leave blank to skip)", '')
        cmd = [target, '--pivot']
        if internal:
            cmd += ['--pivot-scan', internal]
        _run_cmd(cmd)

    elif choice == 'storage':
        _run_cmd([target, '--storage'])

    elif choice == 'firmware':
        _run_cmd([target, '--firmware'])

    elif choice == 'xsp':
        xtype = _choose([
            ('info',    'info    — extract printer ID'),
            ('capture', 'capture — job sniffer'),
            ('dos',     'dos     — PS infinite loop via browser'),
            ('nvram',   'nvram   — NVRAM damage'),
            ('exfil',   'exfil   — exfiltrate captured jobs'),
        ], title='XSP Payload Type', allow_back=True)
        if xtype:
            callback = _ask("Exfiltration callback URL (optional)", '')
            cmd = [target, '--xsp', xtype]
            if callback:
                cmd += ['--xsp-callback', callback]
            _run_cmd(cmd)

    elif choice == 'netmap':
        _run_cmd([target, '--network-map'])

    elif choice == 'payload':
        lang = _choose([
            ('pjl:info',    'PJL info      — extract printer variables'),
            ('pjl:reset',   'PJL reset     — factory reset via PJL'),
            ('ps:custom',   'PS custom     — custom PostScript payload'),
            ('escpr:info',  'ESC/P info    — Epson ESC/P-R device info'),
        ], title='Payload Type', allow_back=True)
        if lang:
            _run_cmd([target, '--payload', lang])

    elif choice == 'implant':
        kv = _ask("Config to implant (e.g. smtp_host=attacker.com)", '')
        if kv:
            _run_cmd([target, '--implant', kv])


def _menu_send_job() -> None:
    """Send a print job (file or raw text) to a target printer."""
    target = _target_prompt()
    print()
    print(f"  {_DIM}Send any file or text directly to the printer for printing.{_RST}")
    print(f"  {_DIM}Supported: .txt, .pdf, .ps, .pcl, .png, .jpg, .doc — or raw text.{_RST}")
    print()
    choice = _choose([
        ('file',    'Send a file          (PDF, PS, PCL, PNG, JPG, TXT, DOC...)'),
        ('text',    'Send raw text        (type text directly, printer outputs it)'),
        ('ps',      'Send PostScript      (raw PS code — advanced)'),
    ], title=f'Send Print Job  ->  {target}', allow_back=True)
    if choice is None:
        return

    proto = _choose([
        ('raw',  'RAW / JetDirect     (port 9100 — fastest, no job tracking)'),
        ('ipp',  'IPP                 (port 631 — standard, job tracking)'),
        ('lpd',  'LPD                 (port 515 — legacy line printer)'),
    ], title='Printing Protocol', allow_back=True)
    if proto is None:
        return

    port_defaults = {'raw': '9100', 'ipp': '631', 'lpd': '515'}
    port = _ask(f"Port [{port_defaults.get(proto, '9100')}]", port_defaults.get(proto, '9100'))
    copies = _ask("Number of copies [1]", '1')

    if choice == 'file':
        path = _ask("File path (absolute or relative)", '')
        if not path:
            return
        cmd = [target, '--send-job', path, '--send-proto', proto, '--port', port]
        if copies and copies != '1':
            cmd += ['--send-copies', copies]
        _run_cmd(cmd)

    elif choice == 'text':
        print(f"  {_DIM}Type your text below. End with a blank line + Enter:{_RST}")
        lines = []
        try:
            while True:
                line = input()
                if line == '' and lines:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        if not lines:
            return
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                          delete=False, encoding='utf-8')
        tmp.write('\n'.join(lines) + '\n')
        tmp.close()
        cmd = [target, '--send-job', tmp.name, '--send-proto', proto, '--port', port]
        if copies and copies != '1':
            cmd += ['--send-copies', copies]
        _run_cmd(cmd)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    elif choice == 'ps':
        print(f"  {_DIM}Enter PostScript code (end with blank line):{_RST}")
        lines = []
        try:
            while True:
                line = input()
                if line == '' and lines:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        if not lines:
            return
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.ps',
                                          delete=False, encoding='utf-8')
        tmp.write('\n'.join(lines) + '\n')
        tmp.close()
        cmd = [target, '--send-job', tmp.name, '--send-proto', proto, '--port', port]
        _run_cmd(cmd)
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _menu_exploits() -> None:
    choice = _choose([
        ('list',   'List all exploits  (sorted by severity: critical → info)'),
        ('check',  'Check target       (non-destructive — is target vulnerable?)'),
        ('run',    'Run exploit        (dry-run by default)'),
        ('fetch',  'Download exploit   (fetch raw exploit from ExploitDB by ID)'),
        ('update', 'Update index       (rebuild xpl/index.json from loaded exploits)'),
    ], title='Exploit Library', allow_back=True)
    if choice is None:
        return

    if choice == 'list':
        _run_cmd(['--xpl-list'])

    elif choice == 'check':
        target = _target_prompt()
        print()
        print(f"  {_DIM}Run --xpl-list first to see available exploit IDs.{_RST}")
        xid = _ask("Exploit ID (e.g. EDB-15631, CVE-2025-26508)", '')
        if xid:
            _run_cmd([target, '--xpl-check', xid])

    elif choice == 'run':
        target = _target_prompt()
        print()
        print(f"  {_DIM}Run --xpl-list first to see available exploit IDs.{_RST}")
        xid = _ask("Exploit ID", '')
        if not xid:
            return
        nodry = _ask_yn(
            f"{_YEL}Enable LIVE mode?{_RST} (default: DRY-RUN — safe probe only)", False
        )
        cmd = [target, '--xpl-run', xid]
        if nodry:
            cmd.append('--no-dry')
        _run_cmd(cmd)

    elif choice == 'fetch':
        print(f"\n  {_DIM}Browse https://www.exploit-db.com/search for printer exploits.{_RST}")
        edb_id = _ask("ExploitDB numeric ID (e.g. 45273)", '')
        if edb_id:
            _run_cmd(['--xpl-fetch', edb_id])

    elif choice == 'update':
        _run_cmd(['--xpl-update'])


def _menu_config() -> None:
    choice = _choose([
        ('check',  'Check API configuration  (shows which features are active)'),
        ('help',   'Full help / all CLI flags'),
        ('about',  'About PrinterReaper'),
    ], title='Configuration & Help', allow_back=True)
    if choice is None:
        return

    if choice == 'check':
        _run_cmd(['--check-config'])
    elif choice == 'help':
        _run_cmd(['--help'])
    elif choice == 'about':
        _show_about()


def _show_about() -> None:
    print()
    print(f"  {_CYN}{'═'*60}{_RST}")
    print(f"  {_BLD}PrinterReaper — Advanced Printer Penetration Testing{_RST}")
    print(f"  {_CYN}{'═'*60}{_RST}")
    lines = [
        ('Author',    'Andre Henrique (@mrhenrike)'),
        ('GitHub',    'https://github.com/mrhenrike'),
        ('LinkedIn',  'https://linkedin.com/in/mrhenrike'),
        ('X',         'https://x.com/mrhenrike'),
        ('License',   'MIT'),
        ('Purpose',   'Authorized security testing of network printers'),
    ]
    for label, value in lines:
        print(f"  {_DIM}{label:<12}{_RST} {value}")
    print()
    try:
        input(f"  {_DIM}Press Enter to continue...{_RST}")
    except (EOFError, KeyboardInterrupt):
        pass


# ── Workflow shortcuts ────────────────────────────────────────────────────────

def _workflow_full_audit() -> None:
    """Guided full audit: scan + BF + exploit check in sequence."""
    print()
    print(f"  {_CYN}{_BLD}Full Audit Workflow{_RST}")
    print(f"  {_DIM}Runs: Scan → Exploit matching → Brute-force → Attack matrix{_RST}")
    _hr()
    target = _target_prompt()
    serial = _serial_prompt()
    vendor = _vendor_prompt()

    steps = [
        (f"Step 1/4  Scan (banner + CVEs)",
         [target, '--scan']),
        (f"Step 2/4  Brute-force login",
         [target, '--bruteforce', '--bf-vendor', vendor]
         + (['--bf-serial', serial] if serial else [])),
        (f"Step 3/4  Attack matrix (dry-run)",
         [target, '--attack-matrix']),
        (f"Step 4/4  Network map",
         [target, '--network-map']),
    ]

    for title, cmd in steps:
        print(f"\n  {_YEL}{'─'*54}{_RST}")
        print(f"  {_YEL}▶  {title}{_RST}")
        print(f"  {_YEL}{'─'*54}{_RST}")
        _run_cmd(cmd, pause=False)

    print(f"\n  {_GRN}Full audit complete.{_RST}")
    print(f"  {_DIM}Review results above. Re-run individual steps for deeper analysis.{_RST}")
    try:
        input(f"\n  {_DIM}Press Enter to return to main menu...{_RST}")
    except (EOFError, KeyboardInterrupt):
        pass


# ── Main interactive loop ─────────────────────────────────────────────────────

_MAIN_MENU = [
    ('discover',  '[~]  Discover printers       Find printers on LAN or via Shodan/Censys'),
    ('scan',      '[?]  Scan target             Fingerprint + CVE lookup + exploit matching'),
    ('bruteforce','[*]  Brute-force login       Test default credentials (all protocols)'),
    ('attack',    '[!]  Attack / Exploit        IPP, pivot, firmware, payload, XSP, matrix'),
    ('exploits',  '[X]  Exploit library         List, check, run or download exploits'),
    ('send',      '[>]  Send print job          Send text/doc/pdf/image to target printer'),
    ('workflow',  '[>>] Full audit workflow     Scan → BF → Attack matrix → Netmap in one go'),
    ('config',    '[=]  Config & help           API keys, settings, documentation'),
]


def _menu_header() -> None:
    from version import __version__
    print()
    _w   = 58  # inner box width (number of ═ chars)
    _ver = f"PrinterReaper v{__version__}"
    _sub = "Advanced Printer Penetration Testing Toolkit"
    _act = "Choose an action:"
    # Each content line: 2 leading spaces + text + padding + 2 trailing spaces = _w
    def _row(text: str, bold: str = '') -> str:
        pad = ' ' * (_w - 4 - len(text))
        inner = f"  {bold}{text}{_RST}{pad}  "
        return f"  {_CYN}║{_RST}{inner}{_CYN}║{_RST}"
    print(f"  {_CYN}╔{'═'*_w}╗{_RST}")
    print(_row(_ver, f"{_RED}{_BLD}"))
    print(_row(_sub, _DIM))
    print(f"  {_CYN}╠{'═'*_w}╣{_RST}")
    print(_row(_act))
    print(f"  {_CYN}╚{'═'*_w}╝{_RST}")
    print()


def run_interactive() -> None:
    """
    Main interactive loop.

    Called by main.py when no meaningful arguments are provided.
    """
    # Enable ANSI on Windows
    if os.name == 'nt':
        os.system('')

    while True:
        _clr()
        _menu_header()

        for i, (key, label) in enumerate(_MAIN_MENU, 1):
            # Split label at first double-space into icon+title and description
            parts = label.split('  ', 2)
            if len(parts) >= 2:
                icon_title = parts[0] + '  ' + parts[1]
                desc       = parts[2] if len(parts) > 2 else ''
            else:
                icon_title = label
                desc       = ''
            print(f"  {_YEL}[{i}]{_RST}  {icon_title:<36} {_DIM}{desc}{_RST}")

        print()
        # Show current session target if one is set
        if _session.get('target'):
            print(f"  {_DIM}Session target:{_RST}  {_GRN}{_session['target']}{_RST}"
                  f"  {_DIM}· type {_RST}[T]{_DIM} to change{_RST}")
        print(f"  {_DIM}[T]  Set/change session target    [Q]  Exit PrinterReaper{_RST}")
        print()

        try:
            raw = input(f"  {_CYN}▶{_RST} Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {_DIM}Bye.{_RST}\n")
            sys.exit(0)

        if raw.lower() in ('q', 'quit', 'exit', ''):
            print(f"\n  {_DIM}Bye.{_RST}\n")
            sys.exit(0)

        # Allow typing 't' to change the session target quickly
        if raw.lower() == 't':
            new_t = _ask("New session target IP or hostname", _session.get('target', ''))
            if new_t and new_t not in ('192.168.x.x',):
                _session['target'] = new_t
            continue

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(_MAIN_MENU):
                key = _MAIN_MENU[idx][0]
            else:
                continue
        except ValueError:
            continue

        _clr()

        if key == 'discover':
            _menu_discover()
        elif key == 'scan':
            _menu_scan()
        elif key == 'bruteforce':
            _menu_bruteforce()
        elif key == 'attack':
            _menu_attack()
        elif key == 'exploits':
            _menu_exploits()
        elif key == 'send':
            _menu_send_job()
        elif key == 'workflow':
            _workflow_full_audit()
        elif key == 'config':
            _menu_config()
