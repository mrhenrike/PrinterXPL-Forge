def get_os():
    """
    Return one of: 'linux', 'wsl', 'windows', or any other string for unsupported.
    """
    import platform, os
    sysname = platform.system().lower()
    if "linux" in sysname:
        # detect WSL
        if os.path.exists('/proc/sys/kernel/osrelease') and 'microsoft' in open('/proc/sys/kernel/osrelease').read().lower():
            return "wsl"
        return "linux"
    if "windows" in sysname:
        return "windows"
    return sysname  # e.g. 'darwin', etc.
