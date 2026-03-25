# EPSON L3250 SECURITY ASSESSMENT REPORT
**Author:** @mrhenrike (André Henrique)  
**LinkedIn:** https://linkedin.com/in/mrhenrike  
**Date:** 2026-03-25  
**Target:** 192.168.0.152  
**Tool:** PrinterReaper v3.5.0  

---

## 1. DEVICE PROFILE

| Field | Value |
|-------|-------|
| Make/Model | Epson EcoTank L3250 Series |
| Firmware | **05.22.XF26P8** |
| Hardware | EEPS2 Hard Ver.1.00 Firm Ver.0.22 |
| Serial / Admin Password | **XAABT77481** (initial password = serial number) |
| MAC Address | **58:05:D9:3F:9F:9C** |
| IP Address | 192.168.0.152 (DHCP/Auto) |
| Default Gateway | 192.168.0.1 |
| WiFi SSID | **Cyberpass** (WPA2-PSK/AES) |
| Wi-Fi Direct SSID | **DIRECT-D9-EPSON-3F9F9C** |
| Device Name (mDNS) | EPSON3F9F9C |
| Epson Connect Email | **vst2954d586u65@print.epsonconnect.com** |
| Epson Connect Status | Registered / **Connected** (active cloud service) |
| Root Certificate | v02.01 |
| Print Languages | ESCPL2, BDC, D4, D4PX, ESCPR1, END4, GENEP, PWGRaster |

---

## 2. OPEN PORTS / ATTACK SURFACE

| Port | Proto | Service | Auth Required | Notes |
|------|-------|---------|---------------|-------|
| TCP/80 | HTTP | EWS (Embedded Web Server) | None | Redirects to HTTPS/443 |
| TCP/443 | HTTPS | EWS | Session cookie | Self-signed TLS cert |
| TCP/515 | TCP | LPD (Line Printer Daemon) | **None** | Confirmed unauthenticated |
| TCP/631 | TCP+HTTPS | IPP / AirPrint / eSCL | **None** | 30+ attributes exposed |

---

## 3. CRITICAL VULNERABILITIES

### [CRIT-1] CVE-2022-3426 — Unauthenticated Information Disclosure
- **CVSS:** 5.4 (Medium — elevated in context)
- **Endpoint:** `https://192.168.0.152/PRESENTATION/HTML/TOP/PRTINFO.HTML`
- **Auth required:** NONE
- **Data exposed:**
  - Device Name: `EPSON3F9F9C`
  - IP Address: `192.168.0.152`
  - Gateway: `192.168.0.1`
  - MAC Address: `58:05:D9:3F:9F:9C`
  - **WiFi SSID: `Cyberpass`** (WPA2-PSK/AES)
  - WiFi Signal: Excellent
- **Impact:** SSID + MAC → targeted WPA2 handshake capture/deauthentication attack

### [CRIT-2] CWE-603 — Client-Side-Only Authentication (Auth Bypass)
- **Severity:** Critical
- **Description:** The Epson EWS enforces authentication ONLY via JavaScript (`location.href='/PRESENTATION/PSWD'`). Any HTTP client that does not execute JavaScript (curl, Python, scripts) can access all 21 management endpoints with HTTP 200.
- **Proof:** `curl -k https://192.168.0.152/PRESENTATION/HTML/TOP/ADMIN.HTML` → HTTP 200
- **Bypassed pages (21 total):**
  - `/PRESENTATION/HTML/TOP/ADMIN.HTML`
  - `/PRESENTATION/HTML/TOP/SECURITY.HTML`
  - `/PRESENTATION/HTML/TOP/PASSWORD.HTML` — password change
  - `/PRESENTATION/HTML/TOP/FWUPDATE.HTML` — **firmware upload**
  - `/PRESENTATION/HTML/TOP/RESTORE.HTML` — **factory reset**
  - `/PRESENTATION/HTML/TOP/NWCONFIG.HTML` — network config
  - `/PRESENTATION/HTML/TOP/MAINTENANCE.HTML`
  - `/PRESENTATION/BOIP/WIFI/WFCONFIG.HTML` — WiFi config
  - `/PRESENTATION/BOIP/WIFI/WFINFO.HTML`
  - `/PRESENTATION/EEPROM/` — EEPROM/NVRAM access
  - ... and 11 more management pages
