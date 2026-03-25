#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Port Configuration Utility
==========================================
Centralised protocol-to-port mapping with user-override support.

All connection code should call `PortConfig.resolve(protocol)` instead of
using literal port numbers.  This enables every module to honour custom
ports supplied by the operator without touching each module individually.

Supported protocol keys (case-insensitive):
    raw      — RAW/JetDirect/PJL           default 9100
    ipp      — Internet Printing Protocol  default 631
    lpd      — LPD/LPR                    default 515
    snmp     — SNMP                        default 161
    ftp      — FTP                         default 21
    http     — HTTP (EWS / web interface)  default 80
    https    — HTTPS                       default 443
    smb      — SMB/CIFS                    default 445
    telnet   — Telnet management           default 23
    wsd      — WSD (discovery)             default 3702

Usage:
    # One-time setup (call from main() after parsing args):
    from utils.ports import PortConfig
    PortConfig.configure(raw=3910, snmp=1161)

    # In any module:
    from utils.ports import PortConfig
    port = PortConfig.resolve('raw')        # returns override or 9100
    port = PortConfig.resolve('snmp')       # returns override or 161
    port = PortConfig.resolve('ipp')        # returns override or 631

    # Extra probe ports (added on top of defaults for banner scan):
    extras = PortConfig.extra_scan_ports()  # set of int
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

from typing import Dict, FrozenSet, Optional, Set

# ── Protocol defaults ─────────────────────────────────────────────────────────

_DEFAULTS: Dict[str, int] = {
    'raw':    9100,   # RAW / JetDirect / PJL
    'ipp':    631,    # Internet Printing Protocol
    'lpd':    515,    # LPD/LPR
    'snmp':   161,    # SNMP (UDP)
    'ftp':    21,     # FTP management
    'http':   80,     # HTTP embedded web server
    'https':  443,    # HTTPS embedded web server
    'smb':    445,    # SMB/CIFS
    'telnet': 23,     # Telnet management
    'wsd':    3702,   # WSD / WS-Discovery (UDP)
}

# Aliases accepted as protocol names
_ALIASES: Dict[str, str] = {
    'pjl':       'raw',
    'jetdirect': 'raw',
    'print':     'raw',
    '9100':      'raw',
    '631':       'ipp',
    '515':       'lpd',
    'lpr':       'lpd',
    '161':       'snmp',
    '21':        'ftp',
    '80':        'http',
    '443':       'https',
    '445':       'smb',
    '23':        'telnet',
    '3702':      'wsd',
}


