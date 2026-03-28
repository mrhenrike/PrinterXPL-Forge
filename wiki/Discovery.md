# Discovery

Find printers before you have a target IP.

---

## Local SNMP Discovery

Sweeps all local network interfaces using SNMP v1/v2c broadcast and unicast probes.

```bash
python printer-reaper.py --discover-local
```

**Output:**
```
[SNMP] Scanning 192.168.0.0/24  [60 threads]
  192.168.0.100  HP LaserJet Pro M404n   uptime=3d 14h   Ready
  192.168.0.152  EPSON L3250             uptime=10h 21m  Ready
  192.168.0.200  Ricoh MP C3003          uptime=15d 03h  Processing

[LOCAL] Installed printers on this host:
  EPSON3F9F9C (L3250 SERIES)  →  192.168.0.152:80
```

**What it does internally:**
- Enumerates all local network adapters and their subnets
- Sends SNMP GET for `sysDescr`, `sysName`, `hrPrinterStatus` to each host
- Uses community strings from `wordlists/snmp_communities.txt`
- Queries the OS installed printer list (Windows WMI / Linux CUPS)
- Reports IP, model, status, uptime

---

## Online Discovery — Shodan & Censys

Requires API keys in `config.json`.

```bash
python printer-reaper.py --discover-online
```

Searches for internet-exposed printers matching known printer banners (PJL, IPP, SNMP) on the configured Shodan/Censys accounts.

**Output:**
```
[SHODAN] Query: port:9100 PJL OR port:631 IPP OR printer ...
  83.X.X.X:9100    HP LaserJet 4250    country=DE   org=Deutsche Telekom
  91.X.X.X:631     CANON iR-ADV C5550  country=FR   org=Orange
  ...

[CENSYS] Fetching ...
  45.X.X.X   port 9100 open   banner: "@PJL" ...
```

### Shodan & Censys setup

```json
{
  "shodan": { "api_key": "YOUR_KEY_HERE" },
  "censys": { "api_id": "YOUR_ID", "api_secret": "YOUR_SECRET" }
}
```

---

## OSINT (passive — no connection to target)

Check if a specific target IP is indexed in Shodan/Censys without connecting to it.

```bash
python printer-reaper.py 192.168.0.152 --osint
```

Useful to check if the device is known-exposed before connecting.

---

## Language Auto-Detect (active probe)

Detect which printer languages are supported without entering interactive mode.

```bash
python printer-reaper.py 192.168.0.152 --auto-detect
```

**Output:**
```
[AUTO] Probing 192.168.0.152 ...
  PJL        : SUPPORTED  (port 9100 responded to @PJL INFO ID)
  PostScript : LIKELY     (PS banner found in HTTP header)
  PCL        : UNKNOWN    (no PCL banner; try interactive mode)
  ESC/P      : NOT FOUND
```

---

## WSD (Web Services for Devices)

WSD discovery happens automatically during `--discover-local` and `--network-map`. It finds WSD-enabled printers via multicast on UDP 3702.

```bash
python printer-reaper.py 192.168.0.152 --network-map
# → [WSD] Neighbor devices: 2 found
```
