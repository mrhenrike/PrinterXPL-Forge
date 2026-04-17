# Changelog — PrinterXPL-Forge

All notable changes to this project are documented here.

This project began as a fork of [PRET (Printer Exploitation Toolkit)](https://github.com/RUB-NDS/PRET)
by Jens Müller / RUB Network and Data Security Group (2016–2023), and was then
extended and rebranded as **PrinterReaper** (2025-10-03) and later as
**PrinterXPL-Forge** (2026-03-25).

Author: André Henrique (@mrhenrike) | União Geek — https://github.com/Uniao-Geek

---

## [4.1.0] — 2026-04-17

### Added
- **Physical damage modules** — three new irreversible-attack modules:
  - `research-fuser-thermal-attack` — fuser thermal runaway via PJL `SET FUSETEMP`,
    PostScript `setpagedevice /FuserTemperature`, HP PML DMCMD (HP/Kyocera/Ricoh/Xerox)
  - `research-motor-jam-attack` — motor jamming via HP PML DMCMD motor-test commands
    and PJL duplex/paper-size rapid cycling
  - `research-laser-scanner-attack` — laser-scanner damage via PostScript `setscreen`
    extreme halftone + PJL `SET RESOLUTION` override + HP PML laser-power DMCMD
- **`src/core/destructive_audit.py`** — orchestration module for scanning all 10
  destructive/irreversible-attack vectors; reports vulnerable/not-vulnerable per module
- **CLI `--destructive-audit`** flag and `--destructive-modules` selector
- **Interactive menu entry `[D] DESTRUCTIVE AUDIT`** with dry-run / live-execute modes
  and mandatory confirmation for live execution
- **`docs/Destructive-Attacks-Wiki.md`** — comprehensive wiki covering damage timelines,
  PJL/PS/PML command references, CLI usage, damage classification table, safety precautions
- **4 previously-empty exploit modules** now fully implemented:
  - `research-fax-dll-inject` — HP MFP Faxploit (CVE-2018-5924/5925)
  - `research-hp-fw-extract` — HP firmware version extraction + CVE mapping
  - `research-nse-compat` — Nmap NSE printer-script compatibility wrapper + PJL fallback
  - `research-xerox-passback` — Xerox LDAP/SMB credential passback (CVE-2022-23968/23969)
- New section in `docs/Exploiting-Network-Printers-via-PrinterXPL-Forge.md`:
  "9b. Irreversible / Physical Damage Attacks"
- **`CHANGELOG.md`** — this file, covering complete project history
- **PRET upstream fixes incorporated:**
  - `pcl.py` `info fonts/macros/patterns/symbols/extended` now iterates all 7 PCL
    location types (Internal, Downloaded, Cartridge, Hard Disk, ROM/SIMMs, Selected,
    All Locations) — fixes PRET issue #89 (hard-disk fonts missed)
  - `pjl.py` `do_set` now wraps `DEFAULT`+`SET` with
    `@PJL SET SERVICEMODE=HPBOISEID` / `EXIT` for persistent HP NVRAM writes
  - `pjl.py` `do_nvram` rewritten to use `@PJL RNVRAM ADDRESS=N` (read) and
    `@PJL WNVRAM ADDRESS=N DATA=V` (write) with `@PJL SUPERUSER PASSWORD=0` bypass,
    plus full sampling-mode `nvram dump all` — replaces broken `@PJL INFO NVRAM`
  - `pjl.py` `do_info` gains hidden undocumented categories: `LOG`, `PRODINFO`,
    `TRACKING`, `SUPPLIES`, `BRFIRMWARE` (covers old HP LaserJet + Brother)

### Changed
- Module count: **96 → 100** exploit modules
- `xpl/index.json` version bumped to `4.1.0`; total updated to 101
- `README.md` and `README.pt-BR.md` updated with destructive-attacks section,
  CLI usage, v4.1.0 badges, and corrected module count

---

## [4.0.0] — 2026-04-17

### Added
- 18 new exploit modules (Batch-32 integration); total reaches **93 modules**
- `research-xsp-beef` — Cross-Site Printing via BeEF-derived JavaScript payloads
  (CORS XHR + PostScript delivery to LAN printers)
- `src/utils/banner_grabber.py` enriched with 85+ Praeda fingerprint signatures
  (`_PRAEDA_SIGNATURES` dict + `praeda_match()`)
- Gemini 2.5 Pro AI-generated PPTX presentation (38 slides, Mueller dark-green theme)
- `docs/Exploiting-Network-Printers-via-PrinterXPL-Forge.md` — 21-section research
  document with Mermaid diagrams, CVE highlights, and 40 references (2002-2025)
- Four high-resolution project diagrams: `printer_architecture.png`,
  `PrinterXPL-Forge_workflow.png`, `attack_coverage_matrix.png`,
  `credential_wordlist_flow.png`
- `.gitignore` security hardening: `docs/*.pptx`, `.tmp/`, `vendor-repos/`,
  `.env`, `secrets/`, `credentials/`

### Changed
- Project renamed from **PrinterReaper** to **PrinterXPL-Forge**
- `README.md` fully rewritten; `README.pt-BR.md` expanded to full parity
- Git history rewritten — single canonical author `mrhenrike`
- `docs/*.pptx` removed from Git tracking
- All `PrinterReaper` / `printer-reaper` references replaced project-wide

---

## [3.15.2] — 2026-03-25

### Fixed
- `fix(ux+print)`: clear OS print queue on startup, handle missing target prompt,
  keep interactive session persistent across re-connections

---

## [3.15.0] — 2026-03-25

### Fixed
- `fix(ipp+print)`: corrected IPP encoding, added PWG Raster format support,
  OS print-job fallback path

---

## [3.14.0] — 2026-03-25

### Added
- Smart job-probe (auto-detect best submit protocol per target)
- TLS auto-upgrade on IPP port 443
- ESC/P encoding fallback for legacy Epson inkjet devices
- Install-printer helper (Windows/CUPS integration)

### Fixed
- ZoomEye / Netlas API errors
- `fix(escp)`: normalize Unicode punctuation (em-dash, curly quotes, ellipsis)
  to ASCII before latin-1 encoding

---

## [3.13.0] — 2026-03-25

### Added
- README dork-filter CSV syntax examples
- GitHub Wiki Home updated to v3.13.0

### Fixed
- ZoomEye/Netlas API key handling; e2e test suite pass
- Repository cleanup: removed tests/, tools/, debian/, packaging/

---

## [3.12.0] — 2026-03-25

### Added
- CSV multi-value dork filters for Shodan/Censys/FOFA/ZoomEye/Netlas
- City/country guard filter for online discovery

---

## [3.11.0] — 2026-03-25

### Added
- Mutual exclusion enforcement on `--shodan`, `--censys`, `--fofa`,
  `--zoomeye`, `--netlas` engine flags
- FOFA key-only authentication mode

---

## [3.10.0] — 2026-03-25

### Added
- Custom port overrides for all protocols (`PortConfig` singleton)
- `--port-raw`, `--port-ipp`, `--port-lpd`, `--port-snmp`, `--port-ftp`,
  `--port-http`, `--port-https`, `--port-smb`, `--port-telnet`, `--extra-ports`
- Zero hardcoded ports in connection code

---

## [3.9.0] — 2026-03-25

### Added
- FOFA, ZoomEye, and Netlas discovery engines (alongside Shodan/Censys)
- `--dork-engine` flag with per-engine native syntax; zero-filter enforcement

---

## [3.8.0] — 2026-03-25

### Added
- Structured dork-based discovery pipeline (Shodan/Censys)
- Auto exploit-matching on discovered targets

---

## [3.7.0] — 2026-03-25

### Added
- GitHub Wiki (13 pages) published
- 4 original SVG/PNG architecture diagrams
- Packaging: `pyproject.toml`, Debian packaging, RPM spec, man page, `MANIFEST.in`
  (pip/deb/rpm installable)
- `run.ps1` / `run.sh` launchers using local `.venv` (SentinelOne EDR workaround)

---

## [3.6.2] — 2026-03-25

### Added
- Expanded default credentials DB
- LDAP hash capture module
- CVE-2024-51978 (Brother serial-based admin password derivation) module

---

## [3.5.0] — 2026-03-25

### Added
- `send-job` command for direct job submission
- External wordlist support (`--bf-wordlist`)
- Emoji-free UI mode

---

## [3.4.2] — 2026-03-24

### Added
- Interactive guided menu with spinner and section headers
- "Next steps" recommendations after scan/exploit

---

## [3.4.1] — 2026-03-24

### Added
- Default credentials DB (multi-vendor)
- Login brute-force module with credential rotation

---

## [3.4.0] — 2026-03-24

### Added
- Exploit library with 8 printer CVE modules + auto-matching on scan
- `--attack-matrix`, `--network-map`, `--xsp` CLI flags
- SSRF pivot module for lateral movement via IPP print-by-reference and WSD SOAP
- IPP attack module (anonymous job, queue purge, attribute manipulation, audit)
- Firmware module (version extract, upload check, NVRAM r/w, payloads, implant)
- Storage module (FTP ops, web file enumeration, SNMP MIB dump, saved jobs)

---

## [3.3.0] — 2026-03-24

### Added
- Network mapper and attack orchestrator
- `--ipp`, `--pivot`, `--storage`, `--firmware`, `--payload`, `--implant` CLI flags

---

## [3.2.0] — 2026-03-24

### Added
- CVE/vuln scanner via NVD API with built-in HP/Epson/Brother CVE DB
- ML engine (scikit-learn) for fingerprint scoring and attack recommendation
- `--scan` / `--scan-ml` recon modes
- Multi-protocol banner grabber (HTTP/HTTPS/IPP/PJL/LPD/WSD/SNMP)
- SMB protocol backend (pysmb)
- IPv6 support (AF_UNSPEC resolution in RAWProtocol)
- SNMP multi-version shim (hlapi-v5, hlapi-v7 asyncio, oneliner fallback)
- Local printer enumeration for Windows and CUPS

---

## [3.1.0] — 2026-03-24

### Added
- Config file support (`--config`, `--check-config`)
- Feature guards for `--discover-online`
- `config.yaml` / `.json` multi-key loader with availability validation
- OpenAI, Anthropic, Gemini LLM integration for AI-assisted analysis

---

## [3.0.0] — 2026-03-24

### Changed
- **Complete architectural rewrite** — modular `src/` layout
  (`core/`, `modules/`, `protocols/`, `utils/`, `ui/`)
- `src/version.py` as single source of truth
- 63-test QA suite (IPv6, SMB, live Epson L3250, Shodan/Censys)
- Version bumped to `3.0.0`; requirements updated

---

## [2.5.3] — 2025-10-04

### Changed
- Final version sync; official website URL in metadata
- União Geek logo resized to 240 px in all docs
- GitHub repository description optimised (40 + 350 char variants)

---

## [2.5.0] — 2025-10-04

### Added
- Import of curated PRET assets: fonts, MIBs, overlays, test pages
  into `assets/` directory structure
- `overlay_list` command; `assets` command (list fonts/MIBs/overlays/testpages)
- Extended CLI: `--discover-local` / `--discover-online` flags

---

## [2.4.2] — 2025-10-04

### Added
- Complete architecture diagrams (4 Mermaid sources + PNGs)
- HTML wiki for website hosting
- Full changelog for this version

### Fixed
- Final cleanup; branding alignment

---

## [2.4.0] — 2025-10-04

### Added
- Attack payload system with 5 PostScript payloads (RCE, DoS, info-disclose)
- Support for 4 additional network printing protocols
- Complete PostScript module with 40+ commands
- Complete PCL module with virtual filesystem

---

## [2.3.5] — 2025-10-04

### Added
- Online discovery module (Shodan API first integration)

---

## [2.3.4] — 2025-10-04

### Added
- Complete wiki documentation (first full wiki release)

---

## [2.3.3] — 2025-10-04

### Changed
- Code audit and cleanup; platform portability improvements

---

## [2.3.0] — 2025-10-04

### Added
- Development roadmap; documentation reorganization

---

## [2.1.0] — 2025-10-03

### Added
- Streamlined system commands
- `.gitignore` for project artifacts

---

## [2.0.0] — 2025-10-03

### Changed
- Complete PJL v2.0 reorganization and integration
- Full PJL command set: `ls`, `get`, `put`, `mkdir`, `rm`, `cd`, `find`, `mirror`,
  `lock`, `unlock`, `destroy`, `nvram`, `flood`, `selftest`, `format`,
  `pagecount`, `hold`, `display`, `offline`, `restart`, `reset`

---

## [1.1.0] — 2025-10-03

### Added
- Robust error handling and user-friendly messages throughout

---

## [1.0.0] — 2025-10-03

### Added
- **PrinterReaper v1.0** — Advanced Printer Penetration Testing Toolkit
  (initial release; fork of PRET, extended for modern exploit research)
- PJL/PS/PCL interactive shells
- Multi-protocol support: RAW (9100), IPP (631), LPD (515), Telnet (23)
- Shodan/Censys discovery engine (initial)
- Basic CVE lookup

---

## PRET Heritage — v0.36 through v0.40 (2017)

> These versions constitute the upstream PRET codebase from which PrinterReaper
> (and subsequently PrinterXPL-Forge) was forked. Changes listed here are taken
> directly from the PRET commit history to provide a complete lineage.

### [0.40] — 2017-11-06

#### Added
- Rewritten print-job capture function (experimental; Lexmark-compatible)
- Monkeypatch for job capture on devices that otherwise drop the connection

### [0.39] — 2017-07-23 *(BlackHat release)*

#### Added
- `unlock bypass` — PostScript `superexec` magic to reset PIN protection without
  knowing the PIN (works on many HP/Ricoh models)
- Lexmark timeout workaround; improved PJL handling for non-HP devices
- PJL `SUPERUSER PASSWORD=0` + `WNVRAM` write bypass for Brother

#### Fixed
- PJL handling for older Lexmark models (timeout issues)

### [0.36] — 2017-01-29 *(first public release)*

#### Added
- `discover` command — SNMP broadcast-based local network printer discovery
- `flood` command — PJL variable fuzzer to reveal buffer overflows
- `lock` / `unlock` commands — PIN-based control panel + disk lock/crack
  (brute-forces 1–65535 PINs at 500 per batch via `@PJL JOB PASSWORD=N`)
- `destroy` command — NVRAM write-cycle exhaustion loop
  (`@PJL DEFAULT COPIES=N`, 100 commands per batch, 10 000 000 iterations)
- `hold` command — enable job retention (`@PJL SET HOLD=ON`)
- `disable` / `enable` — toggle `JOBMEDIA` ON/OFF
- `format` — initialize printer file system (`@PJL FSINIT VOLUME=X`)
- `set` with `@PJL SET SERVICEMODE=HPBOISEID` service-mode unlock
- `selftest` — comprehensive PJL + PML DMCMD self-test trigger
  (11 PJL tests + 9 PML tests + Brother-specific commands)
- `nvram dump/read/write` — Brother NVRAM via `RNVRAM`/`WNVRAM`
- Hidden `@PJL INFO` categories: `LOG`, `PRODINFO`, `TRACKING`, `SUPPLIES`
- PCL virtual filesystem (`pclfs`) using macro IDs + JSON superblock
- PCL `info fonts` over all location types (internal/downloaded/cartridge/ROM)
- LICENSE, README, architecture diagram

### [0.28] — 2016-07-31

#### Added
- Additional PostScript commands (setpagedevice, dict manip, memory ops)
- Minor bug fixes

### [0.25] — 2016-06-24 *(initial GitHub upload)*

#### Added
- Initial public release of PRET
- PJL interactive shell (`ls`, `get`, `put`, `mkdir`, `rm`, `cat`, `edit`,
  `find`, `mirror`, `append`, `touch`, `rename`, `chmod`, `cd`, `pwd`,
  `chvol`, `df`, `free`, `env`, `printenv`, `set`, `display`, `offline`,
  `restart`, `reset`, `status`, `id`, `pagecount`, `version`, `info`)
- PCL interactive shell with virtual filesystem
- PS (PostScript) interactive shell
- SNMP-based printer discovery and reset
- Raw TCP (port 9100), LPD, and IPP transport layers
- Colour terminal output; tab-completion; readline history
- MIB database, codebook for PJL status codes
- Font/overlay/testpage asset bundles

---

*Full git history available via `git log --oneline --all` in the repository.*