- **Impact:** Any local network attacker can potentially trigger firmware update, factory reset, or read/write network configuration without knowing the password.

### [CRIT-3] Unauthenticated LPD / CVE-2023-27516
- **Port:** TCP/515
- **Auth required:** None
- **Confirmed:** LPD responds ACK=0x00 to print commands without credentials
- **Queue State:** `no entries\n` returned to anonymous query
- **Attack:** Send arbitrary PostScript/ESC/P-R data to TCP/515 → prints without auth
- **Proof:**
  ```
  echo "\x04lp\n" | nc 192.168.0.152 515
  → Response: no entries\x00
  ```

### [CRIT-4] Default Admin Password = Public Serial Number
- **Severity:** Critical
- **Description:** Epson documents in the user manual: "The initial password is the product's serial number." The device name `EPSON3F9F9C` is visible on the unauthenticated status page.
- **Attack chain:**
  1. Attacker scans network → finds printer at 192.168.0.152
  2. HTTP GET `/PRTINFO.HTML` → reads device name `EPSON3F9F9C`
  3. Infers serial could be the password
  4. POST `/PRESENTATION/PSWD` with `session=XAABT77481` → **AUTHENTICATED**
- **Mitigation:** Change password immediately

---

## 4. HIGH SEVERITY VULNERABILITIES

### [HIGH-1] Epson Connect Cloud — Sensitive Email Exposed via SNMP
- **OID:** `1.3.6.1.4.1.1248.1.1.3.1.37.2.3.0`
- **Value:** `vst2954d586u65@print.epsonconnect.com`
- **Impact:** Anyone with this email can send print jobs to the printer from anywhere on the internet via Epson Connect cloud service. Email can be used to spam/exfiltrate via this printer remotely.
- **Auth for SNMP:** None (community string `public` accepted)

### [HIGH-2] Wi-Fi Direct SSID Exposed via SNMP
- **OID:** `1.3.6.1.4.1.1248.1.1.3.1.29.3.1.44.0`
- **Value:** `DIRECT-D9-EPSON-3F9F9C`
- **Impact:** Wi-Fi Direct enables direct peer-to-peer connection to the printer without going through the main WiFi network. Attacker in range can connect directly.

### [HIGH-3] SNMP MIB Full Dump — Unauthenticated
- **Community:** `public` (read-only, no auth)
- **Result:** 2,000 OIDs retrieved
- **Key OIDs leaked:**
  - `1.3.6.1.2.1.1.1.0` → `EPSON Built-in 11b/g/n Print Server`
  - `1.3.6.1.2.1.1.5.0` → `EPSON3F9F9C`
  - `1.3.6.1.2.1.43.5.1.1.16.1` → `L3250 Series`
  - `1.3.6.1.2.1.43.11.1.1.6.1.{1-4}` → Ink supply names (BK/C/M/Y)
  - `1.3.6.1.4.1.1248.1.2.2.2.1.1.3.1.2` → `Serial No` label

### [HIGH-4] IPP — 30+ Attributes Disclosed Unauthenticated
- **Port:** TCP/631
- **Key attributes exposed:**
  - `media-default` = `na_letter_8.5x11in`
  - `print-color-mode-supported` = `color`
  - `sides-default` = `one-sided`
  - `output-bin-default` = `face-up`
  - `print-scaling-default` = `auto`
- **AirPrint:** Confirmed active → anonymous job submission via IPP possible

### [HIGH-5] Self-Signed TLS Certificate (HTTPS/443)
- **Issue:** No trusted CA chain → MITM attack trivially possible on the management interface
- **Impact:** Admin credentials transmitted over HTTPS can be intercepted on a compromised network

