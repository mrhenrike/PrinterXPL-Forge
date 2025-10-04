# 🔧 Troubleshooting Guide

Solutions to common problems and error messages in PrinterReaper.

---

## 🚨 Connection Issues

### Problem: "Connection refused"

**Symptoms:**
```
Failed to connect to 192.168.1.100: [Errno 111] Connection refused
```

**Possible Causes:**
1. Printer is offline or powered off
2. Port 9100 is closed or filtered
3. Wrong IP address
4. Firewall blocking connection

**Solutions:**
```bash
# Test 1: Verify printer is online
ping 192.168.1.100

# Test 2: Check if port 9100 is open
telnet 192.168.1.100 9100
# or
nmap -p 9100 192.168.1.100

# Test 3: Try different ports
python3 printer-reaper.py 192.168.1.100:9101 pjl
python3 printer-reaper.py 192.168.1.100:515 pjl   # LPD port
python3 printer-reaper.py 192.168.1.100:631 pjl   # IPP port

# Test 4: Check firewall
sudo iptables -L   # Linux
netsh advfirewall show allprofiles  # Windows
```

---

### Problem: "Connection timeout"

**Symptoms:**
```
Command timed out - printer may be busy
```

**Solutions:**
```bash
# Increase timeout
192.168.1.100:/> timeout 60

# Or use --debug to see what's happening
python3 printer-reaper.py --debug 192.168.1.100 pjl

# Check if printer is responsive
ping 192.168.1.100
```

---

### Problem: "Connection lost"

**Symptoms:**
```
Connection lost - printer may have disconnected
```

**Solutions:**
```bash
# Reconnect
192.168.1.100:/> reconnect

# If persists, restart printer and reconnect
# Check network stability
ping -c 100 192.168.1.100
```

---

## 📁 File System Issues

### Problem: "File not found"

**Symptoms:**
```
File not found or permission denied
```

**Solutions:**
```bash
# Check if file exists
> ls /etc
> find / | grep passwd

# Try different paths
> download /etc/passwd
> download 0:/etc/passwd
> download ../../../etc/passwd

# Check permissions
> permissions /etc/passwd
```

---

### Problem: "Permission denied"

**Symptoms:**
```
Permission denied
```

**Possible Causes:**
1. File is protected
2. Volume is read-only
3. Printer has security controls
4. File doesn't exist

**Solutions:**
```bash
# Test 1: Check if printer is locked
> variables | grep LOCK

# Test 2: Try unlocking
> unlock 0

# Test 3: Try different volumes
> ls 0:/etc/passwd
> ls 1:/etc/passwd
> ls 2:/etc/passwd

# Test 4: Check file permissions
> permissions /etc/passwd
```

---

### Problem: "Directory not empty" (rmdir)

**Symptoms:**
```
Directory not empty
```

**Solution:**
```bash
# Delete files first
> ls /tmp/olddir
> pjl_delete /tmp/olddir/file1.txt
> pjl_delete /tmp/olddir/file2.txt

# Then remove directory
> rmdir /tmp/olddir
```

---

## 🔐 Authentication Issues

### Problem: Printer is locked

**Symptoms:**
```
Printer locked with PIN
```

**Solutions:**
```bash
# Try unlocking with PIN
> unlock 12345

# Try default PINs
> unlock 0
> unlock 1234
> unlock admin

# Brute force (authorized testing only!)
> unlock_bruteforce
```

---

### Problem: "Invalid PIN format"

**Symptoms:**
```
PIN must be between 1 and 65535
```

**Solution:**
```bash
# Use numeric PIN only
> lock 12345        # ✅ Correct
> lock admin        # ❌ Wrong
> lock "1234"       # ❌ Wrong (no quotes)
```

---

## 🌐 Network Issues

### Problem: SNMP discovery finds no printers

**Symptoms:**
```
No printers found via SNMP scan
```

**Solutions:**
```bash
# Test 1: Verify SNMP tools installed
which snmpget
which snmpwalk

# Install if missing
sudo apt install snmp  # Linux
brew install net-snmp  # macOS

# Test 2: Check SNMP access
snmpget -v1 -c public 192.168.1.100 1.3.6.1.2.1.1.1.0

# Test 3: Try different community string
snmpget -v1 -c private 192.168.1.100 1.3.6.1.2.1.1.1.0

# Test 4: Verify network connectivity
ping 192.168.1.100
```

---

### Problem: "No eligible networks found"

**Symptoms:**
```
No eligible networks found to scan
```

**Solutions:**
```bash
# Check network interfaces
ip addr show    # Linux
ifconfig        # macOS/BSD
ipconfig        # Windows

# Verify you're on the same network as printers
# Printers typically on 192.168.x.x or 10.x.x.x
```

---

## 💾 Data Transfer Issues

### Problem: Upload fails

**Symptoms:**
```
Upload failed: <error>
```

**Solutions:**
```bash
# Test 1: Check if filesystem is writable
> touch test.txt
> pjl_delete test.txt

# Test 2: Check file size limits
# Some printers limit upload size
# Try smaller file

# Test 3: Check available space
> info filesys

# Test 4: Try different volume
> upload file.txt 1:/file.txt
```

---

### Problem: Download is corrupted

**Symptoms:**
- Downloaded file is different size
- File contains garbage data
- Binary files are corrupted

**Solutions:**
```bash
# Use binary mode explicitly
# (PrinterReaper handles this automatically)

# Verify file size matches
> ls /etc/passwd
-  834  passwd

$ ls -l passwd
-rw-r--r-- 1 user user 834 Oct 04 13:00 passwd

# If sizes don't match, try again
> download /etc/passwd
```

