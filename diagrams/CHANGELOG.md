# Changelog

All notable changes to PrinterReaper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