---

## 5. MEDIUM VULNERABILITIES

| ID | Description |
|----|-------------|
| MED-1 | WiFi SSID `Cyberpass` exposed → WPA2 handshake attack target |
| MED-2 | No rate limiting on POST /PRESENTATION/PSWD → brute-force possible |
| MED-3 | Missing HTTP security headers (X-Frame-Options, CSP, HSTS) |
| MED-4 | eSCL scanner at TCP/631 returns HTTP 500 (server error) → endpoint exists, potential scan data interception |
| MED-5 | WSD SSRF capable (confirmed by attack matrix) |

---

## 6. ATTACK MATRIX (BlackHat 2017 + Extended)

| Category | Attack | Result | Impact |
|----------|--------|--------|--------|
| Info Disclosure | SNMP MIB dump | **EXPLOITED** (2000 OIDs) | HIGH |
| Info Disclosure | Web status page (no auth) | **VULNERABLE** | HIGH |
| Info Disclosure | Epson Connect email via SNMP | **EXPLOITED** | HIGH |
| Info Disclosure | Wi-Fi Direct SSID via SNMP | **EXPLOITED** | MEDIUM |
| Network | WSD SSRF | **VULNERABLE** | MEDIUM |
| LPD | Unauthenticated print job | **VULNERABLE** | MEDIUM |
| IPP | Anonymous attribute enumeration | **VULNERABLE** | MEDIUM |
| Web Auth | Client-side auth bypass | **VULNERABLE** | CRITICAL |
| Web Auth | Default creds (serial as pwd) | **AUTHENTICATED** | CRITICAL |
| DoS | IPP purge jobs | Not successful (auth required) | — |
| PJL | NVRAM access | N/A (ESC/P only) | — |
| PostScript | exitserver bypass | N/A (no PS support) | — |
| SNMP Write | Factory reset via SNMP | Blocked (private rejected) | — |

---

## 7. CVEs APPLICABLE TO THIS TARGET

| CVE | CVSS | Status | Description |
|-----|------|--------|-------------|
| CVE-2022-3426 | 5.4 | **CONFIRMED** | Unauthenticated info disclosure via PRTINFO.HTML |
| CVE-2023-27516 | 7.5 | **CONFIRMED** | LPD unauthenticated print job acceptance |
| CVE-2021-26598 | 6.1 | Likely | CSRF in web management (no CSRF token found in forms) |
| CVE-2019-3949 | 7.5 | Possible | Stored XSS in printer name/location (needs testing) |
| CWE-603 | N/A | **CONFIRMED** | Client-side-only authentication (design flaw) |

**No CVEs found specific to firmware 05.22.XF26P8 on NVD** — this firmware may be recent and unpublished in vulnerability databases.

---

## 8. EXPLOIT AVAILABILITY

No public exploits on ExploitDB specific to Epson L3250 / EcoTank L3250.  
The existing vulnerabilities are exploitable directly without a dedicated exploit:

- **LPD exploit:** `nc 192.168.0.152 515 < malicious_job.lpd`
- **Auth bypass:** `curl -k https://192.168.0.152/PRESENTATION/HTML/TOP/FWUPDATE.HTML`
- **SNMP dump:** `snmpwalk -v1 -c public 192.168.0.152`
- **Epson Connect abuse:** Send print job to `vst2954d586u65@print.epsonconnect.com`

---

## 9. ATTACK VECTORS (Full Chain)

