# ❓ Frequently Asked Questions (FAQ)

Answers to common questions about PrinterReaper.

---

## 🚀 Getting Started

### Q: What is PrinterReaper?
**A:** PrinterReaper is an advanced penetration testing toolkit specialized in exploiting network printers through PJL (Printer Job Language). It allows security researchers to discover, assess, and exploit printer vulnerabilities.

### Q: Is PrinterReaper legal to use?
**A:** PrinterReaper is a **security research tool**. It is legal when used with proper authorization on devices you own or have written permission to test. Unauthorized use is illegal and unethical.

### Q: What printers does PrinterReaper support?
**A:** PrinterReaper supports printers that implement PJL (Printer Job Language), which includes:
- HP LaserJet series
- Brother MFC/DCP series
- Epson WorkForce series
- Lexmark printers
- Kyocera printers
- OKI printers
- Xerox printers
- And many others

### Q: Does PrinterReaper work on all operating systems?
**A:** Yes! PrinterReaper v2.3.4 supports:
- ✅ Linux (all distributions)
- ✅ Windows 10/11
- ✅ WSL (Windows Subsystem for Linux)
- ✅ macOS (Monterey and later)
- ✅ BSD (FreeBSD, OpenBSD, NetBSD)

---

## 🔧 Installation & Setup

### Q: How do I install PrinterReaper?
**A:** Installation is simple:
```bash
git clone https://github.com/yourusername/PrinterReaper.git
cd PrinterReaper
pip3 install -r requirements.txt
```
See [Installation Guide](Installation) for detailed instructions.

### Q: What are the dependencies?
**A:** Required dependencies:
- Python 3.8+
- colorama (terminal colors)
- requests (HTTP requests)
- pysnmp (SNMP discovery - optional)

### Q: Do I need root/admin privileges?
**A:** No! PrinterReaper runs with standard user privileges. Root is only needed if you want to:
- Use ports below 1024
- Access local USB printers directly
- Install SNMP tools system-wide

### Q: Why isn't SNMP discovery working?
**A:** Install SNMP tools:
```bash
# Linux
sudo apt install snmp

# macOS
brew install net-snmp

# Windows
# Download from net-snmp.org
```

---

## 🎯 Usage Questions

### Q: How do I discover printers on my network?
**A:** Run PrinterReaper without arguments:
```bash
python3 printer-reaper.py
```
It will automatically scan your local network for printers using SNMP.

### Q: How do I connect to a specific printer?
**A:** Use the printer's IP address or hostname:
```bash
python3 printer-reaper.py 192.168.1.100 pjl
```

### Q: What does "pjl" mean in the command?
**A:** It specifies the printer language to use. PrinterReaper currently focuses on PJL (Printer Job Language). Use `auto` for automatic detection.

### Q: How do I get help on a specific command?
**A:** Use the `help` command:
```bash
# General help
> help

# Specific command
> help upload
> help lock
```

### Q: Can I automate testing?
**A:** Yes! Use the `-i` flag to load commands from a file:
```bash
python3 printer-reaper.py -i commands.txt <target> pjl
```

---

## 🔒 Security Questions

### Q: Is it safe to test on production printers?
**A:** **NO!** Always test on dedicated test devices first. Many PrinterReaper commands can:
- Disrupt service
- Modify configuration
- Delete files
- Cause physical damage

### Q: What commands are safe to use?
**A:** Read-only commands are generally safe:
- `id`, `ls`, `cat`, `download`
- `network`, `info`, `variables`
- `printenv`, `pagecount`

Avoid destructive commands without authorization:
- ❌ `destroy`, `format`, `reset`
- ⚠️ `restart`, `lock`, `disable`

### Q: How do I avoid damaging the printer?
**A:** Follow these guidelines:
1. Always backup configuration first (`backup`)
2. Test on non-production devices
3. Read command help before using (`help <command>`)
4. Use `--safe` mode for verification
5. Avoid commands with ⚠️ warnings

