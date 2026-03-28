# Brute-Force Login

Test credentials against HTTP/HTTPS web admin, FTP, SNMP community strings, and Telnet using external wordlists.

---

## Basic Usage

```bash
# Auto-detect vendor from --scan, use default wordlist
python printer-reaper.py 192.168.1.100 --bruteforce

# Explicit vendor
python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor epson

# Vendor + serial (most effective for Epson, HP, Canon)
python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor epson --bf-serial XAABT77481

# Vendor + MAC (OKI, Brother, Kyocera KR2 use last 6 hex chars of MAC)
python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor oki --bf-mac AA:BB:CC:DD:EE:FF

# Combined with scan (auto-populates vendor + serial from fingerprint)
python printer-reaper.py 192.168.1.100 --scan --bruteforce
```

---

## All Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--bruteforce` | — | Enable brute-force login |
| `--bf-vendor VENDOR` | auto | Override vendor for credential selection |
| `--bf-serial SERIAL` | — | Device serial number (`__SERIAL__` token) |
| `--bf-mac MAC` | — | MAC address (`__MAC6__`, `__MAC12__` tokens) |
| `--bf-wordlist FILE` | default list | Custom wordlist (REPLACES default) |
| `--bf-cred USER:PASS` | — | Extra credential on top of wordlist (repeatable) |
| `--bf-no-variations` | False | Disable variation engine |
| `--bf-delay SECS` | 0.3 | Delay between login attempts |

---

## Wordlist Control

### Default wordlist (auto-located)

The default wordlist is `wordlists/printer_default_creds.txt`. It contains 195+ credentials grouped by vendor section.

```bash
python printer-reaper.py 192.168.1.100 --bruteforce --bf-vendor hp
```

### Custom wordlist (replaces default)

```bash
python printer-reaper.py 192.168.1.100 --bruteforce --bf-wordlist /path/to/my_creds.txt
```

The custom wordlist REPLACES the default. Use `--bf-cred` to add individual credentials on top.

### Add individual credentials (highest priority)

```bash
# Tested first, before any wordlist entry
python printer-reaper.py 192.168.1.100 --bruteforce \
  --bf-cred admin:MyPass \
  --bf-cred root: \
  --bf-cred administrator:XAABT77481
```

### Disable variation engine (faster, less thorough)

```bash
python printer-reaper.py 192.168.1.100 --bruteforce --bf-no-variations
```

### Slow down (avoid lockouts)

```bash
python printer-reaper.py 192.168.1.100 --bruteforce --bf-delay 2.0
```

---

## Password Variation Engine

For each base password in the wordlist, the engine generates multiple variants:

| Variation | Input: `epson` | Input: `XAABT77481` |
|-----------|--------------|-------------------|
| normal | `epson` | `XAABT77481` |
| reverse | `nospe` | `18477TBAAXT` |
| leet | `3ps0n` | `XAABT77481` |
| CamelCase | `Epson` | `Xaabt77481` |
| UPPER | `EPSON` | `XAABT77481` |
| lower | `epson` | `xaabt77481` |
| reverse+leet | `n0sp3` | `18477TBAAXT` |
| append `1` | `epson1` | `XAABT774811` |
| prepend `1` | `1epson` | `1XAABT77481` |

Disable with `--bf-no-variations` for a faster pass.

---

## Protocols Tested

PrinterReaper brute-forces all available authentication endpoints in parallel:

### HTTP / HTTPS

- Basic Auth (RFC 7235)
- Form-based login (POST to known EWS login paths per vendor)
- Digest Auth
- Session cookie-based auth (HP EWS, Ricoh, Xerox)

```
Login URL detection per vendor:
  Epson   : /PRESENTATION/HTML/TOP/PRTINFO.HTML
  HP      : /hp/device/webAccess/index.htm
  Ricoh   : /web/guest/en/websys/webArch/loginView.cgi
  Xerox   : /ui/?_action=StartSession
  Canon   : /login.html
  Brother : /general/status.html
  Kyocera : /ws/km-wsdl/setting/account
  Konica  : /wcd/logon.pl
  Samsung : /sws/app/gnb/login/view.jsp
```

### FTP

Uses credentials from `wordlists/ftp_creds.txt` plus any wordlist entries.

### SNMP

Tests community strings from `wordlists/snmp_communities.txt`:
- Tries SNMP GET for `sysDescr`
- Tries SNMP SET for write community verification

### Telnet

Connects to port 23 and attempts login with wordlist credentials.

---

## Dynamic Token Expansion

Tokens in wordlist files are expanded at runtime when the corresponding flag is provided:

| Token in wordlist | Flag | Expanded to |
|------------------|------|-------------|
| `__SERIAL__` | `--bf-serial XAABT77481` | `XAABT77481` |
| `__MAC6__` | `--bf-mac AA:BB:CC:DD:EE:FF` | `DDEEFF` |
| `__MAC12__` | `--bf-mac AA:BB:CC:DD:EE:FF` | `AABBCCDDEEFF` |

Example wordlist line:
```
admin:__SERIAL__
```
With `--bf-serial XAABT77481` → tested as `admin:XAABT77481`.

---

## Full Example Output

```
  ============================================================
  BRUTE FORCE LOGIN — 192.168.1.100
  ============================================================
  Vendor    : epson
  Serial    : XAABT77481
  Wordlist  : wordlists/printer_default_creds.txt (195 entries)
  Variations: YES

  [HTTP BF] http://192.168.1.100:80
  Login URL  : http://192.168.1.100:80/PRESENTATION/HTML/TOP/PRTINFO.HTML

  [ ] admin:admin              → 401
  [ ] admin:epson              → ...
  [+] FOUND: HTTP 192.168.1.100:80 → 'admin' / 'epson'
       Evidence: Basic auth accepted (200 OK)

  [FTP BF] 192.168.1.100:21
  [ ] anonymous:                → 530 Login incorrect
  [ ] admin:admin               → 530
  [ ] admin:epson               → 230 Login successful

  [SNMP BF] 192.168.1.100:161
  [ ] public     → READ: sysDescr=...  (read access)
  [+] FOUND community (write): private → SNMP SET succeeded

  [TELNET BF] 192.168.1.100:23
  (no Telnet service detected)

  ============================================================
  RESULTS SUMMARY
  ============================================================
  HTTP    [+] admin / epson
  FTP     [+] admin / epson
  SNMP    [+] community=private (write)
  Telnet  [ ] not available
```

---

## Wordlist Format

See [Wordlists](Wordlists) for the full format specification.

Quick summary:
```
# Lines starting with # are comments
# ── Epson ──────────────────────────────────────────────────────
admin:epson
admin:__SERIAL__
# ── HP ─────────────────────────────────────────────────────────
Admin:Admin
jetdirect:
admin:hpinvent!
# ── UNIVERSAL / GENERIC ─────────────────────────────────────────
admin:
admin:admin
admin:1234
root:
```
