# PrinterXPL-Forge — Nmap NSE Scripts

> Author: André Henrique (@mrhenrike) | União Geek  
> Repo: https://github.com/mrhenrike/PrinterXPL-Forge  
> Docs: https://github.com/mrhenrike/PrinterXPL-Forge/wiki/NSE

---

## Overview

12 Nmap Scripting Engine (NSE) scripts + 1 shared Lua library for **printer and MFP security assessment**.

These scripts complement the full PrinterXPL-Forge toolkit, providing:
- Multi-protocol banner grabbing and vendor fingerprinting
- CVE cross-reference against 80+ printer vulnerabilities
- Lightweight active probes (non-destructive)
- LDAP/SMB passback attack surface detection
- Firmware update endpoint exposure detection
- Exploit module suggestions for full exploitation

---

## Quick Install

```bash
# 1. Install PrinterXPL-Forge with NSE extras
pip install printerxpl-forge[nse]

# 2. Deploy scripts to Nmap (requires elevated privileges)
printerxpl-nse install

# 3. Verify
printerxpl-nse status
```

On Windows (Administrator PowerShell):
```powershell
pip install printerxpl-forge[nse]
printerxpl-nse install
```

---

## NSE Scripts

| Script | Ports | Description |
|--------|-------|-------------|
| `printer-discover.nse` | 9100, 631, 80, 443, 515, 23 | Fast multi-protocol printer discovery |
| `printer-banner.nse` | 9100, 631, 80, 443, 515 | Full banner grab + vendor fingerprint |
| `printer-pjl-info.nse` | 9100 | Deep PJL enumeration (NVRAM, FS, vars) |
| `printer-ipp-info.nse` | 631 | IPP Get-Printer-Attributes + CVE check |
| `printer-http-ews.nse` | 80, 443 | HTTP EWS fingerprint + default creds |
| `printer-snmp-info.nse` | 161/udp | SNMP Printer MIB enumeration |
| `printer-cve-detect.nse` | Any | CVE cross-reference (80+ CVEs, 15 vendors) |
| `printer-vuln-check.nse` | Any | Active non-destructive vuln validation |
| `printer-cups-rce.nse` | 631 | CUPS CVE-2024-47176 / CVE-2026-34980 |
| `printer-hp-pjl.nse` | 9100 | HP-specific PJL deep scan + CVE check |
| `printer-firmware-exposed.nse` | 80, 443 | Firmware update endpoint detection |
| `printer-passback.nse` | 80, 443 | LDAP/SMB passback attack surface |
| `printer-lexmark-ipp.nse` | 631, 80 | Lexmark-specific IPP + EWS CVE check |
| `printer-printnightmare.nse` | 445, 135 | Windows Print Spooler family check |

**Shared library:** `lib/printerxpl.lua` — vendor patterns, CVE DB, verdict formatting

---

## Usage Examples

```bash
# Discovery across a subnet
nmap -sV --open -p 9100,631,80 --script printer-discover 192.168.1.0/24

# Full assessment on a single target
nmap -p 9100,631,80,443,427,515 --script 'printer-*' <target>

# HP-specific deep scan
nmap -p 9100 --script printer-hp-pjl <target>

# CUPS RCE check (CVE-2026-34980)
nmap -p 631 --script printer-cups-rce <target>

# CVE cross-reference only (safe, no active probes)
nmap -p 9100,631,80 --script printer-banner,printer-cve-detect <target>

# LDAP/SMB passback surface
nmap -p 80,443 --script printer-passback <target>

# Firmware endpoint exposure
nmap -p 80,443 --script printer-firmware-exposed <target>

# Windows Print Spooler (PrintNightmare family)
nmap -p 445,135 --script printer-printnightmare <target>

# SNMP printer MIB dump
nmap -sU -p 161 --script printer-snmp-info <target>

# Active vulnerability validation (intrusive)
nmap -p 9100,631,80,427,445 --script printer-vuln-check <target>
```

---

## Verdict System

Each script returns one of:

| Verdict | Meaning |
|---------|---------|
| `VULNERABLE` | Active probe confirmed the vulnerability |
| `POSSIBLY VULNERABLE` | CVE match or passive indicator — confirm with printer-vuln-check |
| `NOT VULNERABLE` | No CVE match / active probe ruled out |
| `UNKNOWN` | Insufficient data — combine with other scripts |

---

## CVE Coverage (selected)

| CVE | CVSS | Vendor | Description |
|-----|------|--------|-------------|
| CVE-2026-34980 | 9.1 | CUPS | Unauthenticated RCE via PPD injection |
| CVE-2025-26506 | 9.8 | HP | LaserJet Enterprise PostScript RCE |
| CVE-2024-47176 | 9.9 | CUPS | cups-browsed unauthenticated RCE chain |
| CVE-2023-23560 | 9.0 | Lexmark | SSRF-to-RCE (Pwn2Own Toronto 2022) |
| CVE-2022-24673 | 9.8 | Canon | SLP pre-auth stack buffer overflow RCE |
| CVE-2022-45796 | 9.8 | Sharp | Unauthenticated OS command injection |
| CVE-2021-1675  | 9.8 | Microsoft | PrintNightmare — Windows Spooler RCE |
| CVE-2022-38028 | 7.8 | Microsoft | GooseEgg — APT28 Spooler LPE (KEV) |
| CVE-2017-2741  | 9.8 | HP | PJL path traversal to RCE |

Full CVE list: `src/data/cve_catalog.json` (80+ entries)

---

## Full Exploitation

When Nmap suggests a module, run the full exploit with PrinterXPL-Forge:

```bash
pip install printerxpl-forge

# Scan all ports
printerxpl-forge scan --target <IP>

# Run specific module (dry-run first)
printerxpl-forge run --module xpl/edb-cve-2025-26506 --dry-run --target <IP>
printerxpl-forge run --module xpl/edb-cve-2025-26506 --target <IP>

# Check without exploiting
printerxpl-forge check --module xpl/edb-cve-2025-26506 --target <IP>
```

---

## CLI Reference

```
printerxpl-nse <command> [options]

Commands:
  install     Copy NSE scripts to Nmap scripts directory
  uninstall   Remove NSE scripts from Nmap
  list        List all bundled scripts
  status      Check installation status
  path        Show detected Nmap directories
  verify      Verify scripts load in Nmap

Options (install/uninstall):
  --scripts-dir PATH   Override Nmap scripts directory
  --nselib-dir PATH    Override Nmap nselib directory (for shared lib)
  --no-db-update       Skip nmap --script-updatedb after install
```

---

## File Structure

```
nse/
├── __init__.py
├── install_nse.py          ← CLI installer (printerxpl-nse)
├── README.md
├── scripts/
│   ├── printer-banner.nse
│   ├── printer-pjl-info.nse
│   ├── printer-ipp-info.nse
│   ├── printer-http-ews.nse
│   ├── printer-snmp-info.nse
│   ├── printer-cve-detect.nse
│   ├── printer-vuln-check.nse
│   ├── printer-cups-rce.nse
│   ├── printer-hp-pjl.nse
│   ├── printer-firmware-exposed.nse
│   ├── printer-passback.nse
│   ├── printer-lexmark-ipp.nse
│   ├── printer-printnightmare.nse
│   └── printer-discover.nse
└── lib/
    └── printerxpl.lua      ← Shared Lua library
```

---

> Created by André Henrique (@mrhenrike) — União Geek  
> https://github.com/Uniao-Geek