### Q: Can PrinterReaper be detected?
**A:** Potentially yes. Printers may log:
- Network connections
- PJL commands received
- File operations
- Configuration changes

Use in controlled environments only.

---

## 💻 Technical Questions

### Q: What port does PrinterReaper use?
**A:** By default, port 9100 (raw printing port). You can specify a custom port:
```bash
python3 printer-reaper.py 192.168.1.100:9101 pjl
```

### Q: Why is the connection timing out?
**A:** Try increasing the timeout:
```bash
# In shell
> timeout 60

# Or set longer default in code
```
See [Troubleshooting](Troubleshooting) for more solutions.

### Q: Why do some commands not work?
**A:** Not all printers support all PJL commands. Support varies by:
- Printer manufacturer
- Firmware version
- PJL implementation
- Security settings

### Q: How do I capture PJL traffic?
**A:** Use debug mode or tcpdump:
```bash
# Debug mode (shows PJL commands)
python3 printer-reaper.py --debug <target> pjl

# Packet capture
tcpdump -i eth0 -w capture.pcap port 9100
```

### Q: Can I log all commands?
**A:** Yes, use the `-o` flag:
```bash
python3 printer-reaper.py -o session.log <target> pjl
```

---

## 🐛 Error Messages

### Q: "Connection refused" error?
**A:** Possible causes:
- Printer is offline
- Port 9100 is closed
- Firewall is blocking
- Wrong IP address

Try:
```bash
# Test connection
ping <printer-ip>
telnet <printer-ip> 9100
nmap -p 9100 <printer-ip>
```

### Q: "No data received" error?
**A:** Possible causes:
- Printer doesn't support PJL
- Printer is busy
- Network latency high
- Timeout too short

Try:
```bash
# Increase timeout
> timeout 60

# Use safe mode to verify PJL support
python3 printer-reaper.py --safe <target> pjl
```

### Q: "Permission denied" error?
**A:** The printer may have:
- File system restrictions
- Authentication enabled
- Read-only volume
- Security lockdown

Try:
- Different paths
- Different volumes (0:, 1:, 2:)
- Unlock printer first
- Check security settings

---

## 🎯 Feature Questions

### Q: Can PrinterReaper print documents?
**A:** Yes, use the `print` command:
```bash
> print document.pdf
> print "Hello World"
```

### Q: Can I capture print jobs from other users?
**A:** Yes, if the printer supports job retention:
```bash
> hold          # Enable retention
> capture       # Start capturing
```
**⚠️ Legal warning**: Only with authorization!

### Q: Can I backup printer configuration?
**A:** Yes, use the `backup` command:
```bash
> backup config.bak
```

### Q: Can PrinterReaper test for specific CVEs?
**A:** PrinterReaper provides tools to test for common vulnerability types:
- Path traversal (like CVE-2017-8011)
- Authentication bypass
- Buffer overflows
- Information disclosure

Use `traverse`, `flood`, `unlock_bruteforce` commands.

---

## 🔍 Advanced Questions

### Q: How does filesystem mirroring work?
**A:** The `mirror` command:
1. Recursively lists all files using `find`
2. Downloads each file using `download`
3. Recreates directory structure locally
4. Preserves file hierarchy

### Q: What is NVRAM and why is it important?
**A:** NVRAM (Non-Volatile RAM) stores:
- Printer settings
- Passwords
- Network configuration
- Print job history

Access it with: `nvram dump`

### Q: Can I test without connecting to a real printer?
**A:** Not currently. PrinterReaper requires a target device. For testing, consider:
- Using a dedicated test printer
- Setting up a printer emulator
- Using a virtual printer (limited functionality)

### Q: How do I contribute to PrinterReaper?
**A:** See [Contributing](Contributing) guide. We welcome:
- Bug reports
- New features
- Documentation improvements
- Security research

---