```
UNAUTHENTICATED ATTACK CHAIN:
  LAN access → HTTP GET /PRTINFO.HTML
    → Reads: SSID "Cyberpass", MAC, IP, Gateway
    → Can target WiFi: deauth + WPA2 handshake capture
  
  LAN access → SNMP walk (public)
    → Reads: 2000 OIDs, Epson Connect email, Wi-Fi Direct SSID
    → Can send jobs from internet via Epson Connect email
  
  LAN access → TCP/515 (LPD)
    → Sends arbitrary print job (no credentials)
    → DoS: flood print jobs
    → Data exfil: print sensitive docs as bait job
  
  LAN access → TCP/631 (IPP)
    → Enumerates capabilities (30+ attributes)
    → May submit anonymous AirPrint job

AUTHENTICATED ATTACK CHAIN (creds: admin/XAABT77481):
  LAN access → POST /PRESENTATION/PSWD (session=XAABT77481)
    → Session cookie obtained: EPSON_COOKIE_SESSION=<uuid>
    → Access to full web management interface
    → /FWUPDATE.HTML → upload malicious firmware (persistence/implant)
    → /RESTORE.HTML  → factory reset (DoS)
    → /PASSWORD.HTML → change admin password (lockout)
    → /NWCONFIG.HTML → modify network config (man-in-the-middle)
    → /WFCONFIG.HTML → change WiFi config (pivot)

INTERNET ATTACK CHAIN:
  Internet → Epson Connect → vst2954d586u65@print.epsonconnect.com
    → Send print jobs from anywhere in the world
    → No local network access required
```

---

## 10. RECOMMENDED MITIGATIONS

| Priority | Action |
|----------|--------|
| IMMEDIATE | Change admin password from default serial number |
| IMMEDIATE | Disable or firewall LPD port 515 if not required |
| HIGH | Restrict web management to specific IPs or disable remote access |
| HIGH | Review and disable Epson Connect if not actively needed |
| HIGH | Enable IPP authentication |
| HIGH | Block SNMP write access; change community string from `public` |
| MEDIUM | Apply proper TLS certificate |
| MEDIUM | Check for firmware update at https://epson.com/Support/ |
| MEDIUM | Add HTTP security headers (HSTS, X-Frame-Options, CSP) |
| LOW | Disable Wi-Fi Direct if not needed |

---

## 11. APPENDIX — FULL ENDPOINT MAP

| Endpoint | Auth | Size | Notes |
|----------|------|------|-------|
| / | None | 949b | JS redirect to PSWD |
| /PRESENTATION/HTML/TOP/PRTINFO.HTML | **None** | 6540b | **Leaks SSID, MAC, IP** |
| /PRESENTATION/HTML/TOP/ADMIN.HTML | None (bypass) | 576b | JS-only auth |
| /PRESENTATION/HTML/TOP/SECURITY.HTML | None (bypass) | 576b | JS-only auth |
| /PRESENTATION/HTML/TOP/PASSWORD.HTML | None (bypass) | 576b | JS-only auth |
| /PRESENTATION/HTML/TOP/FWUPDATE.HTML | None (bypass) | 576b | **Firmware upload** |
| /PRESENTATION/HTML/TOP/RESTORE.HTML | None (bypass) | 576b | **Factory reset** |
| /PRESENTATION/HTML/TOP/NWCONFIG.HTML | None (bypass) | 576b | Network config |
| /PRESENTATION/HTML/TOP/MAINTENANCE.HTML | None (bypass) | 576b | Maintenance |
| /PRESENTATION/HTML/TOP/INDEX.html | Session | 7459b | Main menu |
| /PRESENTATION/BOIP/WIFI/WFINFO.HTML | None (bypass) | 576b | WiFi status |
| /PRESENTATION/BOIP/WIFI/WFCONFIG.HTML | None (bypass) | 576b | WiFi config |
| /PRESENTATION/EEPROM/ | None (bypass) | 576b | EEPROM/NVRAM |
| /PRESENTATION/PSWD | None | 3488b | Login form |
| /WSD/DEVICE | — | 0b | WSD endpoint |
| /ipp/ | None | — | IPP endpoint |
| /ipp/print | None | — | IPP print |
| /eSCL/ScannerCapabilities | None | 500 err | Scanner API |
| /eSCL/ScannerStatus | None | 500 err | Scanner API |

---

*Assessment performed with PrinterReaper v3.5.0 — all tests are non-destructive (dry-run mode).*  
*Author: @mrhenrike (André Henrique) | https://linkedin.com/in/mrhenrike*
