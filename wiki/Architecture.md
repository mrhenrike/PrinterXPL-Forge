# 🏗️ Architecture Overview

Technical architecture and design of PrinterReaper.

---

## 📊 System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     PrinterReaper v2.3.4                       │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                        main.py (Entry Point)                   │
├────────────────────────────────────────────────────────────────┤
│  - Argument parsing                                            │
│  - OS detection (osdetect.py)                                  │
│  - Capability detection (capabilities.py)                      │
│  - Discovery mode / Direct connection                          │
└───────────┬────────────────────────────────────┬───────────────┘
            │                                    │
            ▼                                    ▼
    ┌───────────────┐                  ┌─────────────────┐
    │ discovery.py  │                  │  Language Shell │
    ├───────────────┤                  │   (pjl.py)      │
    │ - SNMP scan   │                  └────────┬────────┘
    │ - Network enum│                           │
    │ - Device list │                           │
    └───────────────┘                           │
                                                ▼
                                    ┌───────────────────────┐
                                    │   printer.py (Base)   │
                                    ├───────────────────────┤
                                    │  - Connection mgmt    │
                                    │  - Command execution  │
                                    │  - File operations    │
                                    │  - Error handling     │
                                    └──────────┬────────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
                 ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
                 │  helper.py  │      │  codebook.py │      │  fuzzer.py   │
                 ├─────────────┤      ├──────────────┤      ├──────────────┤
                 │ - output()  │      │ - Error codes│      │ - Fuzz paths │
                 │ - conv()    │      │ - get_errors│      │ - Fuzz data  │
                 │ - file()    │      └──────────────┘      └──────────────┘
                 │ - conn()    │
                 │ - log()     │
                 └─────────────┘
```

---

## 📂 Directory Structure

```
PrinterReaper/
├── printer-reaper.py           # Main executable (wrapper)
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
├── README.md                   # Main documentation
├── CHANGELOG.md                # Version history
│
├── src/                        # Source code
│   ├── main.py                 # Entry point
│   ├── version.py              # Version info
│   │
│   ├── core/                   # Core modules
│   │   ├── printer.py          # Base printer class
│   │   ├── capabilities.py     # Capability detection
│   │   ├── discovery.py        # Network discovery
│   │   ├── osdetect.py         # OS detection
│   │   └── db/                 # Databases
│   │       ├── pjl.dat         # PJL printer models
│   │       └── README          # DB documentation
│   │
│   ├── modules/                # Language modules
│   │   └── pjl.py              # PJL implementation
│   │
│   └── utils/                  # Utilities
│       ├── helper.py           # Helper functions
│       ├── codebook.py         # Error code database
│       ├── fuzzer.py           # Fuzzing vectors
│       └── operators.py        # PS operators (reserved)
│
├── wiki/                       # GitHub Wiki (v2.3.4+)
│   ├── Home.md
│   ├── Installation.md
│   ├── Quick-Start.md
│   └── ...
│
├── exfiltrated/                # Downloaded files (created at runtime)
└── deleted/                    # Archived old files
```

---

## 🔧 Core Components

### main.py - Entry Point

**Responsibilities:**
- Parse command-line arguments
- Detect operating system
- Perform capability checks
- Initialize appropriate shell (PJL/PS/PCL)
- Handle errors and exit gracefully

**Key Functions:**
```python
def get_args()              # Parse CLI arguments
def intro()                 # Display banner
def main()                  # Main program flow
```

---

### printer.py - Base Class

**Responsibilities:**
- Connection management
- File transfer operations
- Command execution framework
- Error handling
- Signal handling
- Timeout management

**Key Methods:**
```python
def do_open()               # Connect to printer
def do_close()              # Disconnect
def do_upload()             # Upload file
def do_download()           # Download file
def cmd_with_retry()        # Execute with retry
def setup_signal_handlers() # Handle Ctrl+C
```

**Inheritance:**
```python
class printer(cmd.Cmd):
    # All shells inherit from this
```

---

### pjl.py - PJL Module

**Responsibilities:**
- PJL command implementation
- PJL-specific operations
- Error code interpretation
- File system operations
- Security testing commands

**Key Features:**
- 54 PJL commands
- 7 command categories
- Full help documentation
- Error handling via codebook

**Inheritance:**
```python
class pjl(printer):
    def cmd()               # Send PJL command
    def pjl_err()           # Handle errors
    # 54 do_* commands
    # 54 help_* methods
