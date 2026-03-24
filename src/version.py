#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — version control module.

Versioning scheme: MAJOR.MINOR.PATCH  (semver-inspired)
  MAJOR — breaking changes or major new feature sets
  MINOR — new features, backwards-compatible
  PATCH — bug fixes, small improvements
"""

# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

__version__      = "3.3.0"
__version_info__ = (3, 3, 0)
__release_date__ = "2026-03-24"
__author__       = "Andre Henrique"
__license__      = "MIT"


def get_version() -> str:
    """Return the bare version string, e.g. '3.0.0'."""
    return __version__


def get_version_info() -> tuple:
    """Return the version as a (major, minor, patch) tuple."""
    return __version_info__


def get_version_string() -> str:
    """Return formatted version string used in the banner."""
    return f"Version {__version__} ({__release_date__})"
