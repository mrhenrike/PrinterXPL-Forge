# 📦 Installation Guide

Complete guide to installing PrinterReaper on various platforms.

---

## 📋 Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, Windows, WSL, macOS, or BSD
- **Network**: TCP/IP connectivity to target printers (port 9100)
- **Permissions**: Standard user permissions (root not required)

### Recommended Requirements

- **Python**: 3.10+
- **RAM**: 512 MB minimum
- **Disk Space**: 100 MB for installation
- **Network Tools**: `snmpget` for discovery features

---

## 🐧 Linux Installation

### Ubuntu / Debian

```bash
# 1. Update package list
sudo apt update

# 2. Install Python 3 and pip
sudo apt install python3 python3-pip git

# 3. Clone PrinterReaper
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 4. Install Python dependencies
pip3 install -r requirements.txt

# 5. Install SNMP tools (optional, for discovery)
sudo apt install snmp snmp-mibs-downloader

# 6. Test installation
python3 printer-reaper.py --version
```

### Fedora / RHEL / CentOS

```bash
# 1. Install Python 3 and pip
sudo dnf install python3 python3-pip git

# 2. Clone PrinterReaper
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Install SNMP tools (optional)
sudo dnf install net-snmp net-snmp-utils

# 5. Test installation
python3 printer-reaper.py --version
```

### Arch Linux

```bash
# 1. Install Python and git
sudo pacman -S python python-pip git

# 2. Clone PrinterReaper
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install SNMP tools (optional)
sudo pacman -S net-snmp

# 5. Test installation
python3 printer-reaper.py --version
```

---

## 🪟 Windows Installation

### Windows 10/11 (Native)

```powershell
# 1. Install Python from python.org
# Download and install Python 3.10+ from:
# https://www.python.org/downloads/

# 2. Open PowerShell and clone repository
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 3. Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install win_unicode_console for better display
pip install win_unicode_console

# 6. Test installation
python printer-reaper.py --version
```

### WSL (Windows Subsystem for Linux)

```bash
# 1. Install WSL if not already installed
# In PowerShell as Administrator:
wsl --install

# 2. Open WSL terminal and follow Linux instructions
# Follow Ubuntu installation steps above

# 3. Test installation
python3 printer-reaper.py --version
```

---

## 🍎 macOS Installation

### macOS 12+ (Monterey and later)

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python 3
brew install python3 git

# 3. Clone PrinterReaper
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 4. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip3 install -r requirements.txt

# 6. Install SNMP tools (optional)
brew install net-snmp

# 7. Test installation
python3 printer-reaper.py --version
```

---

## 🔷 BSD Installation

### FreeBSD

```bash
# 1. Install Python and git
sudo pkg install python39 py39-pip git

# 2. Clone PrinterReaper
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install SNMP tools (optional)
sudo pkg install net-snmp

# 5. Test installation
python3.9 printer-reaper.py --version
```

---

## 📦 Dependencies Explained

### Required Dependencies

```python
# Core functionality
colorama>=0.4.6         # Terminal colors
requests>=2.31.0        # HTTP requests
urllib3>=2.0.0          # HTTP client

# Optional but recommended
pysnmp>=4.4.12          # SNMP discovery
win-unicode-console     # Windows Unicode (Windows only)
```

### Optional Tools

```bash
# SNMP tools for network discovery
snmpget, snmpwalk       # SNMP queries

# Image manipulation (for printing features)
imagemagick             # Image conversion
ghostscript             # PostScript rendering
```

---

## 🔧 Virtual Environment Setup

### Why Use Virtual Environment?

- Isolates dependencies from system Python
- Prevents version conflicts
- Easy to remove without affecting system

### Creating Virtual Environment

```bash
# Linux/macOS/BSD
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Activating/Deactivating

```bash
# Activate
source venv/bin/activate  # Linux/macOS/BSD
.\venv\Scripts\Activate.ps1  # Windows

# Deactivate
deactivate
```

---

## 🧪 Verify Installation

### Check Python Version

```bash
python3 --version
# Should show: Python 3.8.0 or higher
```

### Check Dependencies

```bash
pip3 list | grep -E 'colorama|requests|pysnmp'
```

### Run Version Check

```bash
python3 printer-reaper.py --version
# Should show: PrinterReaper Version 2.3.4
```

### Test Discovery

```bash
# Without arguments, discovers printers on network
python3 printer-reaper.py
```

---

## ⚡ Quick Installation (One-liner)

### Linux/macOS

```bash
git clone https://github.com/yourusername/PrinterReaper.git && cd PrinterReaper && pip3 install -r requirements.txt && python3 printer-reaper.py --version
```

### Windows PowerShell

```powershell
git clone https://github.com/yourusername/PrinterReaper.git; cd PrinterReaper; pip install -r requirements.txt; python printer-reaper.py --version
```

---

## 🐳 Docker Installation (Optional)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "printer-reaper.py"]
```

```bash
# Build and run
docker build -t printerreaper .
docker run -it --network host printerreaper <target> pjl
```

---

## 🔍 Troubleshooting Installation

### Python Not Found

```bash
# Try python instead of python3
python --version

# Or install Python
# Linux: sudo apt install python3
# macOS: brew install python3
# Windows: Download from python.org
```

### pip Not Found

```bash
# Install pip
# Linux: sudo apt install python3-pip
# macOS: python3 -m ensurepip
# Windows: python -m ensurepip
```

### Permission Denied

```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Or use --user flag
pip3 install --user -r requirements.txt
```

### Module Not Found

```bash
# Reinstall dependencies
pip3 install --force-reinstall -r requirements.txt
```

### SNMP Discovery Not Working

```bash
# Install SNMP tools
# Ubuntu/Debian: sudo apt install snmp
# Fedora: sudo dnf install net-snmp-utils
# macOS: brew install net-snmp
# Windows: Download from net-snmp.org
```

---

## 🚀 Post-Installation

### Configure Environment

```bash
# Add to PATH (optional)
export PATH=$PATH:/path/to/PrinterReaper

# Create alias (optional)
alias printerreaper='python3 /path/to/PrinterReaper/printer-reaper.py'
```

### Test Connection

```bash
# Test connection to a printer
python3 printer-reaper.py <printer-ip> pjl

# Example
python3 printer-reaper.py 192.168.1.100 pjl
```

---

## 📚 Next Steps

✅ **Installation Complete!**

**→ Continue to [Quick Start Guide](Quick-Start)**

**→ Read [Commands Reference](Commands-Reference)**

**→ Explore [Examples](Examples)**

---

## 💡 Installation Tips

### Performance Tips
- Use Python 3.10+ for best performance
- Install SNMP tools for faster discovery
- Use virtual environment for isolation

### Security Tips
- Keep PrinterReaper updated
- Use in controlled environments only
- Never run on production without permission

### Compatibility Tips
- Test on your specific OS first
- Check firewall rules (port 9100)
- Verify network connectivity

---

<div align="center">

**Installation Help**  
Having trouble? Check [Troubleshooting](Troubleshooting) or open an issue.

**→ [Next: Quick Start](Quick-Start)**

</div>