---

## 🐍 Python Issues

### Problem: "ModuleNotFoundError"

**Symptoms:**
```
ModuleNotFoundError: No module named 'colorama'
```

**Solution:**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt

# Or install specific module
pip3 install colorama
pip3 install requests
pip3 install pysnmp
```

---

### Problem: Python version error

**Symptoms:**
```
SyntaxError: invalid syntax
```

**Solution:**
```bash
# Check Python version
python3 --version

# PrinterReaper requires Python 3.8+
# Update Python if needed

# Ubuntu/Debian
sudo apt install python3.10

# macOS
brew install python@3.10
```

---

### Problem: "win_unicode_console" error (Windows)

**Symptoms:**
```
Please install the 'win_unicode_console' module
```

**Solution:**
```bash
# Windows only
pip install win-unicode-console
```

---

## 🖥️ Platform-Specific Issues

### Linux

**Problem**: "snmpget: command not found"
```bash
# Install SNMP tools
sudo apt install snmp snmp-mibs-downloader  # Ubuntu/Debian
sudo dnf install net-snmp-utils             # Fedora/RHEL
sudo pacman -S net-snmp                     # Arch
```

---

### Windows

**Problem**: Unicode characters display incorrectly
```powershell
# Install Unicode console
pip install win-unicode-console

# Use PowerShell instead of CMD
```

**Problem**: Can't activate virtual environment
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1
```

---

### macOS

**Problem**: Python 3 not found
```bash
# Install Python 3 via Homebrew
brew install python3

# Or use python3 explicitly
python3 printer-reaper.py --version
```

**Problem**: SNMP tools not found
```bash
# Install via Homebrew
brew install net-snmp
```

---

## 🔍 Debugging Tips

### Enable Debug Mode

```bash
# See all traffic
python3 printer-reaper.py --debug 192.168.1.100 pjl

# Or toggle in shell
> debug
Debug output enabled

# See what's being sent/received
> ls
[Sending]: @PJL INFO FILESYS
[Received]: 0: RW 1234567 bytes free
```

### Verbose Logging

```bash
# Log everything to file
python3 printer-reaper.py -o session.log --debug 192.168.1.100 pjl

# Review log
$ cat session.log
@PJL INFO ID
@PJL INFO CONFIG
...
```

### Network Traffic Capture

```bash
# Capture on Linux
sudo tcpdump -i any -w printer.pcap port 9100

# Capture on Windows
# Use Wireshark to capture on port 9100

# Analyze
wireshark printer.pcap
```

---

## 🎯 Common Workflows That Fail

### "I can't find any files"

**Problem**: `ls` returns empty or minimal results

**Try:**
```bash
# Test different volumes
> ls 0:/
> ls 1:/
> ls 2:/

# Test common paths
> ls /etc
> ls /tmp
> ls /webServer
> ls /rw/var

# Use find
> find /
```

---

### "Commands hang or timeout"

**Problem**: Commands don't return

**Solutions:**
```bash
# Increase timeout
> timeout 60

# Check printer status
ping 192.168.1.100

# Restart printer
> restart

# Reconnect
> reconnect
```

---

### "Printer reboots after commands"

**Problem**: Printer restarts unexpectedly

**Possible Causes:**
- Command caused crash
- Buffer overflow triggered
- Firmware bug
- Malformed PJL command

**Solutions:**
```bash
# Avoid problematic commands
# Use safe mode
python3 printer-reaper.py --safe <target> pjl

# Test with simple commands first
> id
> ls
> variables
```

---

## 📞 Getting Help

### Self-Help Resources

1. **Search this Wiki** - Use GitHub search
2. **Check FAQ** - [FAQ](FAQ)
3. **Read Examples** - [Examples](Examples)
4. **Review Logs** - Use `--debug` and `-o`

### Community Help

1. **GitHub Issues** - Report bugs
2. **GitHub Discussions** - Ask questions
3. **Contact** - X / LinkedIn @mrhenrike

### Reporting Issues

When reporting issues, include:
```
PrinterReaper Version: 2.3.4
Operating System: Linux/Windows/macOS
Python Version: 3.10.5
Printer Model: HP LaserJet 4250
Error Message: [exact error]
Steps to Reproduce:
1. Connect to printer
2. Run command: ls
3. Error occurs
```

---

## 🐛 Known Issues

### Issue: Discovery slow on large networks

**Status**: Known limitation  
**Workaround**: Use manual IP or wait for v2.3.5 (parallel scanning)  
**Tracking**: Will be fixed in v2.3.5

### Issue: Some Brother printers don't respond

**Status**: Known compatibility  
**Workaround**: Try increasing timeout to 60+ seconds  
**Tracking**: Under investigation

### Issue: Windows path handling

**Status**: Known issue on some Windows versions  
**Workaround**: Use forward slashes (/) not backslashes (\\)  
**Tracking**: Fixed in v2.3.4

---

## ✅ Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Connection refused | `telnet <ip> 9100` to test |
| Timeout | `timeout 60` |
| Permission denied | `unlock 0` |
| Module not found | `pip3 install -r requirements.txt` |
| Slow discovery | Use specific IP instead |
| SNMP not working | `sudo apt install snmp` |
| Unicode errors (Windows) | `pip install win-unicode-console` |
| Commands hang | `Ctrl+C` then `reconnect` |

---

<div align="center">

**Troubleshooting Guide**  
Still stuck? Open an issue on GitHub!

**→ [Back to FAQ](FAQ)**

</div>

