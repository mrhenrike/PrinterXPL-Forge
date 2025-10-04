# 📖 Commands Reference

Complete reference of all PrinterReaper commands organized by category.

---

## 📋 Command Categories

PrinterReaper features **54 commands** across **7 categories**:

| Category | Commands | Description |
|----------|----------|-------------|
| 📁 Filesystem | 12 | File and directory operations |
| ℹ️ Information | 8 | System information gathering |
| ⚙️ Control | 8 | Printer control and configuration |
| 🔒 Security | 4 | Security testing and access control |
| 💥 Attacks | 8 | Exploitation and attack vectors |
| 🌐 Network | 3 | Network and connectivity |
| 📊 Monitoring | 2 | Status and monitoring |
| 🛠️ Shell | 9 | Shell control commands |

---

## 📁 Filesystem Commands (12)

### ls
**Description**: List directory contents  
**Usage**: `ls [path]`  
**Example**: `ls /etc`

### mkdir
**Description**: Create remote directory  
**Usage**: `mkdir <directory>`  
**Example**: `mkdir /tmp/test`

### find
**Description**: Recursively list all files  
**Usage**: `find [path]`  
**Example**: `find /webServer`

### upload
**Description**: Upload file to printer  
**Usage**: `upload <local_file> [remote_path]`  
**Example**: `upload config.txt 0:/config.txt`

### download
**Description**: Download file from printer  
**Usage**: `download <remote_file> [local_path]`  
**Example**: `download /etc/passwd ./passwd`

### pjl_delete
**Description**: Delete remote file using PJL  
**Usage**: `pjl_delete <file>`  
**Example**: `pjl_delete /tmp/test.log`

### copy
**Description**: Copy remote file  
**Usage**: `copy <source> <destination>`  
**Example**: `copy config.cfg config.bak`

### move
**Description**: Move/rename remote file  
**Usage**: `move <source> <destination>`  
**Example**: `move old.cfg new.cfg`

### touch
**Description**: Create empty file or update timestamp  
**Usage**: `touch <file>`  
**Example**: `touch /tmp/marker`

### chmod
**Description**: Change file permissions  
**Usage**: `chmod <permissions> <file>`  
**Example**: `chmod 644 config.cfg`

### permissions
**Description**: Test file permissions  
**Usage**: `permissions <file>`  
**Example**: `permissions /etc/shadow`

### rmdir
**Description**: Remove remote directory  
**Usage**: `rmdir <directory>`  
**Example**: `rmdir /tmp/old`

### mirror
**Description**: Mirror remote filesystem locally  
**Usage**: `mirror [path]`  
**Example**: `mirror 0:/`

---

## ℹ️ Information Commands (8)

### id
**Description**: Show printer identification  
**Usage**: `id`  
**Example**: `id`

### variables
**Description**: List all environment variables  
**Usage**: `variables`  
**Example**: `variables`

### printenv
**Description**: Show specific environment variable  
**Usage**: `printenv <VAR>`  
**Example**: `printenv TIMEOUT`

### network
**Description**: Show network information  
**Usage**: `network`  
**Example**: `network`

### info
**Description**: Get printer information  
**Usage**: `info <category>`  
**Categories**: config, filesys, id, memory, pagecount, status, variables  
**Example**: `info config`

### scan_volumes
**Description**: Scan all available volumes  
**Usage**: `scan_volumes`  
**Example**: `scan_volumes`

### firmware_info
**Description**: Get firmware information  
**Usage**: `firmware_info`  
**Example**: `firmware_info`

### pagecount
**Description**: Show or manipulate page counter  
**Usage**: `pagecount [number]`  
**Example**: `pagecount 1000`

---

## ⚙️ Control Commands (8)

### set
**Description**: Set environment variable  
**Usage**: `set <VAR=VALUE>`  
**Example**: `set TIMEOUT=90`

### display
**Description**: Set printer's display message  
**Usage**: `display <message>`  
**Example**: `display "Under Maintenance"`

### offline
**Description**: Take printer offline  
**Usage**: `offline <message>`  
**Example**: `offline "System Upgrade"`

### restart
**Description**: Restart printer  
**Usage**: `restart`  
**Example**: `restart`

### reset
**Description**: Reset to factory defaults  
**Usage**: `reset`  
**Example**: `reset`

### selftest
**Description**: Perform printer self-tests  
**Usage**: `selftest`  
**Example**: `selftest`

### backup
**Description**: Backup printer configuration  
**Usage**: `backup <filename>`  
**Example**: `backup config.backup`

### restore
**Description**: Restore printer configuration  
**Usage**: `restore <filename>`  
**Example**: `restore config.backup`

---

## 🔒 Security Commands (4)

### lock
**Description**: Lock control panel and disk  
**Usage**: `lock [PIN]`  
**Example**: `lock 12345`

### unlock
**Description**: Unlock control panel and disk  
**Usage**: `unlock [PIN]`  
**Example**: `unlock 12345`

### disable
**Description**: Disable printer functionality  
**Usage**: `disable`  
**Example**: `disable`

### nvram
**Description**: Access/manipulate NVRAM  
**Usage**: `nvram <dump|set|get> [options]`  
**Example**: `nvram dump`

---

## 💥 Attack Commands (8)

### destroy
**Description**: ⚠️ Cause physical NVRAM damage  
**Usage**: `destroy`  
**Example**: `destroy`  
**Warning**: May permanently damage printer!

