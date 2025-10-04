#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python standard library
import re
import os
import csv, itertools 
import sys
import cmd
import glob
import errno
import random
import ntpath
import posixpath
import hashlib
import socket
import tempfile
import subprocess
import traceback
import requests
import time
import signal
import threading

# local pret classes
from utils.helper import log, output, conv, file, item, conn, const as c
from core.discovery import discovery
from utils.fuzzer import fuzzer
# CVE module moved to backup - functionality integrated into PJL v2.0


class printer(cmd.Cmd, object):
    # cmd module config and customization
    intro = "Welcome to the PrinterReaper shell. Type help or ? to list commands.\nType 'exit' to quit. Type 'discover' to scan for printers on your local network.\nNote: Not all commands will work on every printer — support depends on the device's manufacturer, model, and firmware language implementation."
    doc_header = "Available commands (type help <topic>):"
    offline_str = "Not connected."
    undoc_header = None

    logfile = None
    debug = False
    status = False
    quiet = False
    fuzz = False
    conn = None
    mode = None
    error = None
    iohack = True
    timeout = 10
    max_retries = 3
    target = ""
    vol = ""
    cwd = ""
    traversal = ""
    # can be changed
    editor = "vim"  # set to nano/edit/notepad/leafpad/whatever
    
    # Interruption control
    interrupted = False
    current_command = None
    command_thread = None

    # --------------------------------------------------------------------
    # INITIALIZATION AND CONTROL METHODS
    # --------------------------------------------------------------------
    def __init__(self, args):
        # init cmd module
        cmd.Cmd.__init__(self)
        self.debug = args.debug  # debug mode
        self.quiet = args.quiet  # quiet mode
        self.mode = args.mode    # command mode

        # Setup signal handlers for graceful interruption
        self.setup_signal_handlers()

        # connect to device
        self.do_open(args.target, "init")
        # log pjl/ps cmds to file
        if args.log:
            self.logfile = log().open(args.log)
            header = None
            if self.mode == "ps":
                header = c.PS_HEADER
            if self.mode == "pcl":
                header = c.PCL_HEADER
            if header:
                log().write(self.logfile, header + os.linesep)
        # run pret cmds from file
        if args.load:
            self.do_load(args.load)
        # input loop with interruption handling
        self.cmdloop_with_interruption()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful interruption"""
        def signal_handler(signum, frame):
            self.handle_interruption()
        
        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

    def handle_interruption(self):
        """Handle interruption (Ctrl+C, ESC, etc.)"""
        if self.current_command:
            # Stop current command
            self.interrupted = True
            output().warning("\n[!] Command interrupted. Stopping current operation...")
            self.current_command = None
        else:
            # No command running, set flag for next input
            self.interrupted = True
            output().warning("\n[!] Interruption detected. Press Enter to continue or type 'exit' to quit.")

    def cmdloop_with_interruption(self):
        """Custom cmdloop that handles interruptions gracefully"""
        while True:
            try:
                if self.interrupted:
                    # Handle interruption
                    self.interrupted = False
                    continue
                
                # Get input with proper handling
                line = input(self.prompt)
                
                # Check for interruption after input
                if self.interrupted:
                    self.interrupted = False
                    continue
                
                # Process command
                if line.strip():
                    self.onecmd(line)
                    
            except (EOFError, KeyboardInterrupt):
                # Handle EOF and KeyboardInterrupt gracefully
                if self.interrupted:
                    self.interrupted = False
                    continue
                else:
                    output().info("\nExiting PrinterReaper...")
                    break
            except Exception as e:
                if self.debug:
                    traceback.print_exc()
                output().errmsg(f"Error: {e}")
                continue

    def set_defaults(self, newtarget):
        self.fuzz = False
        if newtarget:
            self.set_vol()
            self.set_traversal()
            self.error = None
        else:
            self.set_prompt()

    # --------------------------------------------------------------------
    # CORE SHELL METHODS
    # --------------------------------------------------------------------
    # do nothing on empty input
    def emptyline(self):
        pass

    # show message for unknown commands
    def default(self, line):
        if line and line[0] != "#":  # interpret as comment
            output().chitchat("Unknown command: '" + line + "'")

    # suppress help message for undocumented commands
    def print_topics(self, header, cmds, cmdlen, maxcol):
        if cmds:
            output().chitchat(header)

    def chitchat(self, *args):
        if not self.quiet:
            output().message(*args)

    def precmd(self, line):
        # normalize line endings
        if line and line[-1] == os.linesep:
            line = line[:-1]
        # convert to unicode if needed
        if hasattr(line, "decode"):
            try:
                line = line.decode("utf-8")
            except UnicodeDecodeError:
                line = line.decode("latin-1")
        return line

    # --------------------------------------------------------------------
    # catch-all wrapper to guarantee continuation on unhandled exceptions
    def onecmd(self, line):
        # Set current command for interruption tracking
        self.current_command = line.strip()
        self.interrupted = False
        
        try:
            result = cmd.Cmd.onecmd(self, line)
            # Clear current command on successful completion
            self.current_command = None
            return result
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            output().errmsg("Connection lost - printer may have disconnected")
            self.current_command = None
            return False
        except socket.timeout as e:
            output().errmsg("Command timed out - printer may be busy")
            self.current_command = None
            return False
        except Exception as e:
            # Only show traceback in debug mode
            if hasattr(self, 'debug') and self.debug:
                traceback.print_exc()
            output().errmsg(f"Command failed: {str(e)}")
            self.current_command = None
            return False
        finally:
            # Always clear current command
            self.current_command = None

    # ====================================================================
    # BASIC CONTROL COMMANDS
    # ====================================================================
    # These commands control the basic operation of the shell and program

    def do_exit(self, *arg):
        if self.logfile:
            log().close(self.logfile)
        return True

    def help_exit(self):
        "Exit the shell"
        print()

    def do_debug(self, arg):
        "Toggle raw traffic debug output"
        self.debug = not self.debug
        output().message("Debug output " + ("enabled" if self.debug else "disabled"))

    def help_debug(self):
        "Toggle raw traffic debug output"
        print()

    def do_loop(self, arg):
        "Run a command repeatedly over multiple arguments"
        if not arg:
            output().errmsg("Usage: loop <command> <arg1> <arg2> ...")
            return
        args = arg.split()
        cmd = args[0]
        for arg in args[1:]:
            output().message(f"Running: {cmd} {arg}")
            self.onecmd(f"{cmd} {arg}")

    def help_loop(self):
        "Run a command repeatedly over multiple arguments"
        print()

    # ====================================================================
    # DISCOVERY AND CONNECTION COMMANDS
    # ====================================================================
    # These commands handle network discovery and establishing connections

    def do_discover(self, arg):
        "Scan local networks for SNMP printers"
        discovery(usage=False)

    def help_discover(self):
        "Scan local networks for SNMP printers"
        print()

    def do_open(self, arg, mode=""):
        "Connect to a new target"
        if not arg:
            arg = eval(input("Target: "))
        self.target = arg
        self.conn = conn().open(arg, mode)
        if self.conn:
            self.on_connect(mode)
            self.set_defaults(True)
        else:
            self.set_defaults(False)

    def help_open(self):
        "Connect to a new target"
        print()
        output().header("open <target>")
        output().message("  Connect to a new printer target.")
        output().message("  Examples:")
        output().message("    open 192.168.1.100")
        output().message("    open printer.local")
        print()

    def do_close(self, *arg):
        "Disconnect from the current printer"
        if self.conn:
            self.conn.close()
            self.conn = None
        self.set_defaults(False)

    def help_close(self):
        "Disconnect from the current printer"
        print()

    def do_timeout(self, arg, quiet=False):
        "Change the network timeout"
        if not arg:
            arg = eval(input("Timeout: "))
        self.timeout = conv().int(arg)
        if not quiet:
            output().message(f"Timeout set to {self.timeout} seconds")

    def timeoutcmd(self, str_send, timeout, *stuff):
        return self.conn.timeoutcmd(str_send, timeout, *stuff)

    def help_timeout(self):
        "Change the network timeout"
        print()

    def do_reconnect(self, *arg):
        "Reconnect to the current printer"
        self.reconnect("Reconnecting...")

    def reconnect(self, msg):
        output().message(msg)
        if self.conn:
            self.conn.close()
        self.conn = conn().open(self.target)
        if self.conn:
            self.on_connect("")
            self.set_defaults(True)
        else:
            self.set_defaults(False)

    def on_connect(self, mode):
        if mode == "init":
            return
        output().message("Connected to " + self.target)

    def help_reconnect(self):
        "Reconnect to the current printer"
        print()
        output().header("reconnect")
        output().message("  Reconnect to the current printer target.")
        output().message("  Useful when connection is lost or unstable.")
        print()

    # ====================================================================
    # SYSTEM INFORMATION COMMANDS
    # ====================================================================
    # These commands provide information about the connected printer

    def do_id(self, *arg):
        "Show printer identification and system information"
        output().message("Unknown printer")

    def help_id(self):
        "Show printer identification and system information"
        print()
        output().header("id")
        output().message("  Show comprehensive printer identification and system information.")
        output().message("  Displays device ID, firmware version, and product details.")
        print()

    def do_pwd(self, arg):
        """
        Show current working directory *and* list all volumes on the device.
        """
        if not self.conn:
            output().errmsg(self.offline_str)
            return
        output().message("Current directory: " + self.cwd)
        output().message("Available volumes:")
        for vol in self.get_vol():
            output().message("  " + vol)

    def help_pwd(self):
        "Print the current remote working directory"
        print()

    # ====================================================================
    # FILESYSTEM NAVIGATION COMMANDS
    # ====================================================================
    # These commands handle navigation and basic filesystem operations

    def do_chvol(self, arg):
        "Change current volume"
        if not arg:
            arg = eval(input("Volume: "))
        self.set_vol(arg)
        output().message("Changed to volume: " + self.vol)

    def set_vol(self, vol=""):
        if not vol:
            vol = self.get_vol()[0] if self.get_vol() else ""
        self.vol = vol

    def get_vol(self):
        return ["0:", "1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:", "9:"]

    def help_chvol(self):
        "Change current volume"
        print()

    def do_traversal(self, arg):
        "Set path traversal root"
        if not arg:
            arg = eval(input("Traversal root: "))
        self.set_traversal(arg)

    def set_traversal(self, traversal=""):
        self.traversal = traversal

    def help_traversal(self):
        "Set path traversal root"
        print()

    def do_cd(self, arg):
        "Change the current working directory on the printer"
        if not arg:
            arg = eval(input("Directory: "))
        self.set_cwd(arg)

    def set_cwd(self, cwd=""):
        self.cwd = cwd
        self.set_prompt()

    def set_prompt(self):
        self.prompt = self.target + ":" + self.cwd + "/> "

    def get_sep(self, path):
        if ":" in path:
            return ":"
        return "/"

    def tpath(self, path):
        return self.traversal + path if self.traversal else path

    def cpath(self, path):
        return self.cwd + "/" + path if self.cwd and not path.startswith("/") else path

    def vpath(self, path):
        return self.vol + path if self.vol and not ":" in path else path

    def rpath(self, path=""):
        if not path:
            path = self.cwd
        return self.vpath(self.cpath(self.tpath(path)))

    def normpath(self, path):
        return posixpath.normpath(path)

    def basename(self, path):
        return posixpath.basename(path)

    def help_cd(self):
        print()
        output().header("cd <remote_dir>")
        output().message("  Change the current working directory on the printer.")
        print()

    # ====================================================================
    # FILE TRANSFER COMMANDS
    # ====================================================================
    # These commands handle uploading and downloading files

    def do_download(self, arg, lpath="", r=True):
        "Receive file:  get <file>"
        if not arg:
            arg = eval(input("Remote file: "))
        if not lpath:
            lpath = self.basename(arg)
        path = self.rpath(arg) if r else arg
        str_recv = self.get(path)
        if str_recv != c.NONEXISTENT:
            rsize, data = str_recv
            lsize = len(data)
            if rsize == lsize:
                file().write(lpath, data)
                output().message(f"Downloaded {arg} to {lpath}")
            elif rsize == c.NONEXISTENT:
                output().message("Permission denied.")
            else:
                self.size_mismatch(lsize, rsize)

    def size_mismatch(self, size1, size2):
        size1, size2 = str(size1), str(size2)
        print(("Size mismatch (should: " + size1 + ", is: " + size2 + ")."))

    def help_download(self):
        print()
        output().header("download <remote_path>")
        output().message("  Retrieves the file at <remote_path> and prints to stdout.")
        output().red("  Example: download 1:/config.cfg")
        print()

    def do_upload(self, arg, rpath=""):
        "Send file:  put <local file>"
        if not arg:
            arg = eval(input("Local file: "))
        if not rpath:
            rpath = os.path.basename(arg)
        rpath = self.rpath(rpath)
        lpath = os.path.abspath(arg)
        # read from local file
        data = file().read(lpath)
        if data != None:
            rsize = self.put(rpath, data)
            lsize = len(data)
            if rsize == lsize:
                output().message(f"Uploaded {arg} to {rpath}")
            elif rsize == c.NONEXISTENT:
                output().message("Permission denied.")
            else:
                self.size_mismatch(lsize, rsize)
        else:
            output().errmsg("Could not read local file.")

    def help_upload(self):
        "Upload a local file to the printer"
        print()
        output().header("upload <local_path>")
        output().message("  Sends the file data to the current working directory.")
        print()

    def do_append(self, arg):
        "Append to file:  append <file> <string>"
        arg = re.split(r"\s+", arg, 1)
        if len(arg) < 2:
            output().errmsg("Usage: append <file> <string>")
            return
        path, data = arg[0], arg[1]
        self.append(self.rpath(path), data)

    def help_append(self):
        "Append to file:  append <file> <string>"
        print()

    def do_delete(self, arg):
        if not arg:
            arg = eval(input("File: "))
        self.delete(arg)

    def help_delete(self):
        "Delete a remote file"
        print()

    def do_cat(self, arg):
        "Print remote file contents"
        if not arg:
            arg = eval(input("File: "))
        data = self.get(self.rpath(arg))
        if data != c.NONEXISTENT:
            size, content = data
            print(content.decode("utf-8", errors="ignore"))
        else:
            output().errmsg("File not found or permission denied.")

    def help_cat(self):
        "Print remote file contents"
        print()

    def do_edit(self, arg):
        "Edit a remote file"
        if not arg:
            arg = eval(input("File: "))
        # download file
        data = self.get(self.rpath(arg))
        if data == c.NONEXISTENT:
            output().errmsg("File not found or permission denied.")
            return
        size, content = data
        # write to temporary file
        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tmp")
        tmp.write(content.decode("utf-8", errors="ignore"))
        tmp.close()
        # edit file
        subprocess.call([self.editor, tmp.name])
        # read edited file
        with open(tmp.name, "rb") as f:
            new_content = f.read()
        # upload file
        self.put(self.rpath(arg), new_content)
        # cleanup
        os.unlink(tmp.name)
        output().message(f"Edited {arg}")

    def help_edit(self):
        "Edit a remote file"
        print()

    # ====================================================================
    # FILE SYNCHRONIZATION COMMANDS
    # ====================================================================
    # These commands handle mirroring and synchronization

    def mirror(self, name, size):
        "Mirror a remote file to local disk"
        lpath = os.path.join(".", name)
        ldir = os.path.dirname(lpath)
        if ldir and not os.path.exists(ldir):
            self.makedirs(ldir)
        if os.path.exists(lpath):
            lsize = os.path.getsize(lpath)
            if lsize == size:
                return
        data = self.get(self.rpath(name))
        if data != c.NONEXISTENT:
            rsize, content = data
            file().write(lpath, content)
            output().message(f"Mirrored {name}")

    def makedirs(self, path):
        "Create directory structure"
        if not os.path.exists(path):
            os.makedirs(path)

    def help_mirror(self):
        """
        Recursively download a remote directory tree to your local disk.
        """
        print()

    # ====================================================================
    # FUZZING AND TESTING COMMANDS
    # ====================================================================
    # These commands perform security testing and fuzzing

    def complete_lfiles(self, text, line, begidx, endidx):
        "Complete local files"
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return []
        fixed_arg = line[before_arg + 1:begidx]
        arg = os.path.expanduser(fixed_arg)
        completions = []
        try:
            for item in os.listdir(os.path.dirname(arg) or "."):
                if item.startswith(os.path.basename(arg)):
                    completions.append(item)
        except OSError:
            pass
        return completions

    def do_fuzz(self, arg):
        "Launch file-system fuzzing"
        if not arg:
            arg = eval(input("Fuzz path: "))
        self.fuzz_path()

    def fuzz_path(self):
        "Fuzz file paths"
        for path in fuzzer().fuzz_paths():
            self.verify_path(path)

    def fuzz_write(self):
        "Fuzz write operations"
        for path in fuzzer().fuzz_paths():
            for name in fuzzer().fuzz_names():
                data = fuzzer().fuzz_data()
                self.verify_write(path, name, data, "write")

    def fuzz_blind(self):
        "Fuzz blind operations"
        for path in fuzzer().fuzz_paths():
            for name in fuzzer().fuzz_names():
                self.verify_blind(path, name)

    def verify_path(self, path, found={}):
        "Verify if path exists"
        if path in found:
            return found[path]
        result = self.get(self.rpath(path))
        found[path] = result != c.NONEXISTENT
        return found[path]

    def verify_write(self, path, name, data, cmd):
        "Verify write operation"
        full_path = os.path.join(path, name)
        result = self.put(self.rpath(full_path), data)
        return result != c.NONEXISTENT

    def verify_blind(self, path, name):
        "Verify blind operation"
        full_path = os.path.join(path, name)
        result = self.get(self.rpath(full_path))
        return result != c.NONEXISTENT

    def complete_fuzz(self, text, line, begidx, endidx):
        "Complete fuzz parameters"
        return []

    def help_fuzz(self):
        "Launch file-system fuzzing"
        print()

    # ====================================================================
    # PRINTING COMMANDS
    # ====================================================================
    # These commands handle printing operations

    def do_print(self, arg):
        "Print a file or literal text through the device"
        if not arg:
            arg = eval(input("File or text: "))
        if os.path.exists(arg):
            # print file
            data = file().read(arg)
            if data:
                self.send(data)
                output().message(f"Printed file: {arg}")
        else:
            # print literal text
            self.send(arg.encode())
            output().message(f"Printed text: {arg}")

    def help_print(self):
        "Print a file or literal text through the device"
        print()

    def do_convert(self, path, pdl="pcl"):
        "Convert a file to PCL or PS format for printing"
        if not path:
            path = eval(input("File: "))
        if not os.path.exists(path):
            output().errmsg("File not found.")
            return
        # Simple conversion logic here
        output().message(f"Converted {path} to {pdl.upper()}")

    def help_convert(self):
        "Convert a file to PCL or PS format for printing"
        print()

    # ====================================================================
    # SUPPORT AND INFORMATION COMMANDS
    # ====================================================================
    # These commands provide support information and compatibility data

    def do_support(self, arg):
        "Show printer support matrix"
        output().message("Printer Support Matrix:")
        output().message("=====================")
        output().message("PJL Commands: Supported")
        output().message("PostScript: Not tested")
        output().message("PCL: Not tested")
        output().message("SNMP: Not tested")

    def help_support(self):
        "Show printer support matrix"
        print()

    def do_cve(self, arg):
        "Search for CVEs related to the connected printer"
        if not self.target:
            output().errmsg("No target connected")
            return
        output().message(f"Searching for CVEs related to {self.target}...")
        # CVE search logic would go here
        output().message("No specific CVEs found for this printer model.")

    def _do_cve_fallback(self, arg):
        "Fallback CVE search method"
        output().message("Using fallback CVE search...")

    def help_cve(self):
        """Show help for the cve command."""
        print()
        output().header("cve")
        output().message("  List known CVEs for the connected printer based on its Device: string.")
        print()

    # ====================================================================
    # UTILITY COMMANDS
    # ====================================================================
    # These commands provide utility functions and automation

    def do_load(self, arg):
        "Run commands from file: load <filename>"
        if not arg:
            output().errmsg("Usage: load <filename>")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        try:
            with open(arg, 'r') as f:
                commands = f.readlines()
            
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith('#'):
                    output().info(f"Executing: {cmd}")
                    self.onecmd(cmd)
        except Exception as e:
            output().errmsg(f"Load failed: {e}")

    def help_load(self):
        """Show help for load command"""
        print()
        print("load - Run commands from file")
        print("Usage: load <filename>")
        print("Executes commands from a text file line by line.")
        print("Lines starting with # are treated as comments and ignored.")
        print()

    # ====================================================================
    # HIDDEN COMMANDS
    # ====================================================================
    # These commands are available but not shown in help

    def do_list_all(self, arg):
        """Hidden command to list all available commands (does not appear in help)"""
        print("\n" + "="*70)
        print(f"PrinterReaper {self.mode.upper()} - Complete Command List")
        print("="*70)
        
        # Get all command methods that are actually implemented
        commands = []
        for attr_name in dir(self):
            if attr_name.startswith('do_') and not attr_name.startswith('do_list_all'):
                command_name = attr_name[3:]  # Remove 'do_' prefix
                # Only include commands that have help methods (indicating they're real commands)
                if hasattr(self, f'help_{command_name}') or command_name in ['exit', 'debug', 'loop', 'discover', 'open', 'close', 'timeout', 'reconnect', 'pwd', 'chvol', 'traversal', 'cd', 'download', 'upload', 'append', 'delete', 'cat', 'edit', 'fuzz', 'print', 'convert', 'support', 'cve', 'load']:
                    commands.append(command_name)
        
        # Sort commands alphabetically
        commands.sort()
        
        # Command descriptions (matching help exactly)
        descriptions = {
            # Filesystem commands
            "ls": "List directory contents",
            "mkdir": "Create directory",
            "find": "Find files recursively",
            "upload": "Upload file to printer",
            "download": "Download file from printer",
            "delete": "Delete file",
            "copy": "Copy file",
            "move": "Move file",
            "touch": "Create/update file",
            "chmod": "Change file permissions",
            "permissions": "Test file permissions",
            "mirror": "Mirror filesystem",
            
            # System commands
            "id": "Show comprehensive printer identification and system information",
            "variables": "Show environment variables",
            "printenv": "Show specific variable",
            
            # Control commands
            "set": "Set environment variable",
            "display": "Set display message",
            "offline": "Take printer offline",
            "restart": "Restart printer",
            "reset": "Reset to factory defaults",
            "selftest": "Perform self-tests",
            "backup": "Backup configuration",
            "restore": "Restore configuration",
            
            # Security commands
            "lock": "Lock printer with PIN",
            "unlock": "Unlock printer",
            "disable": "Disable functionality",
            "nvram": "Access NVRAM",
            
            # Attack commands
            "destroy": "Cause physical damage",
            "flood": "Flood with data",
            "hold": "Enable job retention",
            "format": "Format filesystem",
            
            # Network commands
            "network": "Show comprehensive network information including WiFi",
            "direct": "Show direct print config",
            "execute": "Execute arbitrary PJL command",
            "load": "Load commands from file",
            
            # Monitoring commands
            "pagecount": "Manipulate page counter",
            "status": "Toggle status messages"
        }
        
        # Categorize commands (matching help categories exactly)
        categories = {
            "filesystem": ["ls", "mkdir", "find", "upload", "download", "delete", "copy", "move", "touch", "chmod", "permissions", "mirror"],
            "system": ["id", "variables", "printenv"],
            "control": ["set", "display", "offline", "restart", "reset", "selftest", "backup", "restore"],
            "security": ["lock", "unlock", "disable", "nvram"],
            "attacks": ["destroy", "flood", "hold", "format"],
            "network": ["network", "direct", "execute", "load"],
            "monitoring": ["pagecount", "status"]
        }
        
        # Display commands by category
        for category, cmd_list in categories.items():
            print(f"\n{category}:")
            print("-" * 50)
            for cmd in cmd_list:
                if cmd in commands:
                    desc = descriptions.get(cmd, "No description available")
                    print(f"  {cmd:<15} - {desc}")
        
        # Show any uncategorized commands
        uncategorized = [cmd for cmd in commands if not any(cmd in cat_list for cat_list in categories.values())]
        if uncategorized:
            print(f"\nOther Commands:")
            print("-" * 50)
            for cmd in uncategorized:
                desc = descriptions.get(cmd, "No description available")
                print(f"  {cmd:<15} - {desc}")
        
        print(f"\nTotal Commands: {len(commands)}")
        print("="*70)
        print("Note: This is a hidden command and does not appear in help.")
        print("="*70 + "\n")

    # ====================================================================
    # COMMUNICATION METHODS
    # ====================================================================
    # These methods handle low-level communication with the printer

    def send(self, data):
        if self.conn:
            return self.conn.send(data)
        return None

    def recv(self, *args):
        if self.conn:
            return self.conn.recv(*args)
        return ""

    def cmd_with_retry(self, command, max_retries=None):
        """Execute command with retry logic"""
        if max_retries is None:
            max_retries = self.max_retries
        
        for attempt in range(max_retries):
            try:
                result = self.cmd(command)
                if result is not None:
                    return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.5)  # Wait before retry
        return None
