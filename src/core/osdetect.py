_cached_os = None

def get_os():
    """
    Return one of: 'linux', 'wsl', 'windows', 'darwin' (macOS), 'bsd', or 'unsupported'.
    Result is cached after first call for performance.
    """
    global _cached_os
    if _cached_os:
        return _cached_os
    
    import platform, os
    sysname = platform.system().lower()
    
    if "linux" in sysname:
        # detect WSL (Windows Subsystem for Linux)
        if os.path.exists('/proc/sys/kernel/osrelease'):
            try:
                with open('/proc/sys/kernel/osrelease') as f:
                    if 'microsoft' in f.read().lower():
                        _cached_os = "wsl"
                        return _cached_os
            except:
                pass
        _cached_os = "linux"
        return _cached_os
    
    if "windows" in sysname:
        _cached_os = "windows"
        return _cached_os
    
    if "darwin" in sysname:
        _cached_os = "darwin"  # macOS
        return _cached_os
    
    if "freebsd" in sysname or "openbsd" in sysname or "netbsd" in sysname:
        _cached_os = "bsd"
        return _cached_os
    
    _cached_os = "unsupported"
    return _cached_os
