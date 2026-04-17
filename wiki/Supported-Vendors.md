# Supported Vendors

PrinterXPL-Forge has been tested and validated against the following vendors. Default credentials, exploit modules, and language support are listed per vendor.

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
| Protocols | HTTP/EWS, SNMP, IPP, PJL/9100, Telnet |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:initpass`, `admin:access`, `admin:<serial[-8:]>` |
| Login URL | `/general/status.html` |
| CVEs | CVE-2024-51977, CVE-2024-51978 |
| Exploits | `research-brother-serial-pwd`, `research-brother-nvram`, `research-brother-vuln-enum` |

**CVE-2024-51977:** Unauthenticated serial number disclosure via PJL INFO CONFIG or HTTP web interface.

**CVE-2024-51978:** Default admin password is derived from the last 8 characters of the serial number. Use `research-brother-serial-pwd` to retrieve serial and compute password automatically.

**NVRAM attack:** `research-brother-nvram` sends rapid PJL SET COLLATE commands to exhaust NVRAM write cycles — causes permanent device failure (irreversible DoS).

---

## Ricoh

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, FTP, IPP |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:`, `supervisor:`, `sysadmin:password` |
| Login URL | `/web/guest/en/websys/webArch/loginView.cgi` |
| CVEs | CVE-2019-14308 |
| Exploits | `edb-45273`, `research-ricoh-ldap-passback` |

**LDAP Pass-Back:** `research-ricoh-ldap-passback` logs into the Ricoh web interface and redirects the LDAP server address to an attacker listener to capture bind credentials.

---

## Xerox / Fujifilm Xerox

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, FTP, IPP, PJL/9100 |
| Languages | PJL, PostScript, PCL |
| Default creds | `admin:1111`, `admin:admin`, `admin:22222` |
| Login URL | `/ui/?_action=StartSession` |
| CVEs | CVE-2010-4231, CVE-2024-6333 |
| Exploits | `edb-17636`, `research-xerox-pjl-dlm`, `research-xerox-firmware-root`, `edb-cve-2024-6333` |

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
| CVEs | CVE-2013-6234, CVE-2023-23560, CVE-2023-26067 |
| Exploits | `edb-20565`, `edb-cve-2024-47176` (CUPS chain), `research-lexmark-fw-decrypt`, `research-lexmark-cve-2023-26067`, `msf-lexmark-cred-dump` |

---

## Konica Minolta

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SOAP, SNMP, IPP |
| Languages | PostScript, PCL, PJL |
| Default creds | `Admin:12345678`, `Admin:1234`, `admin:` |
| Login URL | `/wcd/logon.pl` |
| CVEs | CVE-2022-1026 |
| Exploits | `edb-cve-2022-1026`, `research-konica-soap-extract`, `research-bizhub-user-extract` |

**SOAP credential extraction:** `research-konica-soap-extract` authenticates to the bizhub SOAP API and dumps LDAP/SMB/SMTP stored credentials. `research-bizhub-user-extract` reads the unauthenticated address book XML endpoint (`/wcd/abbr.xml`) for usernames.

---

## Sharp

| Property | Details |
|----------|---------|
| Protocols | HTTP/EWS, SNMP, SMTP |
| Languages | PJL, PostScript |
| Default creds | `admin:admin`, `admin:Sharp2012`, `admin:` |
| Login URL | `/main.htm` |
| CVEs | CVE-2022-45796 |
| Exploits | `edb-cve-2022-45796`, `research-sharp-smtp-passback` |

**SMTP Pass-Back:** `research-sharp-smtp-passback` logs into Sharp MX-2640N/MX-B468 and redirects the SMTP server to a listener to capture mail authentication credentials.

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
| Epson | partial | no | no | yes | yes | 4 |
| HP | yes | yes | yes | yes | yes | 11 |
| Brother | yes | yes | yes | yes | yes | 7 |
| Ricoh | yes | yes | yes | yes | yes | 5 |
| Xerox | yes | yes | yes | yes | yes | 7 |
| Canon | no | yes | yes | yes | yes | 5 |
| Kyocera | yes | yes | yes | yes | yes | 4 |
| Samsung | yes | yes | no | yes | yes | 2 |
| OKI | yes | yes | yes | yes | yes | 1 |
| Lexmark | yes | yes | yes | yes | yes | 6 |
| Konica | no | yes | yes | yes | yes | 4 |
| Sharp | partial | yes | no | yes | yes | 3 |
| Toshiba | no | yes | yes | yes | yes | 1 |
| Zebra | no | no | no | yes | yes | 1 |
| Fujifilm | no | yes | yes | yes | yes | 1 |
| Dell | no | no | no | yes | yes | 2 |
| Windows/CUPS | — | — | — | — | — | 9 (spooler/cups) |
| Generic IoT | — | — | — | — | yes | 3 (mirai/wifi/grpc) |

**Total modules: 93** (23 ExploitDB + 19 Metasploit + 51 Research)