### flood
**Description**: Flood input to test buffer overflows  
**Usage**: `flood [size]`  
**Example**: `flood 50000`

### hold
**Description**: Enable job retention  
**Usage**: `hold`  
**Example**: `hold`

### format
**Description**: ⚠️ Format printer's file system  
**Usage**: `format`  
**Example**: `format`  
**Warning**: Erases all data!

### capture
**Description**: Capture print jobs  
**Usage**: `capture`  
**Example**: `capture`

### overlay
**Description**: Add overlay to all prints  
**Usage**: `overlay <file>`  
**Example**: `overlay logo.eps`

### cross
**Description**: Add watermark to prints  
**Usage**: `cross <text>`  
**Example**: `cross "CONFIDENTIAL"`

### traverse
**Description**: Path traversal attack  
**Usage**: `traverse`  
**Example**: `traverse`

---

## 🌐 Network Commands (3)

### direct
**Description**: Show direct-print configuration  
**Usage**: `direct`  
**Example**: `direct`

### execute
**Description**: Execute arbitrary PJL command  
**Usage**: `execute <command>`  
**Example**: `execute @PJL INFO STATUS`

### load
**Description**: Run commands from file  
**Usage**: `load <filename>`  
**Example**: `load commands.txt`

---

## 📊 Monitoring Commands (2)

### pagecount
**Description**: Show/manipulate page counter  
**Usage**: `pagecount [number]`  
**Example**: `pagecount`

### status
**Description**: Toggle status messages  
**Usage**: `status`  
**Example**: `status`

---

## 🛠️ Shell Control Commands (9)

### help
**Description**: List commands or get help  
**Usage**: `help [command]`  
**Example**: `help upload`

### debug
**Description**: Toggle debug mode  
**Usage**: `debug`  
**Example**: `debug`

### loop
**Description**: Run command repeatedly  
**Usage**: `loop <command> <arg1> <arg2> ...`  
**Example**: `loop download file1 file2 file3`

### discover
**Description**: Scan for printers on network  
**Usage**: `discover`  
**Example**: `discover`

### open
**Description**: Connect to new target  
**Usage**: `open <target>`  
**Example**: `open 192.168.1.105`

### close
**Description**: Disconnect from printer  
**Usage**: `close`  
**Example**: `close`

### timeout
**Description**: Set connection timeout  
**Usage**: `timeout <seconds>`  
**Example**: `timeout 30`

### reconnect
**Description**: Reconnect to current printer  
**Usage**: `reconnect`  
**Example**: `reconnect`

### exit
**Description**: Exit PrinterReaper shell  
**Usage**: `exit`  
**Example**: `exit`

---

## 🎯 Command Quick Reference Table

| Command | Category | Risk | Description |
|---------|----------|------|-------------|
| ls | Filesystem | 🟢 Safe | List files |
| upload | Filesystem | 🟡 Modify | Upload file |
| download | Filesystem | 🟢 Safe | Download file |
| delete | Filesystem | 🟡 Modify | Delete file |
| copy | Filesystem | 🟡 Modify | Copy file |
| move | Filesystem | 🟡 Modify | Move file |
| id | Information | 🟢 Safe | Get ID |
| network | Information | 🟢 Safe | Get network info |
| variables | Information | 🟢 Safe | List variables |
| set | Control | 🟡 Modify | Set variable |
| display | Control | 🟡 Modify | Set display |
| restart | Control | 🟠 Disruptive | Restart printer |
| reset | Control | 🔴 Destructive | Factory reset |
| lock | Security | 🟠 Disruptive | Lock panel |
| unlock | Security | 🟡 Modify | Unlock panel |
| nvram | Security | 🟡 Modify | Access NVRAM |
| destroy | Attack | 🔴 Destructive | Damage NVRAM |
| flood | Attack | 🟠 Disruptive | Buffer overflow test |
| format | Attack | 🔴 Destructive | Format filesystem |
| execute | Network | 🟡 Modify | Raw PJL command |

**Risk Levels:**
- 🟢 **Safe** - Read-only, no impact
- 🟡 **Modify** - Changes configuration
- 🟠 **Disruptive** - May interrupt service
- 🔴 **Destructive** - May cause permanent damage

---

## 🔍 Finding the Right Command

### I want to...

**...get printer information**
→ `id`, `network`, `info config`, `variables`

**...explore the filesystem**
→ `ls`, `find`, `pwd`, `cd`

**...download files**
→ `download`, `mirror`, `cat`

**...upload files**
→ `upload`, `copy`, `move`

**...test security**
→ `permissions`, `traverse`, `lock`, `unlock`

**...cause disruption**
→ `offline`, `restart`, `flood`, `disable`

**...backup configuration**
→ `backup`, `download`, `mirror`

**...capture print jobs**
→ `hold`, `capture`

**...test for vulnerabilities**
→ `flood`, `traverse`, `permissions`, `fuzz`

---

## 📚 Related Pages

- **[PJL Commands](PJL-Commands)** - Detailed PJL command documentation
- **[Security Testing](Security-Testing)** - Security testing workflows
- **[Attack Vectors](Attack-Vectors)** - Exploitation techniques
- **[Examples](Examples)** - Practical usage examples

---

<div align="center">

**Command Reference**  
For detailed help on any command, use `help <command>` in the shell

**→ [Next: PJL Commands Details](PJL-Commands)**

</div>

