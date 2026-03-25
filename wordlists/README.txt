PrinterReaper — Wordlists Directory
=====================================
Author: Andre Henrique (@mrhenrike)

Files:
  printer_default_creds.txt  — Master credential list (user:pass format, 200+ entries)
  snmp_communities.txt       — SNMP community strings for GET/SET probing
  ftp_creds.txt              — FTP credential pairs for printer FTP servers
  pjl_passwords.txt          — PJL password bypass attempts

Usage:
  --bf-wordlist wordlists/printer_default_creds.txt
  --snmp-community-file wordlists/snmp_communities.txt

Adding your own:
  Place any text file in this directory.
  Format for cred files: username:password (one per line)
  Lines starting with # are comments and ignored.

Sources consulted:
  - Vendor installation manuals (HP, Epson, Brother, Canon, Ricoh, Xerox,
    Kyocera, Konica Minolta, Samsung, OKI, Lexmark, Sharp, Toshiba, Panasonic)
  - FCC ID database filings
  - SecLists (Daniel Miessler)
  - PrinterSecurity.org research
  - CVE/NVD disclosures referencing hardcoded/default credentials
