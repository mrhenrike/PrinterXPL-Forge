# Supported Vendors

PrinterReaper has been tested and validated against the following vendors. Default credentials, exploit modules, and language support are listed per vendor.

---

## Epson

**Tested model:** L3250 Series (validated with real hardware)

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP, RAW/9100 |
| Languages | ESC/P, PJL (limited), PostScript (some models) |
| Default creds | `admin:epson`, `admin:<serial>` |
| Serial token | `__SERIAL__` (printed on label) |
| Login URL | `/PRESENTATION/HTML/TOP/PRTINFO.HTML` |
| CVEs | CVE-2022-3426, CVE-2023-27516, CVE-2024-51982 |
| Exploits | `research-epson-http-auth-bypass`, `edb-35151` |

---

## HP (Hewlett-Packard)

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP, RAW/9100, FTP |
| Languages | PJL, PostScript, PCL |
| Default creds | `Admin:Admin`, `jetdirect:`, `admin:hpinvent!` |
| Login URL | `/hp/device/webAccess/index.htm` |
| CVEs | CVE-2019-6329, CVE-2018-5925, CVE-2010-4107 |
| Exploits | `edb-15631`, `edb-35151`, `msf-hp-ews-auth`, `research-hp-factory-reset` |

---

## Brother

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP, Telnet |
| Languages | PJL, PostScript |
| Default creds | `admin:initpass`, `admin:access` |
| Login URL | `/general/status.html` |
| CVEs | CVE-2024-51978 |
| Exploits | `edb-cve-2024-51978` (SNMP OID password leak), `research-brother-telnet` |

**CVE-2024-51978 detail:** The WBM (Web Based Management) password for some Brother models is readable via SNMP OID `1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.3.0`.

---

## Ricoh

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, FTP, IPP |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:`, `supervisor:`, `sysadmin:password` |
| Login URL | `/web/guest/en/websys/webArch/loginView.cgi` |
| CVEs | CVE-2019-14308 |
| Exploits | `edb-45273` |

---

## Xerox / Fujifilm Xerox

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, FTP, IPP |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:1111`, `admin:admin`, `admin:22222` |
| Login URL | `/ui/?_action=StartSession` |
| CVEs | CVE-2010-4231 |
| Exploits | `edb-17636` (FTP default credentials) |

---

## Canon

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP |
| Languages | UFR II, PostScript |
| Default creds | `admin:`, `ADMIN:canon`, `admin:Printix`, `admin:<serial>` |
| Serial token | `__SERIAL__` |
| Login URL | `/login.html` |
| CVEs | CVE-2019-14308, CVE-2023-27516 |
| Exploits | `research-canon-session-fixation` |

---

## Kyocera / Kyocera-MITA

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP |
| Languages | PJL, PostScript, PCL |
| Default creds | `Admin:Admin`, `admin:admin`, `admin:<mac6>` |
| MAC token | `__MAC6__` |
| Login URL | `/ws/km-wsdl/setting/account` |
| CVEs | CVE-2020-23575 |
| Exploits | `research-kyocera-snmp-creds`, `msf-kyocera-fs` |

---

## Samsung

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP |
| Languages | PJL, PostScript |
| Default creds | `admin:sec00000`, `admin:1234` |
| Login URL | `/sws/app/gnb/login/view.jsp` |
| CVEs | CVE-2012-4964 |
| Exploits | `msf-samsung-6600` |

---

## OKI Data

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, Telnet |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:aaaaaa`, `admin:<mac6>` |
| MAC token | `__MAC6__` |
| Login URL | `/printmib/` |
| CVEs | - |
| Exploits | PJL-based modules |

---

## Lexmark

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, FTP |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:1234`, `admin:password`, `admin:lexmark` |
| Login URL | `/cgi-bin/dynamic/user/List.html` |
| CVEs | CVE-2013-6234 |
| Exploits | `edb-20565` |

---

## Konica Minolta

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP |
| Languages | PostScript, PCL |
| Default creds | `admin:`, `12345678:12345678`, `ADMIN:12345678` |
| Login URL | `/wcd/logon.pl` |
| CVEs | - |
| Exploits | IPP anonymous job, SNMP walk |

---

## Sharp

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP |
| Languages | PJL, PostScript |
| Default creds | `admin:admin`, `admin:Sharp`, `admin:` |
| Login URL | `/main.htm` |
| CVEs | - |
| Exploits | SNMP MIB walk |

---

## Toshiba

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP |
| Languages | PostScript, PCL |
| Default creds | `admin:`, `root:root`, `admin:admin` |
| Login URL | `/TopAccess/` |
| CVEs | - |
| Exploits | HTTP brute-force |

---

## Zebra (Label Printers)

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, Telnet |
| Languages | ZPL (Zebra Programming Language) |
| Default creds | `admin:1234`, `admin:admin` |
| Login URL | `/config.html` |
| CVEs | - |
| Exploits | HTTP brute-force, ZPL config dump |

---

## Fujifilm

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, IPP |
| Languages | PostScript, PCL |
| Default creds | `x-admin:11111`, `admin:admin` |
| Login URL | `/wcd/logon.pl` |
| CVEs | - |
| Exploits | SNMP, HTTP |

---

## Axis (Network Cameras / Print Servers)

| Property | Details |
|----------|---------|
| Protocols | HTTP, SNMP |
| Default creds | `root:pass`, `admin:admin` |
| CVEs | CVE-2018-10661 |
| Exploits | HTTP brute-force |

---

## Summary Table

| Vendor | PJL | PS | PCL | SNMP | HTTP BF | Exploit Modules |
|--------|-----|----|-----|------|---------|-----------------|
| Epson | partial | no | no | yes | yes | 3 |
| HP | yes | yes | yes | yes | yes | 5 |
| Brother | partial | yes | no | yes | yes | 2 |
| Ricoh | yes | yes | yes | yes | yes | 2 |
| Xerox | yes | yes | yes | yes | yes | 2 |
| Canon | no | yes | yes | yes | yes | 2 |
| Kyocera | yes | yes | yes | yes | yes | 3 |
| Samsung | yes | yes | no | yes | yes | 1 |
| OKI | yes | yes | yes | yes | yes | 1 |
| Lexmark | yes | yes | yes | yes | yes | 1 |
| Konica | no | yes | yes | yes | yes | 1 |
| Sharp | partial | yes | no | yes | yes | 1 |
| Toshiba | no | yes | yes | yes | yes | 1 |
| Zebra | no | no | no | yes | yes | 1 |
| Fujifilm | no | yes | yes | yes | yes | 1 |
