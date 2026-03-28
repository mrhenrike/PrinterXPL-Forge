# Wordlists

PrinterReaper v3.7.0 uses zero hardcoded credentials. All credential data is read from external wordlist files at runtime.

---

## Default Wordlists

```
wordlists/
  printer_default_creds.txt   # 195+ user:pass pairs grouped by vendor
  snmp_communities.txt        # SNMP community strings
  ftp_creds.txt               # FTP credentials for printer file servers
  pjl_passwords.txt           # PJL protection bypass passwords
```

These files are located automatically when `--bruteforce` is used without `--bf-wordlist`.

---

## File Format

### `printer_default_creds.txt`

```
# Lines starting with # are comments — ignored by the loader

# ── Epson ─────────────────────────────────────────────────────────────────────
admin:epson
admin:__SERIAL__
:__SERIAL__
ADMIN:__SERIAL__
administrator:__SERIAL__
admin:__MAC6__
admin:__MAC12__

# ── HP (Hewlett-Packard) ─────────────────────────────────────────────────────
Admin:Admin
admin:
jetdirect:
admin:hpinvent!
admin:HP@dmin1!
admin:password
admin:1234

# ── Canon ─────────────────────────────────────────────────────────────────────
admin:
ADMIN:canon
admin:Printix
admin:__SERIAL__

# ── UNIVERSAL / GENERIC ───────────────────────────────────────────────────────
admin:
admin:admin
admin:1234
admin:12345
admin:password
root:
root:root
```

### `snmp_communities.txt`

```
# One community string per line
public
private
internal
admin
printer
network
```

### `ftp_creds.txt`

```
# FTP credentials for printer file servers
anonymous:
anonymous:anonymous@
admin:admin
admin:epson
admin:password
```

### `pjl_passwords.txt`

```
# PJL protection bypass attempts (4-8 digit PINs and common passwords)
0
00000000
1234
12345678
admin
password
```

---

## Section Detection

The loader detects vendor sections using the pattern:

```
# ── VendorName ─────────────────────────────────────────────────────────
```

When `--bf-vendor epson` is specified, only credentials under the `# ── Epson` section (plus the universal section) are loaded. This significantly reduces the number of attempts and avoids false lockouts.

Vendor name matching is case-insensitive and uses alias normalization:

| Alias | Canonical |
|-------|-----------|
| `hp`, `hewlett`, `hewlett-packard` | `hp` |
| `epson`, `seiko-epson` | `epson` |
| `canon`, `canonicalink` | `canon` |
| `brother`, `brother-industries` | `brother` |
| `ricoh`, `ricoh-company` | `ricoh` |
| `xerox`, `fujifilm-xerox`, `fuji-xerox` | `xerox` |
| `kyocera`, `kyocera-mita` | `kyocera` |
| `samsung`, `samsung-electronics` | `samsung` |
| `lexmark`, `lexmark-international` | `lexmark` |
| `oki`, `oki-data`, `oki-electric` | `oki` |

---

## Dynamic Token Expansion

Tokens in wordlist files are replaced at runtime when the matching flag is provided:

| Token | Required flag | Expands to |
|-------|--------------|-----------|
| `__SERIAL__` | `--bf-serial XAABT77481` | `XAABT77481` |
| `__MAC6__` | `--bf-mac AA:BB:CC:DD:EE:FF` | `DDEEFF` (last 6 hex chars, no separator) |
| `__MAC12__` | `--bf-mac AA:BB:CC:DD:EE:FF` | `AABBCCDDEEFF` (all 12 hex chars, no separator) |

If the required flag is not provided, lines containing unexpanded tokens are skipped silently.

---

## Custom Wordlist

Use a custom wordlist file that replaces the default:

```bash
python printer-reaper.py 192.168.1.100 --bruteforce --bf-wordlist /path/to/my_creds.txt
```

The custom file must follow the same format. Vendor sections are optional — if absent, all credentials are tried regardless of vendor.

---

## Adding Credentials on Top

Use `--bf-cred` to add individual pairs that are tested first (highest priority), before any wordlist entries:

```bash
python printer-reaper.py 192.168.1.100 --bruteforce \
  --bf-wordlist wordlists/printer_default_creds.txt \
  --bf-cred admin:MyCustomPass \
  --bf-cred root:toor
```

---

## Credential Architecture Flow

```
--bf-cred USER:PASS (extra creds)
       |
       v (tested first — highest priority)
wordlist_loader.load_for_vendor(vendor, wordlist_path)
       |
       +-- parse vendor section from .txt file
       +-- expand __SERIAL__, __MAC6__, __MAC12__ tokens
       +-- generate password variations (unless --bf-no-variations)
       |
       v
iter_credentials() generator
       |
       v (deduplicated, ordered)
bruteforce_http()   bruteforce_ftp()   bruteforce_snmp()   bruteforce_telnet()
```

---

## Statistics

The loader provides entry counts per section when a wordlist is loaded:

```
Wordlist: wordlists/printer_default_creds.txt
  Epson      :  12 entries
  HP         :  18 entries
  Canon      :   9 entries
  Brother    :   8 entries
  Ricoh      :   7 entries
  Generic    :  28 entries
  Total      : 195 entries
```

---

## Large Community Wordlists

For broader attacks, you can use community credential lists:

```bash
# SecLists default credentials (requires SecLists installed)
python printer-reaper.py 192.168.1.100 --bruteforce \
  --bf-wordlist /usr/share/seclists/Passwords/Default-Credentials/default-passwords.csv

# Custom hydra-format converted to user:pass
python printer-reaper.py 192.168.1.100 --bruteforce \
  --bf-wordlist /path/to/large_list.txt \
  --bf-delay 1.0 \
  --bf-no-variations
```
