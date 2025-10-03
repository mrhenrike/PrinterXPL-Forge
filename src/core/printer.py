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
import tempfile
import subprocess
import traceback
import requests
import time

# local pret classes
from utils.helper import log, output, conv, file, item, conn, const as c
from core.discovery import discovery
from utils.fuzzer import fuzzer
from modules.cve import do_cve, help_cve


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

    # --------------------------------------------------------------------
    def __init__(self, args):
        # init cmd module
        cmd.Cmd.__init__(self)
        self.debug = args.debug  # debug mode
        self.quiet = args.quiet  # quiet mode
        self.mode = args.mode    # command mode

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
        # input loop
        self.cmdloop()

    def set_defaults(self, newtarget):
        self.fuzz = False
        if newtarget:
            self.set_vol()
            self.set_traversal()
            self.error = None
        else:
            self.set_prompt()

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
        if header is not None:
            cmd.Cmd.print_topics(self, header, cmds, cmdlen, maxcol)

    # suppress some chit-chat in quiet mode
    def chitchat(self, *args):
        if not self.quiet:
            output().chitchat(*args)

    # --------------------------------------------------------------------
    # code to be executed before command line is interpreted
    def precmd(self, line):
        # commands that can be run offline
        off_cmd = [
            "#", "?", "help", "exit", "quit", "EOF", "timeout",
            "mode", "load", "loop", "discover", "open", "debug",
        ]
        line = line.strip()
        if line and line.split()[0] not in off_cmd:
            log().comment(self.logfile, line)
            if self.conn is None:
                print(self.offline_str)
                return os.linesep
        return line

    # --------------------------------------------------------------------
    # catch-all wrapper to guarantee continuation on unhandled exceptions
    def onecmd(self, line):
        try:
            return cmd.Cmd.onecmd(self, line)
        except Exception as e:
            traceback.print_exc()
            output().errmsg("Program Error", e)

    # ====================================================================

    # ------------------------[ exit ]------------------------------------
    def do_exit(self, *arg):
        if self.logfile:
            log().close(self.logfile)
        sys.exit()

    do_quit = do_exit
    do_EOF  = do_exit

    def help_exit(self):
        "Exit the shell"
        print()
        output().header("exit")
        output().message("  Exit the interactive shell and close the connection.")
        print()

    # ------------------------[ debug ]-----------------------------------
    def do_debug(self, arg):
        "Enter debug mode. Use 'hex' for hexdump:  debug [hex]"
        self.debug = not self.debug
        if arg == "hex":
            self.debug = "hex"
        if self.conn:
            self.conn.debug = self.debug
        output().message("Debug mode on" if self.debug else "Debug mode off")

    def help_debug(self):
        "Toggle raw traffic debug output"
        print()
        output().header("debug")
        output().message("  Toggle raw traffic debug output on/off.")
        output().message("  When enabled, show full sent/received buffers.")
        print()

    # ====================================================================
    # ------------------------[ loop <cmd> <arg1> <arg2> … ]--------------
    def do_loop(self, arg):
        "Run command for multiple arguments:  loop <cmd> <arg1> <arg2> …"
        args = re.split(r"\s+", arg)
        if len(args) > 1:
            cmd_name = args.pop(0)
            for a in args:
                output().chitchat(f"Executing command: '{cmd_name} {a}'")
                self.onecmd(f"{cmd_name} {a}")
        else:
            self.onecmd("help loop")

    def help_loop(self):
        "Run a command repeatedly over multiple arguments"
        print()
        output().header("loop <cmd> <arg1> <arg2> ...")
        output().message("  Executes <cmd> for each of the listed arguments in turn.")
        print()

    # ====================================================================

    # ------------------------[ discover ]--------------------------------
    def do_discover(self, arg):
        "Discover local printer devices via SNMP."
        discovery()

    def help_discover(self):
        "Scan local networks for SNMP printers"
        print()
        output().header("discover")
        output().message("  Scan local networks for SNMP printers and print their info.")
        output().message("  Probe each /24 on your host for SNMP printers (snmpget required).")
        print()

    # ------------------------[ open <target> ]---------------------------
    def do_open(self, arg, mode=""):
        "Connect to remote device:  open <target>"
        if not arg:
            arg = eval(input("Target: "))
        try:
            newtarget = arg != self.target
            self.target = arg
            self.conn = conn(self.mode, self.debug, self.quiet)
            self.conn.timeout(self.timeout)
            self.conn.open(arg)
            print(f"Connection to {arg} established")
            self.on_connect(mode)
            if not self.quiet and mode != "reconnect":
                sys.stdout.write("Device:   ")
                self.do_id()
            output().message("")
            self.set_defaults(newtarget)
        except Exception as e:
            output().errmsg(f"Connection to {arg} failed", e)
            self.do_close()
            if mode == "init":
                self.do_exit()

    # wrapper to send data
    def send(self, data):
        if self.conn:
            self.conn.send(data)

    # wrapper to recv data
    def recv(self, *args):
        return self.conn.recv_until(*args) if self.conn else ""
    
    def cmd_with_retry(self, command, max_retries=None):
        """Execute command with retry logic"""
        if max_retries is None:
            max_retries = self.max_retries
            
        for attempt in range(max_retries):
            try:
                if hasattr(self, 'cmd'):
                    return self.cmd(command)
                else:
                    return self.send(command)
            except Exception as e:
                if attempt < max_retries - 1:
                    output().yellow(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)  # Wait before retry
                else:
                    output().red(f"Command failed after {max_retries} attempts: {e}")
                    raise

    def help_open(self):
        "Connect to a new target"
        print()
        output().header("open <host[:port]>")
        output().message("  Disconnects current session and opens to the new target.")
        output().message("  Example: open 192.168.1.10:9100")
        print()

    # ------------------------[ close ]-----------------------------------
    def do_close(self, *arg):
        "Disconnect from device."
        if self.conn:
            self.conn.close()
            self.conn = None
        output().message("Connection closed.")
        self.set_prompt()

    def help_close(self):
        "Disconnect from the current printer"
        print()
        output().header("close")
        output().message("  Close the connection but stay in the shell.")
        print()

    # ------------------------[ timeout <seconds> ]-----------------------
    def do_timeout(self, arg, quiet=False):
        "Set connection timeout:  timeout <seconds>"
        try:
            if arg:
                t = float(arg)
                if self.conn:
                    self.conn.timeout(t)
                self.timeout = t
            if not quiet:
                print(f"Device or socket timeout: {self.timeout}")
        except Exception as e:
            output().errmsg("Cannot set timeout", e)

    # send mode-specific command with modified timeout
    def timeoutcmd(self, str_send, timeout, *stuff):
        old = self.timeout
        self.do_timeout(str(timeout), True)
        recv = self.cmd(str_send, *stuff)
        self.do_timeout(str(old), True)
        return recv

    def help_timeout(self):
        "Change the network timeout"
        print()
        output().header("timeout <seconds>")
        output().message("  Set the socket timeout for subsequent commands.")
        print()

    # ------------------------[ reconnect ]-------------------------------
    def do_reconnect(self, *arg):
        self.do_close()
        self.do_open(self.target, "reconnect")

    # re-open connection on error
    def reconnect(self, msg):
        if msg:
            output().errmsg("Command execution failed", msg)
        sys.stdout.write(os.linesep + "Forcing reconnect. ")
        self.do_close()
        self.do_open(self.target, "reconnect")
        if not msg:
            self.cmdloop(intro="")

    # --------------------------------------------------------------------
    # dummy functions to overwrite
    def on_connect(self, mode):
        # disable unsolicited status
        if mode == "init":
            self.cmd("@PJL USTATUSOFF", False)

            # fetch and store Device string
            resp = self.cmd("@PJL INFO ID")
            lines = [ line.strip('"') for line in resp.splitlines() if line.strip() ]
            self.device_info = lines[0] if lines else None


    def do_id(self, *arg):
        output().message("Unknown printer")

    # ====================================================================

    # ------------------------[ pwd ]-------------------------------------
    def do_pwd(self, arg):
        """
        Show current working directory *and* list all volumes on the device.
        """
        # current remote CWD is something like "0:/path/to/dir"
        cwd = self.cwd.lstrip(c.SEP) or ""
        vol = self.vol or ""
        # Print the cwd
        print(f"{vol}:{c.SEP}{cwd or ''}")

        # Now enumerate volumes
        vols = self.vol_exists()  # returns e.g. ['0:/', '1:/', ...]
        if vols:
            output().message("\nAvailable volumes/storage:")
            for v in vols:
                # query each one to see if it actually exists
                exists = self.vol_exists(v)
                status = "OK" if v[0] == exists else "?" 
                print(f"  {v}  [{status}]")
        else:
            output().message("(no others volumes found)")

    def help_pwd(self):
        "Print the current remote working directory"
        print()
        output().header("pwd")
        output().message("  Show current working directory on the printer.")
        output().message("  Display CWD like '0:/' or '1:/subdir/'")
        print()

    # ------------------------[ chvol <volume> ]-------------------------
    def do_chvol(self, arg):
        "Change remote volume: chvol <volume>"
        if not arg:
            output().message("Usage: chvol <volume> (e.g. chvol 1)")
            return
        # allow either "1" or "1:" or "1:/"
        vol = str(arg).rstrip(c.SEP).rstrip(":") + ":/"
        available = self.vol_exists()
        if vol in available:
            self.vol = vol
            print(f"Volume changed to {vol}")
        else:
            print(f"Volume not available: {vol}")

    def set_vol(self, vol=""):
        if not vol:
            if self.mode == "ps":
                vol = c.PS_VOL
            if self.mode == "pjl":
                vol = c.PJL_VOL
        if self.vol != vol:
            self.set_traversal()
            self.vol = vol

    def get_vol(self):
        v = self.vol
        if v and self.mode == "ps":
            v = v.strip("%")
        if v and self.mode == "pjl":
            v = v[0]
        return v

    def help_chvol(self):
        "Change current volume"
        print()
        output().header("chvol <volume_letter>")
        output().message("  Change current volume")
        output().message("  Switch active filesystem volume (e.g. 0, 1, etc.)")
        output().red("  Example: chvol 1")
        print()

    # ------------------------[ traversal <path> ]------------------------
    def do_traversal(self, arg):
        "Set path traversal:  traversal <path>"
        if not arg or self.dir_exists(self.tpath(arg)):
            self.set_traversal(arg)
            output().message("Path traversal " + ("" if arg else "un") + "set.")
        else:
            output().message("Cannot use this path traversal.")

    def set_traversal(self, traversal=""):
        self.traversal = traversal
        if not traversal:
            self.set_cwd()

    def help_traversal(self):
        "Set path traversal root"
        print()
        output().header("traversal <path>")
        output().message("  Set the path traversal root for subsequent commands.")
        output().message("  Change how relative paths are expanded for find/mirror.")
        print()
        output().red("  Example: traversal 1:/jobs/")
        output().message("  Note: This command is useful for setting a base path.")
        output().message("  If no path is given, it will reset to the default traversal.")
        print()

    # ------------------------[ cd <path> ]-------------------------------
    def do_cd(self, arg):
        "Change remote working directory:  cd <path>"
        if not self.cpath(arg) or self.dir_exists(self.rpath(arg)):
            if re.match(r"^[\." + re.escape(c.SEP) + "]+$", self.cpath(arg)):
                output().raw("*** Congratulations, path traversal found ***")
                output().chitchat("Consider setting 'traversal' instead of 'cd'.")
            self.set_cwd(arg)
        else:
            output().message("Failed to change directory.")

    def set_cwd(self, cwd=""):
        self.cwd = self.cpath(cwd) if cwd else ""
        self.set_prompt()

    def set_prompt(self):
        prefix = self.target + ":" if self.conn else ""
        cwd = self.cwd if self.conn else ""
        self.prompt = prefix + c.SEP + cwd + "> "

    def get_sep(self, path):
        if self.mode == "ps" and re.search(r"^%.*%$", path):
            return ""
        return c.SEP if (path or self.cwd or self.traversal) else ""

    # get path without traversal and cwd
    def tpath(self, path):
        return self.vol + self.normpath(path.lstrip(c.SEP))

    # get path without volume and traversal
    def cpath(self, path):
        p = c.SEP.join((self.cwd, path)).lstrip(c.SEP)
        return self.normpath(p)

    # get path without volume
    def vpath(self, path):
        p = c.SEP.join((self.traversal, self.cwd, path)).lstrip(c.SEP)
        return self.normpath(p)

    # get path with volume
    def rpath(self, path=""):
        if (path.startswith("%") or path.startswith("0:")) and not self.fuzz:
            output().warning("Do not refer to disks directly, use chvol.")
        if self.fuzz:
            return path
        return self.vol + self.vpath(path)

    # normalize posix path, mapping "." => ""
    def normpath(self, path):
        p = posixpath.normpath(path)
        return p if p != "." else ""

    def basename(self, path):
        return os.path.basename(posixpath.basename(ntpath.basename(path)))

    def help_cd(self):
        print()
        "Change the current working directory on the printer"
        print()
        output().header("cd <remote_dir>")
        output().message("  Change the current working directory on the printer.")
        print()

    # ------------------------[ get <file> ]------------------------------
    def do_get(self, arg, lpath="", r=True):
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
            # fix carriage return chars added by some devices
            if lsize != rsize and len(conv().nstrip(data)) == rsize:
                lsize, data = rsize, conv().nstrip(data)
            # write to local file
            file().write(lpath, data.encode())
            if lsize == rsize:
                print((str(lsize) + " bytes received."))
            else:
                self.size_mismatch(rsize, lsize)

    def size_mismatch(self, size1, size2):
        size1, size2 = str(size1), str(size2)
        print(("Size mismatch (should: " + size1 + ", is: " + size2 + ")."))

    def help_get(self):
        print()
        output().header("get <remote_path>")
        output().message("  Retrieves the file at <remote_path> and prints to stdout.")
        output().red("  Example: get 1:/config.cfg")
        print()

    # ------------------------[ put <local file> ]------------------------
    def do_put(self, arg, rpath=""):
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
            self.put(rpath, data)
            lsize = len(data)
            rsize = self.file_exists(rpath)
            if rsize == lsize:
                print((str(rsize) + " bytes transferred."))
            elif rsize == c.NONEXISTENT:
                output().message("Permission denied.")
            else:
                self.size_mismatch(lsize, rsize)

    def help_put(self):
        "Upload a local file to the printer"
        print()
        output().header("put <local_path>")
        output().message("  Sends the file data to the current working directory.")
        print()

    # ------------------------[ append <file> <string> ]------------------
    def do_append(self, arg):
        "Append to file:  append <file> <string>"
        arg = re.split(r"\s+", arg, 1)
        if len(arg) > 1:
            path, data = arg
            rpath = self.rpath(path)
            data = data + os.linesep
            self.append(rpath, data)
        else:
            self.onecmd("help append")

    def help_append(self):
        "Append a literal string to a remote file"
        print()
        output().header("append <remote_path> <string>")
        output().message("  Append the given string to the end of <remote_path>.")
        output().message('  Example: append "/logs/today.txt" "New log entry"')
        print()

    # ------------------------[ delete <file> ]---------------------------
    def do_delete(self, arg):
        if not arg:
            arg = eval(input("File: "))
        self.delete(arg)

    # define alias but do not show alias in help
    do_rm = do_delete
    do_rmdir = do_delete

    def help_delete(self):
        "Delete a remote file"
        print()
        output().header("delete <remote_path>")
        output().message("  Remove the specified file from the printer filesystem.")
        output().red("  Example: delete 0:/jobs/printjob.pjl")
        print()

    # ------------------------[ cat <file> ]------------------------------
    def do_cat(self, arg):
        "Output remote file to stdout:  cat <file>"
        if not arg:
            arg = eval(input("Remote file: "))
        path = self.rpath(arg)
        str_recv = self.get(path)
        if str_recv != c.NONEXISTENT:
            rsize, data = str_recv
            output().raw(data.strip())

    def help_cat(self):
        "Print remote file contents"
        print()
        output().header("cat <remote_path>")
        output().message("  Dumps the contents of the remote file to your console.")
        print()
        output().red("  Example: cat 0:/logs/today.txt")
        output().message("  Note: this may not work on all devices.")
        output().message("  If the file is binary, it may contain control characters.")
        output().message("  Use 'get' to download the file instead.")
        print()

    # ------------------------[ edit <file> ]-----------------------------
    def do_edit(self, arg):
        # get name of temporary file
        t = tempfile.NamedTemporaryFile(delete=False)
        lpath = t.name
        t.close
        # download to temporary file
        self.do_get(arg, lpath)
        # get md5sum for original file
        chksum1 = hashlib.md5(open(lpath, "rb").read()).hexdigest()
        try:
            subprocess.call([self.editor, lpath])
            # get md5sum for edited file
            chksum2 = hashlib.md5(open(lpath, "rb").read()).hexdigest()
            # upload file, if changed
            if chksum1 == chksum2:
                output().message("File not changed.")
            else:
                self.do_put(lpath, arg)
        except Exception as e:
            output().errmsg("Cannot edit file - Set self.editor", e)
        # delete temporary file
        os.remove(lpath)

    # define alias but do not show alias in help
    do_vim = do_edit

    def help_edit(self):
        "Edit a remote file"
        print()
        output().header("edit <remote_path>")
        output().message("  Open the file in your $EDITOR, upload on save.")
        print()
        output().red("  Example: edit 0:/config.cfg")
        output().message("  Note: Set self.editor to your preferred editor (e.g. vim, nano).")
        output().message("  If the file is large, it may take a while to download/upload.")
        output().message("  If the file is binary, it may contain control characters.")
        output().message("  Use 'get' to download the file instead.")
        print()

    # ------------------------[ mirror <path> ]---------------------------
    def mirror(self, name, size):
        target, vol = self.basename(self.target), self.get_vol()
        root = os.path.abspath(os.path.join("mirror", target, vol))
        lpath = os.path.join(root, name)
        """
    ┌───────────────────────────────────────────────────────────┐
    │                 mitigating path traversal                 │
    ├───────────────────────────────────────────────────────────┤
    │ creating a mirror can be a potential security risk if the │
    │ path contains traversal characters, environment variables │
    │ or other things we have not thought about; while the user │
    │ is in total control of the path (via 'cd' and 'traversal' │
    │ commands), she might accidentally overwrite her files...  │
    │                                                           │
    │ our strategy is to first replace trivial path traversal   │
    │ strings (while still being able to download the files)    │
    │ and simply give up on more sophisticated ones for now.    │
    └───────────────────────────────────────────────────────────┘
    """
        # replace path traversal (poor man's version)
        lpath = re.sub(r"(\.)+" + c.SEP, "", lpath)
        # abort if we are still out of the mirror root
        if not os.path.realpath(lpath).startswith(root):
            output().errmsg(
                "Not saving data out of allowed path",
                "I'm sorry Dave, I'm afraid I can't do that.",
            )
        elif size:  # download current file
            output().raw(self.vol + name + " -> " + lpath)
            self.makedirs(os.path.dirname(lpath))
            self.do_get(self.vol + name, lpath, False)
        else:  # create current directory
            self.chitchat("Traversing " + name)
            self.makedirs(lpath)

    # recursive directory creation
    def makedirs(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def help_mirror(self):
        """
        Recursively download a remote directory tree to your local disk.

        Usage:
        mirror <remote_dir>

        Description:
        - Walks the PJL filesystem under <remote_dir>, downloading each file and
            reproducing the directory hierarchy under ./mirror/<target>/<volume>/.
        - If an entry is a directory, it creates the corresponding local folder.
        - Simple path‐traversal mitigation strips leading “../” sequences—but be
            cautious: deeply nested or malicious paths may still pose a risk.

        Input:
        mirror 0:/jobs/

        Local output:
        mirror/<printer-ip-or-hostname>/0/jobs/report1.txt
        mirror/<printer-ip-or-hostname>/0/jobs/archive/log.txt
        ...

        Examples:
        # Mirror all stored jobs on volume 0:
        mirror 0:/jobs/
        # Mirror root of volume 1:
        mirror 1:/

        Risks:
        - If the remote <remote_dir> contains unexpected traversal patterns,
            local files **outside** the intended mirror directory may be at risk.
        - Always run in a dedicated working directory to avoid accidental
            overwrites of your own files.
        - Large directories may consume significant disk space and time.
        """
        print()
        output().header("mirror <remote_dir>")
        output().message("  Recursively download every file and folder under <remote_dir>")
        output().message("  into ./mirror/<target>/<volume>/, preserving the directory tree.")
        print()
        output().red("Examples:")
        output().red("  mirror 0:/jobs/")
        output().red("    # Downloads all files under 0:/jobs/ to")
        output().red("    #   mirror/<printer_ip>/0/jobs/... on your local disk")
        print()
        output().message("  mirror 1:/")
        output().message("    # Mirrors the entire volume 1 filesystem")
        print()
        output().red("Warnings:")
        output().red("  • Simple path‐traversal mitigation strips '../', but may not cover")
        output().red("    all edge cases—avoid running in sensitive directories.")
        output().red("  • Large file trees can use lots of disk space/time.")
        output().red("  • If you interrupt midway, partial directories may remain.")
        print()

    # --------------------------------------------------------------------
    # auto-complete dirlist for local fs
    def complete_lfiles(self, text, line, begidx, endidx):
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return  # arg not found

        fixed = line[before_arg + 1: begidx]  # fixed portion of the arg
        arg = line[before_arg + 1: endidx]
        pattern = arg + "*"

        completions = []
        for path in glob.glob(pattern):
            if path and os.path.isdir(path) and path[-1] != os.sep:
                path = path + os.sep
            completions.append(path.replace(fixed, "", 1))
        return completions

    # define alias
    complete_load = complete_lfiles  # files or directories
    complete_put = complete_lfiles  # files or directories
    complete_print = complete_lfiles  # files or directories

    # ====================================================================

    # ------------------------[ fuzz <category> ]-------------------------
    def do_fuzz(self, arg):
        if arg in self.options_fuzz:
            # enable global fuzzing
            self.fuzz = True
            if arg == "path":
                self.fuzz_path()
            if arg == "write":
                self.fuzz_write()
            if arg == "blind":
                self.fuzz_blind()
            self.chitchat("Fuzzing finished.")
            # disable global fuzzing
            self.fuzz = False
        else:
            self.help_fuzz()

    def fuzz_path(self):
        output().raw("Checking base paths first.")
        # get a cup of coffee, fuzzing will take some time
        output().fuzzed("PATH", "", ("", "EXISTS", "DIRLIST"))
        output().hline()
        found = {}  # paths found
        # try base paths first
        for path in self.vol_exists() + fuzzer().path:
            self.verify_path(path, found)
        output().raw("Checking filesystem hierarchy standard.")
        # try direct access to fhs dirs
        for path in fuzzer().fhs:
            self.verify_path(path)
        # try path traversal strategies
        if found:
            output().raw("Now checking traversal strategies.")
            output().fuzzed("PATH", "", ("", "EXISTS", "DIRLIST"))
            output().hline()
            # only check found volumes
            for vol in found:
                sep = "" if vol[-1:] in ["", "/", "\\"] else "/"
                sep2 = vol[-1:] if vol[-1:] in ["/", "\\"] else "/"
                # 1st level traversal
                for dir in fuzzer().dir:
                    path = vol + sep + dir + sep2
                    self.verify_path(path)
                    # 2nd level traversal
                    for dir2 in fuzzer().dir:
                        path = vol + sep + dir + sep2 + dir2 + sep2
                        self.verify_path(path)

    def fuzz_write(self):
        output().raw("Writing temporary files.")
        # get a cup of tea, fuzzing will take some time
        output().fuzzed("PATH", "COMMAND", ("GET", "EXISTS", "DIRLIST"))
        output().hline()
        # test data to put/append
        data = "test"
        data2 = "test2"
        # try write to disk strategies
        for vol in self.vol_exists() + fuzzer().write:
            sep = "" if vol[-1:] in ["", "/", "\\"] else "/"
            name = "dat" + str(random.randrange(10000))
            # FSDOWNLOAD
            self.put(vol + sep + name, data)
            fsd_worked = self.verify_write(vol + sep, name, data, "PUT")
            # FSAPPEND
            self.append(vol + sep + name, data2)
            data = (data + data2) if fsd_worked else data2
            self.verify_write(vol + sep, name, data, "APPEND")
            # FSDELETE
            self.do_delete(vol + sep + name)
            output().hline()

    def fuzz_blind(self):
        output().raw("Blindly trying to read files.")
        # get a bottle of beer, fuzzing will take some time
        output().fuzzed("PATH", "", ("", "GET", "EXISTS"))
        output().hline()
        # try blind file access strategies (relative path)
        for path in fuzzer().rel:
            self.verify_blind(path, "")
        output().hline()
        # try blind file access strategies (absolute path)
        for vol in self.vol_exists() + fuzzer().blind:
            sep = "" if vol[-1:] in ["", "/", "\\"] else "/"
            sep2 = vol[-1:] if vol[-1:] in ["/", "\\"] else "/"
            # filenames to look for
            for file in fuzzer().abs:
                # set current delimiter
                if isinstance(file, list):
                    file = sep2.join(file)
                path = vol + sep
                self.verify_blind(path, file)
                # vol name out of range error
                if self.error == "30054":
                    output().raw("Volume nonexistent, skipping.")
                    break
                # no directory traversal
                for dir in fuzzer().dir:
                    # n'th level traversal
                    for n in range(1, 3):
                        path = vol + sep + n * (dir + sep2)
                        self.verify_blind(path, file)

    # check for path traversal
    def verify_path(self, path, found={}):
        # 1st method: EXISTS
        opt1 = self.dir_exists(path) or False
        # 2nd method: DIRLIST
        dir2 = self.dirlist(path, False)
        opt2 = True if dir2 else False
        # show fuzzing results
        output().fuzzed(path, "", ("", opt1, opt2))
        if opt2:  # DIRLIST successful
            # add path if not already listed
            if dir2 not in list(found.values()):
                found[path] = dir2
                output().raw("Listing directory.")
                self.do_ls(path)
        elif opt1:  # only EXISTS successful
            found[path] = None

    # check for remote files (write)
    def verify_write(self, path, name, data, cmd):
        # 1st method: GET
        opt1 = data in self.get(path + name, len(data))[1]
        # 2nd method: EXISTS
        opt2 = self.file_exists(path + name) != c.NONEXISTENT
        # 3rd method: DIRLIST
        opt3 = name in self.dirlist(path, False)
        # show fuzzing results
        output().fuzzed(path + name, cmd, (opt1, opt2, opt3))
        return opt1

    # check for remote files (blind)
    def verify_blind(self, path, name):
        # 1st method: GET
        opt1 = self.get(path + name, 10)[1]  # file size is unknown :/
        opt1 = True if opt1 and not "FILEERROR" in opt1 else False
        # 2nd method: EXISTS
        opt2 = self.file_exists(path + name) != c.NONEXISTENT
        # show fuzzing results
        output().fuzzed(path + name, "", ("", opt1, opt2))

    options_fuzz = ("path", "write", "blind")

    def complete_fuzz(self, text, line, begidx, endidx):
        return [cat for cat in self.options_fuzz if cat.startswith(text)]
    
    def help_fuzz(self):
        "Launch file-system fuzzing"
        print()
        output().header("fuzz <path|write|blind>")
        output().message("  Perform various file-system traversal and append tests.")
        output().message("  This is an experimental feature, use with caution.")
        print()
        output().message("  Available categories:")
        output().message("    path - test for path traversal and directory listing")
        output().message("    write - test for file creation, appending and deletion")
        output().message("    blind - test for blind file access (read)")
        print()
        output().red("  Example: fuzz path")
        output().red("  Note: This may take a long time and produce many results.")
        print()
    # ====================================================================

    # ------------------------[ print <file>|"text" ]----------------------------
    def do_print(self, arg):
        'Print image file or raw text:  print <file>|"text"'
        """
┌──────────────────────────────────────────────────────────┐
│ Poor man's driverless printing (PCL based, experimental) │
└──────────────────────────────────────────────────────────┘
        """
        if not arg:
            arg = eval(input('File or "text": '))
        # raw text
        if arg.startswith('"') and arg.endswith('"'):
            data = arg.strip('"').encode()
        else:
            # either PS file or convert anything else to PCL
            if arg.lower().endswith(".ps"):
                data = file().read(arg) or b""
            else:
                # convert returns bytes or None on failure
                self.chitchat(f"Converting '{arg}' to {self.mode} format")
                data = self.convert(arg, self.mode)
            # wrap in PJL/UEL for PCL
            if data is not None and self.mode == "pcl":
                data = c.UEL.encode() + data + c.UEL.encode()

        if not data:
            output().errmsg("Print failed", "No data to send (conversion error or empty file)")
            return

        # send to printer
        try:
            self.send(data)
            output().message("H")
        except Exception as e:
            output().errmsg("Send failed", e)

    def help_print(self):
        "Print a file or literal text through the device"
        print()
        output().header("print <file>|\"text\"")
        output().message("  Send a local file or literal text to the printer.")
        output().message("  If the file is not in PCL format, it will be converted to PCL using ImageMagick or Ghostscript.")
        output().message("  If the file is a PostScript file, it will be sent as is.")
        output().message("  If the file is a text file, it will be sent as raw text.")
        print()
        output().red("Examples:")
        output().red('print "Hello, world!"  Send literal text to the printer')
        output().red('print myfile.ps      Send a PostScript file')
        output().red('print myfile.txt     Send a text file')
        output().red('print myfile.png     Convert and send an image file')
        output().red('print myfile.pdf     Convert and send a PDF file')
        print()

    # convert image to page description language
    def do_convert(self, path, pdl="pcl"):
        try:
            self.chitchat(f"Converting '{path}' to {pdl} format")
            pdf_opts = ["-density", "300"] if path.lower().endswith(".pdf") else []
            cmd = ["convert"] + pdf_opts + [path, "-quality", "100", f"{pdl}:-"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if err:
                output().errmsg("Cannot convert", err.decode(errors="ignore"))
                return None
            return out
        except FileNotFoundError as e:
            output().errmsg("Cannot convert", "ImageMagick or Ghostscript missing")
            return None
        except Exception as e:
            output().errmsg("Cannot convert", e)
            return None

    def help_convert(self):
        "Convert a file to PCL or PS format for printing"
        print()
        output().header("convert <file> [pcl|ps]")
        output().message("  Convert a file to PCL or PS format for printing.")
        output().message("  If no format is specified, defaults to PCL.")
        output().message("  Uses ImageMagick or Ghostscript for conversion.")
        print()
        output().red("Examples:")
        output().red("  convert myfile.png pcl  Convert an image to PCL format")
        output().red("  convert myfile.pdf ps   Convert a PDF to PostScript format")
        output().red("""
┌──────────────────────────────────────────────────────────┐
│ Warning: ImageMagick and Ghostscript are used to convert │
│ the document to be printed into a language understood be │
│ the printer. Don't print anything from untrusted sources │
│ as it may be a security risk (CVE-2016–3714, 2016-7976). │
└──────────────────────────────────────────────────────────┘""")
        print()

    # ------------------------[ support ]----------------------------
    def do_support(self, arg):
        """
        List printer support matrix from src/utils/printers_list.csv
        Usage: support
        """
        # locate the CSV
        csv_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         '..', 'utils', 'printers_list.csv')
        )
        try:
            with open(csv_path, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                rows = [r for r in reader if r]  # skip empty lines
        except Exception as e:
            output().errmsg("Cannot load support list", e)
            return

        if not rows:
            output().message("No data in support list.")
            return

        header = rows[0]
        num_cols = len(header)

        # pad all rows to the same length
        normalized = []
        for r in rows:
            if len(r) < num_cols:
                r = r + [''] * (num_cols - len(r))
            normalized.append(r[:num_cols])

        # compute column widths
        cols = list(itertools.zip_longest(*normalized, fillvalue=''))
        widths = [max(len(cell) for cell in col) for col in cols]

        # print header
        output().message("  ".join(header[i].ljust(widths[i]) for i in range(num_cols)))
        output().message("  ".join('-' * widths[i] for i in range(num_cols)))

        # print rows
        for row in normalized[1:]:
            output().message("  ".join(row[i].ljust(widths[i]) for i in range(num_cols)))
        output().message("")

    def help_support(self):
        "Show printer support matrix"
        print()
        output().header("support")
        output().message("  List printer support matrix from src/utils/printers_list.csv")
        output().message("  Displays the printer model, PCL version, PS support, and other flags.")
        print()
        output().red("  Note: This file is maintained in the src/utils directory.")
        output().red("      It is used to determine printer capabilities and compatibility.")
        output().red("      The output includes columns for model, PCL version, PS support, and other flags.")
        output().red("      The CSV file is structured with semicolon (;) as the delimiter.")
        output().red("      The first row contains headers, and subsequent rows contain printer data.")
        print()

    # --------------------------------------------------------------------
    def do_cve(self, arg):
        """List known CVEs for the connected printer based on its Device: string."""
        device = getattr(self, "device_info", None)
        device = "HP LaserJet MFP M139w"
        if not device:
            output().errmsg("CVE", "No device information available.")
            return

        # 1) print the product line
        output().message(f"Searching CVEs for: {device}")

        # 2) URL‐encode: replace spaces with '+'
        keyword = device.replace(" ", "+")

        # 3) CIRCL public API
        url = f"https://cve.circl.lu/api/search/{keyword}"

        # 4) fetch & handle 404 as “no results”
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 404:
                items = []
            else:
                resp.raise_for_status()
                items = resp.json() or []
        except HTTPError as e:
            output().errmsg("CVE", f"Failed to fetch CVEs: {e}")
            return
        except Exception as e:
            output().errmsg("CVE", f"Failed to fetch CVEs: {e}")
            return

        if not items:
            output().info(f"No CVEs found for {device}")
            return

        # 5) build table rows
        rows = []
        for idx, it in enumerate(items, start=1):
            cve_id = it.get("id", "UNKNOWN")
            link   = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            rows.append((str(idx), device, cve_id, link))

        headers = ("ORD", "Product", "CVE-ID", "Link")
        # compute column widths
        col_widths = [
            max(len(headers[i]), *(len(r[i]) for r in rows))
            for i in range(len(headers))
        ]

        # 6) print table
        print()
        print("  ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
        print("  ".join("-" * col_widths[i]        for i in range(len(headers))))
        for r in rows:
            print("  ".join(r[i].ljust(col_widths[i]) for i in range(len(headers))))
        print()
    def help_cve(self):
        """Show help for the cve command."""
        print()
        output().header("cve")
        output().message("  List known CVEs for the connected printer based on its Device: string.")
        print()