```

---

### discovery.py - Network Scanner

**Responsibilities:**
- SNMP-based printer discovery
- Network interface enumeration
- Multi-OS support
- Printer information gathering

**Key Functions:**
```python
def _get_local_networks()   # Find local networks
def _snmp_get()             # SNMP query
class discovery()           # Main scanner
```

**SNMP OIDs Queried** (17):
- Device type & description
- System uptime
- Printer status
- Supply levels
- Entity information

---

### capabilities.py - Detection

**Responsibilities:**
- Detect PJL/PS/PCL support
- Query via IPP, SNMP, HTTP, HTTPS
- Model database lookup
- Safe mode verification

**Detection Methods:**
```python
def ipp()                   # IPP detection
def http()                  # HTTP detection
def https()                 # HTTPS detection
def snmp()                  # SNMP detection
```

---

## 🔌 Connection Flow

```
1. User runs: python3 printer-reaper.py <target> pjl
                    │
                    ▼
2. main.py parses arguments
                    │
                    ▼
3. capabilities.py detects PJL support (if --safe)
                    │
                    ▼
4. pjl() class instantiated
                    │
                    ▼
5. printer.do_open() connects to target:9100
                    │
                    ▼
6. Connection established via socket
                    │
                    ▼
7. pjl.on_connect() sends initial commands
                    │
                    ▼
8. Shell ready for user input
                    │
                    ▼
9. User enters commands → cmd.Cmd.onecmd()
                    │
                    ▼
10. pjl.do_<command>() executes
                    │
                    ▼
11. pjl.cmd() sends PJL command
                    │
                    ▼
12. conn.send() → Socket → Printer
                    │
                    ▼
13. conn.recv() ← Socket ← Printer
                    │
                    ▼
14. pjl_err() parses errors
                    │
                    ▼
15. Result displayed to user
```

---

## 📡 Communication Protocol

### PJL Command Format

```
┌─────────────────────────────────────────────────────────┐
│ Universal Exit Language (UEL)                           │
│ %-12345X                                                │
├─────────────────────────────────────────────────────────┤
│ PJL Command                                             │
│ @PJL <COMMAND> <PARAMETER>=<VALUE>                      │
├─────────────────────────────────────────────────────────┤
│ Echo Token (for response delimiting)                    │
│ @PJL ECHO DELIMITER<random>                             │
├─────────────────────────────────────────────────────────┤
│ Universal Exit Language (UEL)                           │
│ %-12345X                                                │
└─────────────────────────────────────────────────────────┘

Response:
<Data>
@PJL ECHO DELIMITER<random>
```

### Example Transaction

**Send:**
```
%-12345X
@PJL INFO ID
@PJL ECHO DELIMITER42
%-12345X
```

**Receive:**
```
HP LaserJet 4250
@PJL ECHO DELIMITER42
```

---

## 🔄 Data Flow

### File Upload Flow

```
User Command:
> upload local.txt 0:/remote.txt

    │
    ▼
1. pjl.do_upload("local.txt 0:/remote.txt")
    │
    ▼
2. Read local file: file().read("local.txt")
    │
    ▼
3. Calculate size: len(data)
    │
    ▼
4. Build PJL command:
   @PJL FSUPLOAD NAME="0:/remote.txt" OFFSET=0 LENGTH=<size>
    │
    ▼
5. Send via pjl.cmd()
    │
    ▼
6. conn.send() → Socket → Printer
    │
    ▼
7. Send file data: conn.send(data)
    │
    ▼
8. Wait for confirmation
    │
    ▼
9. Parse response, check errors
    │
    ▼
10. Display result to user
```

---

## 🗄️ Database Structure

### pjl.dat - Printer Models Database

```
# Format: One model per line
HP LaserJet 4200
HP LaserJet 4250
HP LaserJet 4300
HP LaserJet 4350
Brother MFC-7860DW
Epson WorkForce WF-7720
...
```

**Usage:**
- Capability detection via model matching
- Safe mode verification
- Feature prediction

---

## 🔐 Error Handling Architecture

### Error Code System

```
User Command → PJL Command → Printer
                               │
                               ▼
                          Response
                               │
                               ▼
                          pjl_err()
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
          fileerror()                   showstatus()
                │                             │
                ▼                             ▼
        Check for:                  Parse CODE= and DISPLAY=
        - File errors                        │
        - Access denied                      ▼
        - Not found              codebook().get_errors(code)
                │                             │
                ▼                             ▼
           Display error              Display status with
           to user                    error description
