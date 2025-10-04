#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fuzzer Module - Path and Data Fuzzing for Printer Security Testing
Provides fuzzing vectors for file system testing, path traversal, and vulnerability discovery
"""

class fuzzer():
    """
    Fuzzer class with static lists and dynamic generators for security testing
    """
    
    # Volume prefixes (printer volumes and drive letters)
    vol = ["", ".", "\\", "/", "file:///", "C:/", "D:/", "E:/", "F:/", "G:/", "H:/", "I:/", "J:/", "K:/", "L:/", "M:/", "N:/", "O:/", "P:/", "Q:/", "R:/", "S:/", "T:/", "U:/", "V:/", "W:/", "X:/", "Y:/", "Z:/", "0:/", "1:/", "2:/", "3:/", "4:/", "5:/", "6:/", "7:/", "8:/", "9:/"]
    
    # Environment variables (Unix-like)
    var = ["~", "$HOME", "$USER", "$PATH", "$PWD", "$TEMP", "$TMP", "$TMPDIR", "$HOME/.config", "$HOME/.local/share"]
    
    # Windows environment variables
    win = ["%WINDIR%", "%SYSTEMROOT%", "%HOMEPATH%", "%PROGRAMFILES%", "%PROGRAMFILES(X86)%", "%APPDATA%", "%LOCALAPPDATA%", "%TEMP%", "%TMP%", "%USERPROFILE%", "%SYSTEMDRIVE%"]
    
    # SMB/UNC paths
    smb = ["\\\\127.0.0.1\\", "\\\\localhost\\", "\\\\smb\\", "\\\\samba\\", "\\\\fileserver\\", "\\\\share\\", "\\\\printer\\", "\\\\printserver\\", "\\\\networkshare\\"]
    
    # Web paths (HTTP)
    web = ["http://127.0.0.1/", "http://localhost/", "http://smb/", "http://samba/", "http://fileserver/", "http://share/", "http://printer/", "http://printserver/", "http://networkshare/"]
    
    # Directory traversal patterns
    dir = ["..", "...", "....", "../..", "../../..", "../../../..", "../../../../..", "../../../../../..", "../../../../../../..", "../../../../../../../.."]
    
    # Path separators
    sep = ["", "\\", "/", "\\\\", "//", "\\/", "/\\"]
    
    # Filesystem hierarchy standard (Unix/Linux)
    fhs = ["/etc", "/bin", "/sbin", "/home", "/proc", "/dev", "/lib",
           "/opt", "/run",  "/sys", "/tmp", "/usr", "/var",  "/mnt", "/srv",
           "/boot", "/root", "/media", "/lib64", "/lib32", "/usr/local",
           "/usr/share", "/usr/lib", "/usr/bin", "/usr/sbin", "/usr/libexec",
           "/usr/include", "/usr/src", "/usr/local/bin", "/usr/local/sbin",
           "/usr/local/lib", "/usr/local/include", "/usr/local/share"]
    
    # Absolute paths to test
    abs = [".profile", ["etc", "passwd"], ["bin", "sh"], ["bin", "ls"],
           "boot.ini", ["windows", "win.ini"], ["windows", "cmd.exe"]]
    
    # Relative Windows paths
    rel = ["%WINDIR%\\win.ini",
           "%WINDIR%\\repair\\sam",
           "%WINDIR%\\repair\\system",
           "%WINDIR%\\system32\\config\\system.sav",
           "%WINDIR%\\System32\\drivers\\etc\\hosts",
           "%SYSTEMDRIVE%\\boot.ini",
           "%USERPROFILE%\\ntuser.dat",
           "%SYSTEMDRIVE%\\pagefile.sys",
           "%SYSTEMROOT%\\repair\\sam",
           "%SYSTEMROOT%\\repair\\system"]

    # Combined prefixes for different fuzzing modes
    path = vol+var+win+smb+web  # path fuzzing
    write = vol+var+win+smb+fhs  # write fuzzing
    blind = vol+var             # blind fuzzing
    
    # ====================================================================
    # DYNAMIC FUZZING METHODS (Added in v2.3.3)
    # ====================================================================
    
    def fuzz_paths(self):
        """
        Generate comprehensive list of fuzzing paths
        Combines volumes, directories, separators for path traversal testing
        """
        paths = []
        
        # Basic paths
        paths.extend(self.path)
        
        # Traversal combinations (vol + traversal + separator)
        for v in self.vol[:10]:  # Focus on common volumes
            for d in self.dir[:5]:  # Common traversal depths
                for s in self.sep[:3]:  # Common separators
                    if v and d:
                        paths.append(v + s + d)
        
        # Common sensitive files with traversal
        sensitive = [
            "../../../etc/passwd",
            "../../etc/shadow",
            "../../../proc/version",
            "../../rw/var/sys/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../boot.ini",
            "0:/../../../etc/passwd",
            "1:/../../etc/shadow",
        ]
        paths.extend(sensitive)
        
        # Filesystem hierarchy
        paths.extend(self.fhs)
        
        return paths
    
    def fuzz_names(self):
        """
        Generate fuzzing filenames for testing
        Returns list of potentially sensitive or dangerous filenames
        """
        names = [
            # Hidden files
            ".htaccess", ".htpasswd", ".profile", ".bashrc", ".ssh",
            
            # Configuration files
            "passwd", "shadow", "config.xml", "config.cfg", "device.cfg",
            "settings.ini", "printer.cfg", "network.xml",
            
            # Traversal attempts
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            
            # Script files
            "test.ps", "test.pcl", "exploit.ps", "backdoor.ps",
            "malicious.pdf", "payload.eps",
            
            # System files
            "boot.ini", "win.ini", "hosts", "resolv.conf",
            
            # Special characters
            "file with spaces.txt",
            "file;with;semicolons.txt",
            "file|with|pipes.txt",
            "file&with&ampersands.txt",
            
            # Long names (overflow testing)
            "A" * 255,
            "B" * 1000,
        ]
        
        return names
    
    def fuzz_data(self, size='small'):
        """
        Generate fuzzing data payloads
        Args:
            size: 'small', 'medium', 'large', or 'huge'
        Returns:
            bytes object with fuzzing payload
        """
        sizes = {
            'small': 1000,
            'medium': 10000,
            'large': 100000,
            'huge': 1000000
        }
        
        length = sizes.get(size, 1000)
        
        payloads = []
        
        # Buffer overflow patterns
        payloads.append(b"A" * length)
        payloads.append(b"B" * length)
        
        # Null bytes
        payloads.append(b"\x00" * (length // 10))
        
        # Format string attacks
        payloads.append(b"%s" * (length // 10))
        payloads.append(b"%x" * (length // 10))
        payloads.append(b"%n" * (length // 10))
        
        # Special characters
        payloads.append(b"<script>alert('XSS')</script>" * (length // 100))
        payloads.append(b"'; DROP TABLE printers; --" * (length // 100))
        
        # Binary patterns
        payloads.append(bytes(range(256)) * (length // 256))
        
        # Return first payload (can be extended to return all)
        return payloads[0]
    
    def fuzz_traversal_vectors(self):
        """
        Generate specific path traversal attack vectors
        Returns list of path traversal attempts
        """
        vectors = []
        
        # Unix/Linux traversal (multiple depths)
        for depth in range(1, 10):
            prefix = "../" * depth
            targets = ["etc/passwd", "etc/shadow", "proc/version", "root/.ssh/id_rsa"]
            for target in targets:
                vectors.append(prefix + target)
        
        # Windows traversal
        for depth in range(1, 10):
            prefix = "..\\" * depth
            targets = ["windows\\system32\\config\\sam", "boot.ini", "windows\\win.ini"]
            for target in targets:
                vectors.append(prefix + target)
        
        # Volume-based traversal (printer-specific)
        for vol in ["0:", "1:", "2:"]:
            for depth in range(1, 6):
                prefix = "/../" * depth
                vectors.append(vol + prefix + "etc/passwd")
                vectors.append(vol + prefix + "rw/var/sys/passwd")
        
        # Embedded systems specific
        vectors.extend([
            "../../rw/var/sys/passwd",
            "../../../mnt/flash/config",
            "../../opt/printer/config.xml",
        ])
        
        return vectors
