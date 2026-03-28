# Installation

## Requirements

- **Python 3.8+** (tested up to 3.13)
- **OS:** Windows 10/11, Linux (Debian/Ubuntu/Kali/Arch), macOS 12+, BSD, Android/Termux (limited)
- **Disk:** ~80 MB (including virtual environment and ML models)
- **RAM:** ~100 MB at runtime (ML disabled) / ~200 MB with ML enabled

---

## Standard Installation

```bash
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper

# Create virtual environment (strongly recommended)
python -m venv .venv

# Activate
.venv\Scripts\activate        # Windows PowerShell
source .venv/bin/activate     # Linux / macOS / Termux

# Install all dependencies
pip install -r requirements.txt

# Verify
python printer-reaper.py --version
# → printerreaper Version 3.7.0 (2026-03-25)
```

---

## Windows — SentinelOne / EDR

If your machine has EDR that blocks `%TEMP%` writes:

```powershell
# Create venv inside the project (not in temp dirs)
python -m venv C:\Projetos-SafeLabs\dev\IoT\PrinterReaper\.venv
C:\Projetos-SafeLabs\dev\IoT\PrinterReaper\.venv\Scripts\activate
pip install -r requirements.txt
```

Use the provided launchers:
```powershell
.\scripts\run.ps1      # Windows PowerShell launcher
```
```bash
./scripts/run.sh       # Linux / macOS launcher
```

---

## Linux (Debian/Ubuntu/Kali)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv snmp

git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## macOS

```bash
brew install python3 net-snmp
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Android / Termux (limited)

```bash
pkg update && pkg install python git
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper
pip install -r requirements.txt
# Note: SNMP discovery may not work; ML disabled on ARM without numpy wheels
```

---

## Dependencies

| Package | Purpose | Required |
|---------|---------|---------|
| `requests` | HTTP client for web interface attacks | Yes |
| `urllib3` | HTTP helpers | Yes |
| `pysnmp` | SNMP v1/v2c/v3 discovery and attacks | Yes |
| `pysmb` | SMB printing protocol | Yes |
| `colorama` | Terminal colors (Windows) | Yes |
| `shodan` | Shodan API for online discovery | Optional |
| `censys` | Censys API for online discovery | Optional |
| `scikit-learn` | ML fingerprinting and attack scoring | Optional |
| `impacket` | SMB/NTLM helpers | Optional |
| `pytest` | Run QA test suite | Dev only |

---

## Optional tools (system)

| Tool | Purpose |
|------|---------|
| `snmpwalk` | Enhanced SNMP enumeration |
| `nmap` | Network port scanning |
| `responder` | NTLM hash capture (lateral movement) |
| `hashcat` | Crack captured NTLM hashes |
