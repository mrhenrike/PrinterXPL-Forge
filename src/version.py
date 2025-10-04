#!/usr/bin/env python3
"""
Version information for PrinterReaper
"""

__version__ = "2.2.11"
__version_info__ = (2, 2, 11)

def get_version():
    """Get the current version string"""
    return __version__

def get_version_info():
    """Get the current version tuple"""
    return __version_info__

def get_version_string():
    """Get formatted version string"""
    return f"Version {__version__}"
