# PrinterReaper Wiki

> **Advanced Printer Penetration Testing Toolkit — v3.7.0**

Welcome to the PrinterReaper documentation wiki. Select a page below for detailed documentation on each feature.

---

## Pages

| Page | Description |
|------|-------------|
| [Installation](Installation) | Prerequisites, virtual environment, dependencies |
| [Quick Start](Quick-Start) | First scan in 60 seconds |
| [Discovery](Discovery) | Find printers: local SNMP, WSD |
| [Online Discovery Dorks](Online-Discovery-Dorks) | `--discover-online` with structured dorks: vendor, country, region, port, city, CPE |
| [Reconnaissance](Reconnaissance) | `--scan`, `--scan-ml`, banner grab, CVE lookup, ML |
| [Auto Exploit](Auto-Exploit) | `--auto-exploit` — automatic selection, verification, parameter pre-fill, and execution |
| [Interactive Shell](Interactive-Shell) | PJL, PostScript, PCL — all 109 commands with examples |
| [Brute Force Login](Brute-Force) | `--bruteforce`, wordlists, tokens, variations |
| [Exploit Library](Exploit-Library) | `--xpl-*` flags, exploit modules, writing custom exploits |
| [Attack Matrix](Attack-Matrix) | `--attack-matrix` — full BlackHat 2017 campaign |
| [Lateral Movement](Lateral-Movement) | SSRF pivot, network map, LDAP hash capture |
| [Storage & Firmware](Storage-Firmware) | `--storage`, `--firmware`, `--implant` |
| [Cross-Site Printing](Cross-Site-Printing) | XSP + CORS spoofing payload generator |
| [Send Print Job](Send-Job) | `--send-job` — print any file type to target |
| [Wordlists](Wordlists) | Format, vendor sections, tokens, custom wordlists |
| [Configuration](Configuration) | `config.json`, API keys, `--check-config` |
| [Custom Exploits](Custom-Exploits) | Write your own `exploit.py` module |
| [Supported Vendors](Supported-Vendors) | Default credentials and exploits per vendor |

---

## Quick reference

```bash
# Discover printers on local network
python printer-reaper.py --discover-local

# Passive fingerprint + CVE scan (no payloads)
python printer-reaper.py 192.168.1.100 --scan

# PJL interactive shell
python printer-reaper.py 192.168.1.100 pjl

# Credential brute-force with serial number
python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor epson --bf-serial XAABT77481

# Full attack matrix campaign (dry-run)
python printer-reaper.py 192.168.1.100 --attack-matrix

# List all exploit modules
python printer-reaper.py 192.168.1.100 --xpl-list
```

---

> Author: [@mrhenrike](https://github.com/mrhenrike) · [LinkedIn](https://linkedin.com/in/mrhenrike) · [X/Twitter](https://x.com/mrhenrike)
