# Reconnaissance

Passive assessment: fingerprint, CVE lookup, attack surface mapping — **no payloads sent**.

---

## --scan

Full fingerprint + CVE/NVD lookup + attack surface assessment.

```bash
python printer-reaper.py 192.168.0.152 --scan
```

### What `--scan` does

**Phase 1 — Fingerprint & Banner Grab**
- Connects to ports: 9100 (RAW/PJL), 631 (IPP), 515 (LPD), 80/443 (HTTP/HTTPS), 161 (SNMP), 21 (FTP), 23 (Telnet), 445 (SMB)
- Sends `@PJL INFO ID` and `@PJL INFO VARIABLES` to port 9100
- Sends HTTP HEAD + GET to ports 80/443, reads Server header, EWS title, version strings
- Sends SNMP GET for `sysDescr`, `sysObjectID`, `hrDeviceDescr`
- Parses model, make, firmware version, serial number from all sources
- Reports open ports and supported protocols

**Phase 2 — CVE / NVD Lookup**
- Queries NVD API (National Vulnerability Database) for known CVEs matching `make+model+firmware`
- Falls back to built-in CVE database if NVD API is not configured
- Reports CVE ID, CVSS score, description, affected versions

**Phase 3 — Exploit Matching**
- Cross-references detected make+model against `xpl/index.json`
- Lists applicable exploit modules (check with `--xpl-check`, run with `--xpl-run`)

**Sample output:**
```
[1/3] Fingerprint & Banner Grab — 192.168.0.152
  Make      : Epson
  Model     : L3250 Series
  Serial    : XAABT77481
  Firmware  : 05.22.XF26P8
  HTTP      : 200 OK  (EPSON Web Config)
  SNMP      : public  sysDescr=EPSON L3250 Series
  IPP       : ipp://192.168.0.152/ipp  version=2.0
  Open ports: 80, 443, 631, 9100

[2/3] CVE / NVD Lookup
  CVE-2022-3426  CVSS 7.5  Epson L3xxx HTTP auth bypass
  CVE-2023-27516 CVSS 6.5  Epson session fixation
  CVE-2024-51982 CVSS 5.3  Epson FORMLINES crash (DoS)

[3/3] Exploit Matching
  edb-35151  CVSS 7.8   HP/Epson PJL info disclosure  → --xpl-check edb-35151
  research-ldap-hash-capture  CVSS 9.0  LDAP NTLM hash capture
```

---

## --scan-ml

Same as `--scan` plus ML-assisted fingerprinting and attack scoring.

```bash
python printer-reaper.py 192.168.0.152 --scan-ml
```

The ML engine:
- Uses a trained classifier to confirm vendor/model from banner text patterns
- Scores each detected attack vector by estimated success likelihood
- Suggests the most effective attack sequence based on the fingerprint

**Additional output from ML:**
```
[ML] Fingerprint confidence: EPSON=97.3%  HP=1.2%  Other=1.5%
[ML] Recommended attack sequence:
  1. bruteforce (HTTP) — score 0.92
  2. xpl-check edb-35151 — score 0.78
  3. attack-matrix (pjl:info + snmp) — score 0.71
```

---

## --no-nvd

Skip the NVD API call. Uses only the built-in CVE database. Useful for offline mode or faster scans.

```bash
python printer-reaper.py 192.168.0.152 --scan --no-nvd
```

---

## Scan + auto-exploit matching

```bash
python printer-reaper.py 192.168.0.152 --scan --xpl
```

After the scan, automatically runs `--xpl-check` for every matching exploit and shows which ones are verified vulnerable.

---

## Global flags that enhance scan

```bash
--debug     # show raw bytes sent/received during probe
--quiet     # suppress banner (useful in scripts)
-o file     # log all raw probe data to file
--config    # use custom config.json with API keys
```

---

## Combining scan + brute-force (auto-populate serial)

```bash
python printer-reaper.py 192.168.0.152 --scan --bruteforce
```

When both are combined:
- `--scan` runs first and extracts make/model/serial
- `--bruteforce` auto-receives the detected vendor and serial number
- No need to pass `--bf-vendor` and `--bf-serial` separately
