# Changelog

All notable changes to PrinterReaper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.3] - 2025-10-05

### Added
- **Official Website** - https://www.uniaogeek.com.br/printer-reaper/
- **União Geek Branding** - Logotype and links across all documentation
- Version consistency - All .md files updated to v2.5.3

### Changed
- README.md enhanced with oficial website links
- Wiki footer standardized with União Geek branding
- CHANGELOG.md now includes v2.5.0-2.5.3 entries

### Fixed
- Version synchronization across all documentation
- Link consistency in wiki pages

---

## [2.5.1] - 2025-10-05

### Added
- **PRET Assets Integration** - Complete import of legacy PRET assets
  - 8 PostScript Type 1 fonts in `src/assets/fonts/`
  - 3 SNMP MIBs in `src/assets/mibs/` (HOST-RESOURCES, Printer, SNMPv2)
  - 4 EPS overlay samples in `src/assets/overlays/`
  - 5 test pages (PS/PCL) in `tests/fixtures/pretpages/`
- **New Commands**:
  - `assets` - List all bundled assets (fonts, MIBs, overlays, testpages)
  - `overlay_list` (PS) - Preview overlay files with title extraction
- **Tools**:
  - `tools/release_notes.py` - Generate release notes from git commits
  - `tools/db_merge.py` - Merge PRET model databases
- **União Geek Branding** - Logotype and links in README and wiki

### Changed
- **Repository Cleanup** - Removed 116+ archived files from public tracking
  - Untracked `deleted/` folder (90K+ lines)
  - Removed `wiki-html/`, `src/utils/docs/`, test outputs
  - Enhanced `.gitignore` with status reports, summaries, and temp files
- **Documentation**:
  - README.md updated to v2.5.1 with overview diagram
  - Wiki footer updated with União Geek branding
  - All wiki links corrected (yourusername → mrhenrike)
- **Help System**:
  - PS `overlay` help now references asset directories
  - Enhanced help messages with asset locations

### Fixed
- PS/PCL help now standardized with categories and command counts
- Repository structure optimized for public consumption

---

## [2.5.0] - 2025-10-05

### Added
- **Startup UX** - Running without args shows extended help, quick-start, and discovery options
- **Discovery Flags**:
  - `--discover-local` - Run local SNMP discovery
  - `--discover-online` - Run online discovery (Shodan/Censys)
- **Help Standardization** - PS/PCL shells now show categorized help (PJL-style)
- Test fixtures: Simple testpages in `tests/fixtures/testpages/`
- Example overlay in `src/payloads/assets/overlays/notice.eps`

### Changed
- `main.py` CLI refactored for better UX
- `target` and `mode` arguments now optional (for discovery workflows)
- Help output enhanced with quick-start examples

### Fixed
- `help` command now works in PS and PCL shells (not just PJL)
- Generic `do_help` added to base `printer.py` class

---

## [2.4.2] - 2025-10-04

### Added
- Standalone HTML wiki for website deployment
- `wiki-html/` directory with professional HTML documentation
- `wiki-html/index.html` - Main homepage
- `wiki-html/commands.html` - Commands reference
- Responsive design for mobile devices

### Changed
- Updated all documentation to v2.4.2
- Improved README.md with recent updates section
- Enhanced .gitignore with better exclusions

### Fixed
- Minor documentation inconsistencies

---

## [2.4.1] - 2025-10-04

### Added
- Comprehensive QA test suite (37 automated tests)
- QA_REPORT_v2.4.0.md with detailed test results
- tests/test_runner.py - Automated testing framework
- tests/qa_comprehensive_test.py - Extended test suite

### Changed
- Updated README.md to accurately reflect v2.4.0 features
- All documentation updated to match current feature set
- Version bumped to 2.4.1

### Fixed
- Missing `import json` in test_runner.py
- Windows encoding issues in test output
- Documentation accuracy improvements

### Tested
- ✅ 100% pass rate on 37 automated tests
- ✅ All modules validated
- ✅ All protocols tested
- ✅ All payloads verified

---

## [2.4.0] - 2025-10-04