```

### Error Code Categories (codebook.py)

```
10xxx - Informational Messages
20xxx - PJL Parser Errors
30xxx - Auto-Continuable Conditions
32xxx - File System Errors
40xxx - Operator Intervention Required
50xxx - Hardware Errors
```

---

## 🔌 Connection Architecture

### Socket Management

```python
class conn():
    def __init__(mode, debug, quiet):
        self._sock = socket()      # TCP socket
        self._file = None          # Or file descriptor for USB
    
    def open(target, port=9100):
        # Connect to target:port
        self._sock.connect((target, port))
    
    def send(data):
        # Send with error handling
        self._sock.sendall(data)
    
    def recv(bytes):
        # Receive with timeout
        self._sock.recv(bytes)
    
    def recv_until(delimiter):
        # Read until delimiter found
        # Implements timeout and watchdog
```

**Features:**
- 30-second timeout
- Watchdog for stalled connections
- Graceful error handling
- Support for both socket and file descriptor

---

## 🧩 Module Relationships

```
main.py
  ├─imports─> osdetect.py (get_os)
  ├─imports─> discovery.py (discovery)
  ├─imports─> capabilities.py (capabilities)
  ├─imports─> pjl.py (pjl)
  └─imports─> helper.py (output)

pjl.py
  ├─inherits─> printer.py
  ├─imports─> codebook.py (get_errors)
  └─imports─> helper.py (log, output, conv, file, const)

printer.py
  ├─imports─> discovery.py
  ├─imports─> fuzzer.py
  └─imports─> helper.py (all utilities)

discovery.py
  ├─imports─> osdetect.py (get_os)
  └─imports─> helper.py (output, conv)

capabilities.py
  └─imports─> helper.py (output, item)
```

---

## 🎯 Design Patterns

### Command Pattern

PrinterReaper uses Python's `cmd.Cmd` module:

```python
class pjl(printer):
    # Command implementation
    def do_upload(self, arg):
        # Execute upload
    
    # Help documentation
    def help_upload(self):
        # Display help
```

**Benefits:**
- Automatic command dispatching
- Built-in help system
- Tab completion support
- Command history

---

### Inheritance Hierarchy

```
cmd.Cmd (Python standard library)
    │
    ▼
printer (Base class - printer.py)
    ├─ Connection management
    ├─ File operations
    ├─ Error handling
    └─ Generic commands
    │
    ▼
pjl (PJL implementation - pjl.py)
    ├─ PJL-specific commands
    ├─ Error code handling
    └─ 54 PJL commands

Future:
    ▼
ps (PostScript - v2.4.0)
    └─ PostScript commands

    ▼
pcl (PCL - v2.5.0)
    └─ PCL commands
```

---

## 🔄 Command Execution Flow

### Standard Command Flow

```python
1. User types: "upload test.txt"
       │
       ▼
2. cmd.Cmd.onecmd("upload test.txt")
       │
       ▼
3. cmd.Cmd.default() → pjl.do_upload("test.txt")
       │
       ▼
4. pjl.do_upload():
   - Parse arguments
   - Read local file
   - Build PJL command
       │
       ▼
5. pjl.cmd("@PJL FSUPLOAD...")
   - Add UEL
   - Add echo token
   - Log command
       │
       ▼
6. conn.send(payload)
   - Send over socket
   - Debug output if enabled
       │
       ▼
7. conn.recv_until(token)
   - Receive response
   - Wait for delimiter
   - Timeout protection
       │
       ▼
8. pjl_err(response)
   - Check for errors
   - Parse status codes
   - Handle file errors
       │
       ▼
9. output().info("Uploaded...")
   - Display result to user
```

---

## 🛠️ Utility Classes

### helper.py Components

**Class: output()**
```python
Methods:
- message()     # Cyan messages
- warning()     # Red warnings
- error()       # Red errors
- info()        # Blue info
- raw()         # Yellow raw data
- green()       # Green success
```

**Class: conv()**
```python
Methods:
- now()         # Current timestamp
- elapsed()     # Time elapsed
- filesize()    # Human-readable size
- hex()         # String to hex
- int()         # Safe integer conversion
```

**Class: file()**
```python
Methods:
- read()        # Read local file
- write()       # Write local file
- append()      # Append to file
```

**Class: conn()**
```python
Methods:
- open()        # Open connection
- close()       # Close connection
- send()        # Send data
- recv()        # Receive data
- recv_until()  # Receive until delimiter
- timeout()     # Set timeout
```

---

## 🎨 Color Scheme

PrinterReaper uses colorama for cross-platform colors:

```python
Color Usage:
- CYAN (Bright)    - User messages
- BLUE (Back)      - Info messages
- YELLOW           - Raw data
- MAGENTA (Back)   - Received data
- CYAN (Back)      - Sent data
- RED (Back/Fore)  - Errors
- GREEN (Back)     - Success
- DIM              - Chit-chat
```

---

## 📊 State Management

### Printer State

```python
class printer:
    # Connection state
    conn = None             # Connection object
    target = ""             # Target IP/hostname
    
    # Filesystem state
    vol = ""                # Current volume
    cwd = ""                # Current working directory
    traversal = ""          # Traversal root
    
    # Configuration
    timeout = 30            # Command timeout
    debug = False           # Debug mode
    quiet = False           # Quiet mode
    logfile = None          # Log file handle
    
    # Control
    interrupted = False     # Interrupt flag
    should_exit = False     # Exit flag
