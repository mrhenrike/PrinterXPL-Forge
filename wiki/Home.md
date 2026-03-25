# 🔥 Welcome to PrinterReaper Wiki

**Advanced Printer Penetration Testing Toolkit**

> *"Is your printer safe from the void? Find out before someone else does…"*

> **📍 Official Website**: [www.uniaogeek.com.br/printer-reaper](https://www.uniaogeek.com.br/printer-reaper/)

---

## What is PrinterReaper?

PrinterReaper **v3.13.0** is a **complete, modular framework** for **security assessment of network printers**. It supports all major printer languages (PJL, PostScript, PCL, ESC/P), all common protocols (RAW/JetDirect, IPP, LPD, SNMP, FTP, HTTP/HTTPS, SMB, Telnet), 39+ exploit modules, ML-assisted fingerprinting, NVD/CVE integration, and 5-engine internet discovery via structured dork queries.

### Key Features

- **5 Search Engines** — Shodan, Censys, FOFA, ZoomEye, Netlas with multi-value dork filters (CSV or repeat)
- **39+ Exploit Modules** — ExploitDB, Metasploit-reference, and original research modules
- **Auto-Exploit Pipeline** — Fingerprints target, matches exploits, pre-fills variables, runs best confirmed exploit
- **Zero Hardcoded Credentials** — Wordlist-driven brute-force engine with vendor sections and variation generator
- **Custom Port Overrides** — Every protocol port configurable via `--port-raw`, `--port-ipp`, etc.
- **ML Fingerprinting** — ML-assisted printer language and attack scoring (`--scan-ml`)
- **3 LLM Providers** — OpenAI, Anthropic (Claude), Google (Gemini) for analysis and reports
- **Attack Matrix** — Full BlackHat 2017 + CVEs campaign with DoS, RCE, info disclosure, bypass vectors
- **Network Mapping** — SNMP routing, PJL network vars, subnet scan, WSD neighbors, attack paths

---

## 🚀 Quick Links

### Getting Started
- **[Installation Guide](Installation)** - Set up PrinterReaper in minutes
- **[Quick Start](Quick-Start)** - Your first printer test in 5 minutes
- **[Commands Reference](Commands-Reference)** - Complete command list

### Advanced Usage
- **[PJL Commands](PJL-Commands)** - Detailed PJL command reference
- **[Security Testing](Security-Testing)** - Security assessment workflows
- **[Attack Vectors](Attack-Vectors)** - Exploitation techniques
- **[Examples](Examples)** - Real-world usage examples

### Help & Support
- **[FAQ](FAQ)** - Frequently asked questions
- **[Troubleshooting](Troubleshooting)** - Common issues and solutions
- **[Architecture](Architecture)** - Technical architecture overview

---

## 📊 PrinterReaper at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    PrinterReaper v2.4.2                     │
├─────────────────────────────────────────────────────────────┤
│  📁 Filesystem     │  12 commands │ Upload, download, copy │
│  ℹ️  Information    │   8 commands │ ID, version, network   │
│  ⚙️  Control        │   8 commands │ Restart, reset, backup │
│  🔒 Security       │   4 commands │ Lock, unlock, NVRAM    │
│  💥 Attacks        │   8 commands │ Destroy, flood, format │
│  🌐 Network        │   3 commands │ Direct, execute, load  │
│  📊 Monitoring     │   2 commands │ Pagecount, status      │
├─────────────────────────────────────────────────────────────┤
│  Total             │  54 commands │ 100% documented        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 What You Can Do

### File System Access
- Browse printer's file system (folders, files)
- Download configuration files and logs
- Upload arbitrary files to printer
- Mirror entire filesystem locally
- Manipulate file permissions

### Information Gathering
- Identify printer model and firmware
- Extract network configuration
- Dump NVRAM contents
- List environment variables
- Get system uptime and page count

### Control & Configuration
- Change printer settings
- Display custom messages on panel
- Take printer offline
- Backup and restore configuration
- Perform self-tests

### Security Testing
- Test for authentication bypass
- Verify file system restrictions
- Check NVRAM security
- Test buffer overflows
- Path traversal testing

### Exploitation
- Capture print jobs
- Inject malicious data
- Cause denial of service
- Physical NVRAM damage
- Job retention attacks

---

## ⚠️ Legal Notice

**IMPORTANT**: PrinterReaper is intended **solely for authorized security testing**. 

- ✅ Run only against devices you own or have written permission to test
- ❌ Unauthorized use may violate laws and regulations
- ⚖️ The authors disclaim all liability for misuse or damage

**By using PrinterReaper, you accept full responsibility for your actions.**

---

## 📚 Documentation Structure

This wiki is organized into the following sections:

### 🚀 Getting Started
1. [Installation](Installation) - Install and configure
2. [Quick Start](Quick-Start) - First steps tutorial
3. [Commands Reference](Commands-Reference) - All commands overview

### 📖 Command Details
4. [PJL Commands](PJL-Commands) - PJL-specific commands
5. [Filesystem Commands](Filesystem-Commands) - File operations
6. [Security Commands](Security-Commands) - Security testing
7. [Attack Commands](Attack-Commands) - Exploitation techniques

### 🔬 Advanced Topics
8. [Security Testing](Security-Testing) - Testing workflows
9. [Attack Vectors](Attack-Vectors) - Exploitation methods
10. [Examples](Examples) - Real-world scenarios
11. [Architecture](Architecture) - System design

### 🆘 Support
12. [FAQ](FAQ) - Common questions
13. [Troubleshooting](Troubleshooting) - Problem solving
14. [Contributing](Contributing) - How to contribute

---

## 🌟 Key Highlights

### Version 2.4.2 Features

**✨ New in 2.4.2:**
- HTML wiki for website deployment
- QA tested with 100% pass rate
- Complete toolkit: 109 commands
- 3 printer languages (PJL, PS, PCL)
- 4 network protocols (RAW, LPD, IPP, SMB)
- 5 attack payloads
- Comprehensive documentation

**⚡ Performance:**
- 30-second timeout configuration
- Robust retry logic
- Connection pooling ready
- Optimized for reliability

**🛡️ Security:**
- Safe mode verification
- Destructive command warnings
- Comprehensive error handling
- No sensitive data leakage

---

## 🎯 Typical Workflow

```
1. Discovery
   └─> ./printer-reaper.py        # Find printers on network

2. Connect
   └─> ./printer-reaper.py <target> pjl

3. Reconnaissance
   ├─> id                          # Identify printer
   ├─> ls                          # Browse filesystem
   ├─> network                     # Get network info
   └─> info config                 # Get configuration

4. Exploitation
   ├─> download /etc/passwd        # Exfiltrate sensitive files
   ├─> upload backdoor.ps          # Upload malicious files
   ├─> lock 12345                  # Lock control panel
   └─> capture                     # Capture print jobs

5. Cleanup
   ├─> delete backdoor.ps          # Remove evidence
   └─> exit                        # Disconnect
```

---

## 📞 Need Help?

- **Wiki Navigation**: Use the sidebar to browse all topics
- **Command Help**: Type `help <command>` in the shell
- **Search**: Use GitHub's wiki search feature
- **Issues**: Report bugs on GitHub Issues
- **Contact**: X / LinkedIn @mrhenrike

---

## 🚀 Ready to Start?

**→ [Install PrinterReaper Now](Installation)**

**→ [Quick Start Guide](Quick-Start)**

---

<div align="center">

**PrinterReaper v2.5.3**  
*Complete Printer Penetration Testing Toolkit*

**109 Commands | 3 Languages | 4 Protocols | 5 Payloads**

Made with ❤️ for the security community

---

### Powered by União Geek

<a href="https://www.uniaogeek.com.br"><img src="../img/logotype-uniaogeek-2.png" width="240" alt="União Geek"></a>

**[www.uniaogeek.com.br](https://www.uniaogeek.com.br)** | **[Blog](https://www.uniaogeek.com.br/blog)**

</div>