### Added - MAJOR RELEASE
- **PostScript Module** (src/modules/ps.py) - 40 commands
  - Complete PostScript exploitation
  - operators.py integration (400+ operators)
  - Dictionary dumping and enumeration
  - Print job manipulation (overlay, cross, replace)
  - File system operations
  - Payload system integration

- **PCL Module** (src/modules/pcl.py) - 15 commands
  - Virtual filesystem via PCL macros
  - Macro-based file storage
  - Legacy printer support

- **Network Protocols** (src/protocols/)
  - RAW Protocol (Port 9100) - src/protocols/raw.py
  - LPD Protocol (Port 515) - src/protocols/lpd.py
  - IPP Protocol (Port 631) - src/protocols/ipp.py
  - SMB Protocol (Ports 445/139) - src/protocols/smb.py

- **Payload System** (src/payloads/)
  - banner.ps - Custom banner printing
  - loop.ps - Infinite loop DoS
  - erase.ps - Page erase
  - storm.ps - Print storm attack
  - exfil.ps - Data exfiltration
  - Payload loader with variable substitution

### Changed
- main.py now supports 3 languages (pjl, ps, pcl)
- Enhanced auto-detect for language selection
- operators.py finally integrated (reserved since v2.3.3)

### Statistics
- Total commands: 54 → 109 (+102%)
- Languages: 1 → 3 (+200%)
- Protocols: 1 → 4 (+300%)
- Payloads: 0 → 5 (NEW)
- Lines of code: +4,000

---

## [2.3.4] - 2025-10-04

### Added
- Complete GitHub Wiki (14 pages, 8,440+ lines)
- Home.md, Installation.md, Quick-Start.md
- Commands-Reference.md, PJL-Commands.md
- Security-Testing.md, Examples.md
- Attack-Vectors.md, Architecture.md
- FAQ.md, Troubleshooting.md, Contributing.md
- _Sidebar.md for navigation
- WIKI_README.md

### Changed
- Documentation increased by 425% (2,000 → 10,600 lines)

---

## [2.3.3] - 2025-10-04

### Added
- macOS (Darwin) support in osdetect.py
- BSD (FreeBSD, OpenBSD, NetBSD) support
- OS detection caching for performance
- Configurable timeout in capabilities.py
- CODE_ANALYSIS_v2.3.3.md (1,000+ lines analysis)

### Changed
- osdetect.py enhanced with broader OS support
- capabilities.py timeout now configurable
- operators.py comprehensively documented
- main.py accepts darwin and bsd OS types

### Improved
- Better error handling in WSL detection
- More informative OS detection messages
- Enhanced documentation for operators.py

---

## [2.3.2] - 2025 (Earlier)

### Added
- Enhanced fuzzer.py with dynamic methods
- fuzz_paths(), fuzz_names(), fuzz_data()
- fuzz_traversal_vectors() for path traversal testing

---

## [2.3.0] - 2025 (Earlier)

### Added
- Complete PJL v2.0 implementation
- 54 PJL commands across 7 categories
- Organized help system
- Enhanced error handling

---

## Version History Summary

| Version | Date | Type | Highlights |
|---------|------|------|------------|
| 2.4.2 | Oct 2025 | Patch | HTML wiki, QA tested |
| 2.4.1 | Oct 2025 | Patch | QA testing, documentation updates |
| 2.4.0 | Oct 2025 | Major | PostScript, PCL, protocols, payloads |
| 2.3.4 | Oct 2025 | Minor | Complete wiki documentation |
| 2.3.3 | Oct 2025 | Minor | macOS/BSD support, code analysis |
| 2.3.0 | 2025 | Minor | PJL v2.0 complete |

---

## Links

- [GitHub Repository](https://github.com/mrhenrike/PrinterReaper)
- [GitHub Wiki](https://github.com/mrhenrike/PrinterReaper/wiki)
- [Issue Tracker](https://github.com/mrhenrike/PrinterReaper/issues)
- [Releases](https://github.com/mrhenrike/PrinterReaper/releases)

---

**Maintained by**: PrinterReaper Development Team  
**Last Updated**: October 4, 2025