class PortConfig:
    """
    Module-level singleton for protocol port configuration.

    All state is class-level so any module importing this class sees the same
    overrides without dependency injection.
    """

    _overrides:    Dict[str, int] = {}   # proto → custom port
    _extra_ports:  Set[int]       = set()  # additional scan ports

    # ── Configuration (call once from main) ───────────────────────────────────

    @classmethod
    def configure(cls,
                  raw:    Optional[int] = None,
                  ipp:    Optional[int] = None,
                  lpd:    Optional[int] = None,
                  snmp:   Optional[int] = None,
                  ftp:    Optional[int] = None,
                  http:   Optional[int] = None,
                  https:  Optional[int] = None,
                  smb:    Optional[int] = None,
                  telnet: Optional[int] = None,
                  wsd:    Optional[int] = None,
                  extra:  Optional[Set[int]] = None) -> None:
        """
        Set custom ports for one or more protocols.

        Args:
            raw:    Override RAW/PJL/JetDirect port (default 9100).
            ipp:    Override IPP port (default 631).
            lpd:    Override LPD port (default 515).
            snmp:   Override SNMP port (default 161).
            ftp:    Override FTP port (default 21).
            http:   Override HTTP port (default 80).
            https:  Override HTTPS port (default 443).
            smb:    Override SMB port (default 445).
            telnet: Override Telnet port (default 23).
            wsd:    Override WSD port (default 3702).
            extra:  Additional ports to include in banner scan sweeps.
        """
        locals_ = {k: v for k, v in locals().items() if k != 'cls' and k != 'extra' and v is not None}
        for proto, port in locals_.items():
            if not (1 <= port <= 65535):
                raise ValueError(f"Port {port} for '{proto}' is out of valid range 1-65535")
            cls._overrides[proto] = int(port)

        if extra:
            cls._extra_ports.update(extra)

    @classmethod
    def configure_from_args(cls, args: object) -> None:
        """
        Convenience method to apply overrides from parsed argparse args.

        Reads attributes: port_raw, port_ipp, port_lpd, port_snmp,
        port_ftp, port_http, port_snmp, port_smb, port_telnet.
        Also reads extra_ports (list of int).
        """
        mapping = {
            'port_raw':    'raw',
            'port_ipp':    'ipp',
            'port_lpd':    'lpd',
            'port_snmp':   'snmp',
            'port_ftp':    'ftp',
            'port_http':   'http',
            'port_https':  'https',
            'port_smb':    'smb',
            'port_telnet': 'telnet',
            'port_wsd':    'wsd',
        }
        for attr, proto in mapping.items():
            val = getattr(args, attr, None)
            if val:
                try:
                    cls._overrides[proto] = int(val)
                except (ValueError, TypeError):
                    pass

        extra = getattr(args, 'extra_ports', None) or []
        for p in extra:
            try:
                cls._extra_ports.add(int(p))
            except (ValueError, TypeError):
                pass

    # ── Resolution ────────────────────────────────────────────────────────────

    @classmethod
    def resolve(cls, protocol: str, fallback: Optional[int] = None) -> int:
        """
        Return the port to use for a given protocol.

        Resolution order:
          1. User override set via configure() or configure_from_args()
          2. Protocol default from _DEFAULTS
          3. Optional fallback argument
          4. 9100 (last resort)

        Args:
            protocol: Protocol key (e.g. 'raw', 'ipp', 'snmp') or alias.
            fallback: Value to use if protocol not recognised.

        Returns:
            Port number as int.
        """
        key = _ALIASES.get(protocol.lower(), protocol.lower())
        if key in cls._overrides:
            return cls._overrides[key]
        if key in _DEFAULTS:
            return _DEFAULTS[key]
        if fallback is not None:
            return int(fallback)
        return 9100

    @classmethod
    def default(cls, protocol: str) -> int:
        """Return the *factory* default port for a protocol, ignoring overrides."""
        key = _ALIASES.get(protocol.lower(), protocol.lower())
        return _DEFAULTS.get(key, 9100)

    @classmethod
    def extra_scan_ports(cls) -> Set[int]:
        """Return extra ports to include in banner/fingerprint sweeps."""
        return set(cls._extra_ports)

    @classmethod
    def all_printer_ports(cls) -> Set[int]:
        """
        Return the full set of ports to probe during a banner scan.
        Includes resolved defaults for all known printer protocols plus any extras.
        """
        base = {cls.resolve(p) for p in ('raw', 'ipp', 'lpd', 'snmp', 'http', 'https', 'smb', 'telnet', 'ftp')}
        base.update(cls._extra_ports)
        return base

    @classmethod
    def reset(cls) -> None:
        """Clear all overrides (mainly for testing)."""
        cls._overrides.clear()
        cls._extra_ports.clear()

    @classmethod
    def summary(cls) -> str:
        """Return a human-readable port mapping summary."""
        lines = []
        for proto, default in _DEFAULTS.items():
            resolved = cls.resolve(proto)
            override = f" [custom: {resolved}]" if resolved != default else ""
            lines.append(f"  {proto:<8} {default}{override}")
        if cls._extra_ports:
            lines.append(f"  extra    {', '.join(str(p) for p in sorted(cls._extra_ports))}")
        return "\n".join(lines)