## 📊 Performance Questions

### Q: How fast is network discovery?
**A:** Discovery speed depends on:
- Network size (number of hosts)
- Network latency
- SNMP timeout (default 1 second)
- Number of printers

Typical: ~2-5 minutes for /24 network

### Q: Can discovery be made faster?
**A:** Currently sequential. Parallel scanning planned for v2.3.5 which will be much faster.

### Q: Why is download slow?
**A:** Large files over network take time. Monitor progress:
```bash
> debug          # Enable to see progress
> download large_file.dat
```

---

## 🛡️ Safety Questions

### Q: Can PrinterReaper damage printers?
**A:** Some commands can cause damage:
- `destroy` - ⚠️⚠️⚠️ Physical NVRAM damage
- `format` - ⚠️⚠️ Erases filesystem
- `reset` - ⚠️ Factory reset
- `flood` - ⚠️ May crash printer

Always read warnings and use only with permission!

### Q: How do I undo changes?
**A:** Best practices:
1. **Backup first**: `> backup before_changes.cfg`
2. **Document changes**: Keep notes
3. **Restore if needed**: `> restore before_changes.cfg`

Some operations cannot be undone:
- ❌ `destroy` - Permanent damage
- ❌ `format` - Data erased
- ❌ `delete` - Files removed

---

## 📖 Documentation Questions

### Q: Where can I find command documentation?
**A:** Multiple sources:
- **In-shell**: `help <command>`
- **Wiki**: [Commands Reference](Commands-Reference)
- **Detailed**: [PJL Commands](PJL-Commands)

### Q: Are there usage examples?
**A:** Yes! See:
- [Examples](Examples) - Real-world scenarios
- [Quick Start](Quick-Start) - Beginner tutorial
- [Security Testing](Security-Testing) - Professional workflows

### Q: How do I report bugs?
**A:** Open an issue on GitHub with:
- PrinterReaper version
- Operating system
- Printer model
- Steps to reproduce
- Error messages

---

## 🎓 Learning Questions

### Q: I'm new to printer hacking. Where do I start?
**A:** Follow this learning path:
1. Read [Quick Start](Quick-Start) - 5-minute tutorial
2. Practice on test printer
3. Learn [Commands Reference](Commands-Reference)
4. Study [Examples](Examples)
5. Read [Security Testing](Security-Testing)

### Q: What is PJL?
**A:** PJL (Printer Job Language) is a printer control language developed by HP. It allows:
- Printer control
- Job management
- File system access
- Configuration changes

### Q: What resources do you recommend?
**A:** Essential resources:
- [HP PJL Technical Reference](http://h10032.www1.hp.com/ctg/Manual/bpl13208.pdf)
- [Hacking Printers Wiki](http://hacking-printers.net)
- PrinterReaper Wiki (this site!)

---

## 🤝 Community Questions

### Q: Is there a Discord/Slack for PrinterReaper?
**A:** Not yet! For now:
- GitHub Issues - Bug reports
- GitHub Discussions - Q&A
- X/LinkedIn @mrhenrike - Contact

### Q: Can I request features?
**A:** Yes! Open a GitHub issue with:
- Feature description
- Use case
- Why it's needed
- Proposed implementation (optional)

### Q: How can I help?
**A:** Many ways to contribute:
- Report bugs
- Submit fixes
- Improve documentation
- Add examples
- Test on different printers
- Security research

---

## 🔧 Still Have Questions?

- **Search the Wiki** - Use GitHub's search feature
- **Check Troubleshooting** - [Troubleshooting Guide](Troubleshooting)
- **Read Examples** - [Practical Examples](Examples)
- **Open an Issue** - GitHub Issues
- **Contact** - X / LinkedIn @mrhenrike

---

<div align="center">

**FAQ**  
Can't find your answer? Open an issue on GitHub!

**→ [Next: Troubleshooting](Troubleshooting)**

</div>

