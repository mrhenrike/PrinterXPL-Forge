# Changelog — PrinterXPL-Forge

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.1.0] — 2026-04-17

### Added
- **3 new physical-damage exploit modules** (96 total):
  - `research-fuser-thermal-attack` — Override fuser temperature setpoint via PJL SET FUSETEMP, PostScript setpagedevice /FuserTemperature, and HP PML DMCMD. Temperatures >270°C risk thermal runaway, fuser melt, and fire.
  - `research-motor-jam-attack` — HP PML DMCMD simultaneous motor activation + duplex-stress cycling + Ricoh MOTORTEST=CONT. Permanently strips plastic drive-train gears.
  - `research-laser-scanner-attack` — PostScript setscreen 9999 lpi + all-black flood + HP PML laser power 0xFF. Degrades laser diode, polygon mirror motor, and photosensitive drum.
- **5 previously empty modules now implemented** (101 total):
  - `research-fax-dll-inject` — HP MFP Faxploit probe (CVE-2018-5924/5925): fax subsystem enumeration via HTTP and PJL
  - `research-hp-fw-extract` — HP firmware version extraction via HTTP DevMgmt XML + PJL + CVE mapping
  - `research-nse-compat` — Nmap NSE printer script wrapper (printer-info, pjl-ready-message, lexmark-config, bjnp-discover) with PJL fallback
  - `research-pret-compat` — PRET (RUB-NDS) compatibility shim: runs PRET commands if installed, falls back to native PJL
  - `research-xerox-passback` — Xerox VersaLink/AltaLink LDAP/SMB/SMTP credential passback (CVE-2022-23968/23969)
- **`src/core/destructive_audit.py`** — Destructive Attack Audit Engine scanning all 10 irreversible attack vectors
- **`--destructive-audit`** CLI flag — assess or execute all destructive attack modules against a target
- **`--destructive-modules`** CLI flag — select specific destructive module IDs
- **Interactive menu option `[D] DESTRUCTIVE AUDIT`** — guided destructive attack selector with confirmation gate
- **`docs/Destructive-Attacks-Wiki.md`** — comprehensive wiki covering all 10 irreversible attack vectors, damage timelines, safety precautions, and references
- **Destructive attacks section in README.md and README.pt-BR.md** — full table, PJL/PS payload examples, CLI usage

### Changed
- `xpl/index.json`: 93 → 101 modules, version 4.0.0 → 4.1.0
- `src/version.py`: 4.0.0 → 4.1.0
- README version badge: 3.14.0 → 4.1.0
- `docs/Exploiting-Network-Printers-via-PrinterXPL-Forge.md`: added section 9b (Physical Damage attack class)

---

## [4.0.0] — 2026-04-17

### Added
- **93 exploit modules** across 7 categories (PJL, PostScript, PCL, ESC/P, SNMP, HTTP, Research)
- **`--destructive-audit`** predecessor: `--auto-exploit`, `--attack-matrix` orchestration
- **BeEF XSP module** (`research-xsp-beef`) — Cross-Site Printing with real BeEF JS payloads
- **Praeda integration** in `src/utils/banner_grabber.py` — 85+ printer fingerprints
- **Comprehensive research documentation** `docs/Exploiting-Network-Printers-via-PrinterXPL-Forge.md` (21 sections, 40 references)
- **PPTX presentation** `docs/Exploiting-Network-Printers-via-PrinterXPL-Forge.pptx` (38 slides, Gemini 2.5 Pro generated)
- **Security hardened `.gitignore`** — blocks `.tmp/`, `vendor-repos/`, `.env`, `secrets/`
- **Git history rewritten** — single canonical author `mrhenrike` via filter-repo

### Changed
- Project renamed `PrinterReaper` → `PrinterXPL-Forge`
- 4 architectural diagrams regenerated (PRET-style, PIL icons, anti-aliased)
- README.pt-BR.md expanded to full content parity with README.md

---

## [3.14.0] — 2026-03-25

### Added
- Batch-3 integration: 18 new exploit modules (total 93)
- `src/ui/interactive.py` — guided interactive menu
- `--bruteforce` with vendor credential wordlist (all protocols)
- `--scan-ml` fingerprinting
- Shodan / Censys OSINT integration (`--discover-online`)
- `--attack-matrix` full campaign orchestrator
- `--send-job` print job delivery (RAW/IPP/LPD)

### Changed
- Version scheme migrated from 3.x to 4.x after overhaul

---

## [3.0.0] — 2026-02-01 (PrinterReaper)

### Added
- Initial public release forked from PRET (RUB-NDS)
- PJL / PostScript / PCL interactive shells
- Basic CVE catalog and exploit module framework
- Multi-protocol scanner (RAW 9100, IPP 631, LPD 515, SNMP 161)

---

*Author: André Henrique (@mrhenrike) | União Geek — https://github.com/Uniao-Geek*
