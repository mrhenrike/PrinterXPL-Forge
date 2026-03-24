#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Configuration Loader
======================================
Loads config.yaml from the project root (or a path set via PRINTERREAPER_CONFIG
environment variable). Falls back gracefully to defaults when the file is absent.

Values can also be overridden by environment variables:
  SHODAN_API_KEY, CENSYS_API_ID, CENSYS_API_SECRET, NVD_API_KEY
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

# Locate the project root (two directories up from this file)
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent.parent

_DEFAULT_CONFIG: dict = {
    'shodan':    {'api_key': ''},
    'censys':    {'api_id': '', 'api_secret': ''},
    'nvd':       {'api_key': ''},
    'network':   {'timeout': 5, 'snmp_community': 'public', 'snmp_timeout': 2},
    'ml':        {'enabled': False, 'model_dir': '.ml_models', 'min_confidence': 0.60},
    'discovery': {'max_results_per_query': 50, 'delay_between_queries': 1.5},
    'output':    {'color': True, 'verbose': False, 'log_dir': '.log'},
}

_config: dict | None = None


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config(path: str | None = None) -> dict:
    """
    Load and return the merged configuration dict.

    Resolution order (highest priority first):
      1. Environment variables  (SHODAN_API_KEY, CENSYS_API_ID, …)
      2. config.yaml at *path* (or PRINTERREAPER_CONFIG env var or project root)
      3. Built-in defaults
    """
    global _config

    # Determine config file location
    env_path = os.environ.get('PRINTERREAPER_CONFIG')
    cfg_path = Path(path or env_path or _PROJECT_ROOT / 'config.yaml')

    # Start from defaults
    merged = dict(_DEFAULT_CONFIG)

    # Overlay config.yaml if it exists
    if cfg_path.exists():
        try:
            import yaml  # pyyaml — optional
            with open(cfg_path, encoding='utf-8') as fh:
                file_cfg = yaml.safe_load(fh) or {}
            merged = _deep_merge(merged, file_cfg)
            _log.debug("Loaded config from %s", cfg_path)
        except ImportError:
            _log.warning("pyyaml not installed — config.yaml ignored; install with: pip install pyyaml")
        except Exception as exc:
            _log.warning("Cannot read config.yaml: %s", exc)

    # Override with environment variables
    if os.environ.get('SHODAN_API_KEY'):
        merged['shodan']['api_key'] = os.environ['SHODAN_API_KEY']
    if os.environ.get('CENSYS_API_ID'):
        merged['censys']['api_id'] = os.environ['CENSYS_API_ID']
    if os.environ.get('CENSYS_API_SECRET'):
        merged['censys']['api_secret'] = os.environ['CENSYS_API_SECRET']
    if os.environ.get('NVD_API_KEY'):
        merged['nvd']['api_key'] = os.environ['NVD_API_KEY']

    _config = merged
    return merged


def get(section: str, key: str, default: Any = None) -> Any:
    """
    Convenience accessor.

    Example::
        get('shodan', 'api_key')
    """
    cfg = _config or load_config()
    return cfg.get(section, {}).get(key, default)


def get_section(section: str) -> dict:
    """Return an entire config section as a dict."""
    cfg = _config or load_config()
    return dict(cfg.get(section, {}))


def shodan_key() -> str:
    """Return the Shodan API key or an empty string."""
    return get('shodan', 'api_key', '')


def censys_credentials() -> tuple[str, str]:
    """Return (api_id, api_secret) for Censys."""
    return get('censys', 'api_id', ''), get('censys', 'api_secret', '')


def nvd_key() -> str:
    """Return the NVD API key or an empty string."""
    return get('nvd', 'api_key', '')


def ml_enabled() -> bool:
    """Return True if the ML engine is enabled in config."""
    return bool(get('ml', 'enabled', False))


def network_timeout() -> float:
    """Return the configured network timeout in seconds."""
    return float(get('network', 'timeout', 5))