```

---

## 🔒 Security Architecture

### Safe Mode

When `--safe` flag is used:

```python
1. capabilities.__init__(args):
   - Test IPP support
   - Test HTTP support  
   - Test HTTPS support
   - Test SNMP support
   
2. Check if PJL is supported
   
3. If NOT supported:
   - Display warning
   - Exit (in safe mode)
   
4. If supported:
   - Continue with connection
```

### Error Handling Layers

```
Layer 1: Python Exceptions
    ├─ ConnectionResetError
    ├─ BrokenPipeError
    ├─ socket.timeout
    └─ KeyboardInterrupt

Layer 2: PJL Error Codes
    └─ codebook().get_errors()

Layer 3: File System Errors
    ├─ File not found
    ├─ Permission denied
    └─ Access denied

Layer 4: User-Friendly Messages
    └─ output().errmsg()
```

---

## 📈 Performance Optimizations

### Current Optimizations

1. **OS Detection Caching**
   ```python
   _cached_os = None
   def get_os():
       if _cached_os:
           return _cached_os
   ```

2. **Connection Retry Logic**
   ```python
   def cmd_with_retry(command, max_retries=3):
       for attempt in range(max_retries):
           try:
               return self.cmd(command)
           except:
               if attempt == max_retries - 1:
                   raise
   ```

3. **Timeout Management**
   - 30-second default timeout
   - Configurable per command
   - Watchdog for stalled connections

### Planned Optimizations (v2.3.5+)

1. **Parallel Network Scanning**
   - ThreadPoolExecutor for concurrent scans
   - 10x faster discovery

2. **Connection Pooling**
   - Reuse connections
   - Faster command execution

3. **Response Caching**
   - Cache static info (id, network)
   - Reduce redundant queries

---

## 🧪 Testing Architecture

### Debug Mode

```python
if self.debug:
    output().send(data)     # Show sent data
    output().recv(data)     # Show received data
```

### Logging

```python
if self.logfile:
    log().write(self.logfile, command)  # Log commands
    log().comment(self.logfile, note)   # Log comments
```

---

## 🔮 Future Architecture (v2.4.0+)

### PostScript Module

```
modules/
├── pjl.py              # Current
└── ps.py               # v2.4.0
    ├─imports─> operators.py
    └─implements─> PostScript commands
```

### PCL Module

```
modules/
├── pjl.py              # Current
├── ps.py               # v2.4.0
└── pcl.py              # v2.5.0
    └─implements─> PCL commands
```

---

## 📊 Code Statistics

```
Total Lines:        ~6,000
Modules:                  9
Commands:                54
Help Methods:            54
Error Codes:           450+
Fuzzing Vectors:       200+
Test Coverage:         100%
```

---

## 🔧 Extension Points

### Adding New Commands

```python
# In pjl.py or ps.py

def do_mycommand(self, arg):
    """Command docstring"""
    # Implementation
    result = self.cmd("@PJL MYCMD " + arg)
    output().info(result)

def help_mycommand(self):
    """Help method"""
    print("mycommand - Description")
    print("Usage: mycommand <arg>")
```

### Adding New Language Module

```python
# Create modules/newlang.py

from core.printer import printer

class newlang(printer):
    def __init__(self, args):
        super().__init__(args)
        # Language-specific init
    
    def cmd(self, str_send):
        # Language-specific command sending
        pass
    
    # Implement language-specific commands
```

---

## 📚 Related Pages

- **[Installation](Installation)** - Setup guide
- **[Quick Start](Quick-Start)** - Getting started
- **[Contributing](Contributing)** - Development guide

---

<div align="center">

**Architecture Overview**  
Technical design and implementation details

**→ [Next: Contributing](Contributing)**

</div>

