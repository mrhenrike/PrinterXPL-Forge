#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class fuzzer():
    vol = ["", ".", "\\", "/", "file:///", "C:/", "D:/", "E:/", "F:/", "G:/", "H:/", "I:/", "J:/", "K:/", "L:/", "M:/", "N:/", "O:/", "P:/", "Q:/", "R:/", "S:/", "T:/", "U:/", "V:/", "W:/", "X:/", "Y:/", "Z:/", "0:/", "1:/", "2:/", "3:/", "4:/", "5:/", "6:/", "7:/", "8:/", "9:/"]
    var = ["~", "$HOME", "$USER", "$PATH", "$PWD", "$TEMP", "$TMP", "$TMPDIR", "$HOME/.config", "$HOME/.local/share"]
    win = ["%WINDIR%", "%SYSTEMROOT%", "%HOMEPATH%", "%PROGRAMFILES%", "%PROGRAMFILES(X86)%", "%APPDATA%", "%LOCALAPPDATA%", "%TEMP%", "%TMP%", "%USERPROFILE%", "%SYSTEMDRIVE%"]
    smb = ["\\\\127.0.0.1\\", "\\\\localhost\\", "\\\\smb\\", "\\\\samba\\", "\\\\fileserver\\", "\\\\share\\", "\\\\printer\\", "\\\\printserver\\", "\\\\networkshare\\"]
    web = ["http://127.0.0.1/", "http://localhost/", "http://smb/", "http://samba/", "http://fileserver/", "http://share/", "http://printer/", "http://printserver/", "http://networkshare/"] # web fuzzing
    dir = ["..", "...", "...."]  # also combinations like "./.."
    sep = ["", "\\", "/", "\\\\", "//", "\\/"]
    fhs = ["/etc", "/bin", "/sbin", "/home", "/proc", "/dev", "/lib",
           "/opt", "/run",  "/sys", "/tmp", "/usr", "/var",  "/mnt", "/srv",
           "/boot", "/root", "/media", "/lib64", "/lib32", "/usr/local",
           "/usr/share", "/usr/lib", "/usr/bin", "/usr/sbin", "/usr/libexec",
           "/usr/include", "/usr/src", "/usr/local/bin", "/usr/local/sbin",
           "/usr/local/lib", "/usr/local/include", "/usr/local/share"]
    abs = [".profile", ["etc", "passwd"], ["bin", "sh"], ["bin", "ls"],
           "boot.ini", ["windows", "win.ini"], ["windows", "cmd.exe"]]
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

    # define prefixes to use in fuzzing modes
    path = vol+var+win+smb+web  # path fuzzing
    write = vol+var+win+smb+fhs  # write fuzzing
    blind = vol+var             # blind fuzzing
