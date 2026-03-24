#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Configuration Loader
======================================
Loads config.json (JSON) from the project root, a path set via the
--config CLI flag, or the PRINTERREAPER_CONFIG environment variable.
Also accepts the legacy config.yaml format (requires pyyaml).

Supports multiple API keys per provider (first non-empty key is used).
Validates which features are available based on configured credentials
and warns the user when a feature is called without required keys.

Resolution order (highest priority first):
  1. CLI flag: --config /path/to/config.json
  2. Environment variable: PRINTERREAPER_CONFIG
  3. config.json in project root (next to src/)
  4. config.yaml in project root (legacy fallback)
  5. Built-in defaults (no credentials — limited features)

Override individual keys via environment variables:
  SHODAN_API_KEY, CENSYS_API_ID, CENSYS_API_SECRET,
  NVD_API_KEY, VIRUSTOTAL_API_KEY, GREYNOISE_API_KEY,
  ABUSE_IPDB_API_KEY, OPENAI_API_KEY
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_log = logging.getLogger(__name__)

# ── Project root detection ────────────────────────────────────────────────────

_HERE         = Path(__file__).resolve().parent           # src/utils/
_PROJECT_ROOT = _HERE.parent.parent                       # project root

# ── Feature → credential mapping ─────────────────────────────────────────────
# Maps feature names to human-readable labels and the config key(s) needed.

FEATURE_REQUIREMENTS: Dict[str, Dict] = {
    'shodan_search': {
        'label':   'Shodan search / --discover-online',
        'section': 'shodan',
        'keys':    ['api_key'],
        'url':     'https://account.shodan.io/',
    },
    'censys_search': {
        'label':   'Censys search / --discover-online',
        'section': 'censys',
        'keys':    ['api_id', 'api_secret'],
        'url':     'https://search.censys.io/account/api',
    },
    'nvd_lookup': {
        'label':   'NVD CVE lookup (higher rate limit)',
        'section': 'nvd',
        'keys':    ['api_key'],
        'url':     'https://nvd.nist.gov/developers/request-an-api-key',
        'optional': True,  # NVD works without key, just rate-limited
    },
    'virustotal': {
        'label':   'VirusTotal IP/hash reputation',
        'section': 'virustotal',
        'keys':    ['api_key'],
        'url':     'https://www.virustotal.com/gui/my-apikey',
    },
    'greynoise': {
        'label':   'GreyNoise IP noise scoring',
        'section': 'greynoise',
        'keys':    ['api_key'],
        'url':     'https://viz.greynoise.io/account/api-key',
    },
    'abuse_ipdb': {
        'label':   'AbuseIPDB reputation',
        'section': 'abuse_ipdb',
        'keys':    ['api_key'],
        'url':     'https://www.abuseipdb.com/account/api',
    },
    'openai': {
        'label':   'OpenAI AI-assisted analysis',
        'section': 'openai',
        'keys':    ['api_key'],
        'url':     'https://platform.openai.com/api-keys',
    },
}

# ── Defaults ──────────────────────────────────────────────────────────────────

_DEFAULTS: Dict = {
    'shodan':      [{'label': 'primary', 'api_key': ''}],
    'censys':      [{'label': 'primary', 'api_id': '', 'api_secret': ''}],
    'nvd':         [{'label': 'primary', 'api_key': ''}],
    'virustotal':  [{'label': 'primary', 'api_key': ''}],
    'greynoise':   [{'label': 'primary', 'api_key': ''}],
    'abuse_ipdb':  [{'label': 'primary', 'api_key': ''}],
    'openai':      [{'label': 'primary', 'api_key': '', 'model': 'gpt-4o-mini'}],
    'network':     {'timeout': 5, 'snmp_community': 'public', 'snmp_timeout': 2, 'max_retries': 1},
    'ml':          {'enabled': False, 'model_dir': '.ml_models', 'min_confidence': 0.60},
    'discovery':   {'max_results_per_query': 50, 'delay_between_queries': 1.5},
    'output':      {'color': True, 'verbose': False, 'log_dir': '.log'},
}

# ── Module state ──────────────────────────────────────────────────────────────

_config:      Dict | None = None
_config_path: Path | None = None
_load_errors: List[str]   = []


# ── Loader ────────────────────────────────────────────────────────────────────

def _find_config_file(explicit_path: str | None = None) -> Optional[Path]:
    """Return the first valid config file path, or None."""
    candidates = []

    if explicit_path:
        candidates.append(Path(explicit_path))
    env_path = os.environ.get('PRINTERREAPER_CONFIG')
    if env_path:
        candidates.append(Path(env_path))

    candidates.extend([
        _PROJECT_ROOT / 'config.json',
        _PROJECT_ROOT / 'config.yaml',
        Path.cwd() / 'config.json',
        Path.cwd() / 'config.yaml',
    ])

    for p in candidates:
        if p.exists():
            return p
    return None


def _load_json(path: Path) -> Dict:
    with open(path, encoding='utf-8') as fh:
        raw = json.load(fh)
    # Strip the _comment key (documentation only)
    raw.pop('_comment', None)
    return raw


def _load_yaml(path: Path) -> Dict:
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml not installed — cannot load .yaml config. "
                          "Run: pip install pyyaml  OR  use config.json instead.")
    with open(path, encoding='utf-8') as fh:
        return yaml.safe_load(fh) or {}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _normalise_provider(section: Any) -> List[Dict]:
    """
    Normalise a provider entry to a list of credential dicts.

    Accepts both the new list format and the legacy single-dict format:
      new:    [{"label": "primary", "api_key": "..."}]
      legacy: {"api_key": "..."}
    """
    if isinstance(section, list):
        return section
    if isinstance(section, dict):
        return [section]
    return []


def load_config(path: str | None = None) -> Dict:
    """
    Load and return the merged configuration dict.

    Args:
        path: Explicit path to config file (overrides all auto-detection).

    Returns:
        The merged configuration dict.
    """
    global _config, _config_path, _load_errors
    _load_errors = []

    cfg_path = _find_config_file(path)
    merged = dict(_DEFAULTS)

    if cfg_path:
        try:
            if cfg_path.suffix == '.json':
                file_cfg = _load_json(cfg_path)
            else:
                file_cfg = _load_yaml(cfg_path)
            merged = _deep_merge(merged, file_cfg)
            _config_path = cfg_path
            _log.debug("Loaded config from %s", cfg_path)
        except Exception as exc:
            msg = f"Cannot read config file {cfg_path}: {exc}"
            _load_errors.append(msg)
            _log.warning(msg)
    else:
        _log.debug("No config file found — using defaults (no credentials)")

    # Override with environment variables
    _apply_env_overrides(merged)

    _config = merged
    return merged


def _apply_env_overrides(cfg: Dict) -> None:
    """Apply environment variable overrides to the config dict."""
    env_map = {
        'SHODAN_API_KEY':     ('shodan',     'api_key'),
        'CENSYS_API_ID':      ('censys',     'api_id'),
        'CENSYS_API_SECRET':  ('censys',     'api_secret'),
        'NVD_API_KEY':        ('nvd',        'api_key'),
        'VIRUSTOTAL_API_KEY': ('virustotal', 'api_key'),
        'GREYNOISE_API_KEY':  ('greynoise',  'api_key'),
        'ABUSE_IPDB_API_KEY': ('abuse_ipdb', 'api_key'),
        'OPENAI_API_KEY':     ('openai',     'api_key'),
    }
    for env_var, (section, key) in env_map.items():
        val = os.environ.get(env_var, '').strip()
        if val:
            entries = _normalise_provider(cfg.get(section, []))
            if entries:
                entries[0][key] = val
            else:
                entries = [{'label': 'env', key: val}]
            cfg[section] = entries


# ── Credential accessors ──────────────────────────────────────────────────────

def _get_first_key(section: str, key: str) -> str:
    """Return the first non-empty value of *key* from the provider list."""
    cfg = _config or load_config()
    entries = _normalise_provider(cfg.get(section, []))
    for entry in entries:
        val = str(entry.get(key, '')).strip()
        if val:
            return val
    return ''


def _get_first_entry(section: str) -> Dict:
    """Return the first non-empty credential entry for a provider section."""
    cfg = _config or load_config()
    entries = _normalise_provider(cfg.get(section, []))
    for entry in entries:
        # An entry is "valid" if at least one non-label key is non-empty
        has_value = any(v for k, v in entry.items()
                        if k not in ('label', '_comment') and str(v).strip())
        if has_value:
            return entry
    return {}


def get(section: str, key: str, default: Any = None) -> Any:
    """Get a value from a flat config section (network, ml, output, etc.)."""
    cfg = _config or load_config()
    sec = cfg.get(section, {})
    if isinstance(sec, dict):
        return sec.get(key, default)
    # Provider list — return first key
    return _get_first_key(section, key) or default


def get_section(section: str) -> dict:
    """Return a flat config section as a dict."""
    cfg = _config or load_config()
    sec = cfg.get(section, {})
    return dict(sec) if isinstance(sec, dict) else {}


# ── Feature availability ──────────────────────────────────────────────────────

def feature_available(feature: str) -> bool:
    """
    Return True if the required credentials for *feature* are configured.

    Example::
        if not feature_available('shodan_search'):
            print(warn_missing('shodan_search'))
    """
    req = FEATURE_REQUIREMENTS.get(feature)
    if not req:
        return False
    section = req['section']
    keys    = req['keys']
    entry   = _get_first_entry(section)
    return all(str(entry.get(k, '')).strip() for k in keys)


def warn_missing(feature: str, verbose: bool = True) -> str:
    """
    Return a formatted warning string for a missing credential.

    Args:
        feature: Feature name from FEATURE_REQUIREMENTS.
        verbose: If True, include the URL to get credentials.

    Returns:
        A human-readable warning string.
    """
    req = FEATURE_REQUIREMENTS.get(feature)
    if not req:
        return f"[!] Unknown feature: {feature}"

    label   = req['label']
    section = req['section']
    keys    = req['keys']
    url     = req.get('url', '')
    optional = req.get('optional', False)

    missing = [k for k in keys if not str(_get_first_entry(section).get(k, '')).strip()]
    kind    = "optional enhancement" if optional else "required credential"
    msg     = (f"[!] Feature unavailable: {label}\n"
               f"    Missing {kind}: config.json → {section}[].{', '.join(missing)}")
    if verbose and url:
        msg += f"\n    Get credentials: {url}"
    return msg


def check_all_features(print_report: bool = True) -> Dict[str, bool]:
    """
    Check availability of all known features.

    Args:
        print_report: If True, print a formatted availability table to stdout.

    Returns:
        Dict of {feature_name: bool}.
    """
    status = {f: feature_available(f) for f in FEATURE_REQUIREMENTS}

    if print_report:
        cfg_src = str(_config_path) if _config_path else 'no config file (defaults only)'
        print(f"\n  Config: {cfg_src}")
        print(f"\n  {'Feature':<35} {'Status'}")
        print(f"  {'-'*60}")
        for feat, avail in status.items():
            req  = FEATURE_REQUIREMENTS[feat]
            opt  = ' (optional)' if req.get('optional') else ''
            icon = '\033[0;32mOK\033[0m' if avail else '\033[1;33mNO KEY\033[0m'
            print(f"  {req['label']:<35} {icon}{opt}")
        print()

    return status


def require_feature(feature: str, exit_on_missing: bool = False) -> bool:
    """
    Assert a feature is available; warn if not.

    Args:
        feature:         Feature name from FEATURE_REQUIREMENTS.
        exit_on_missing: If True, raise SystemExit when feature is missing.

    Returns:
        True if available, False otherwise (after printing a warning).
    """
    if feature_available(feature):
        return True

    req = FEATURE_REQUIREMENTS.get(feature, {})
    if req.get('optional'):
        _log.info(warn_missing(feature, verbose=False))
    else:
        print(warn_missing(feature, verbose=True))

    if exit_on_missing:
        raise SystemExit(1)
    return False


# ── Convenience accessors ─────────────────────────────────────────────────────

def shodan_key() -> str:
    """Return the first non-empty Shodan API key."""
    return _get_first_key('shodan', 'api_key')


def censys_credentials() -> Tuple[str, str]:
    """Return (api_id, api_secret) for Censys."""
    entry = _get_first_entry('censys')
    return (str(entry.get('api_id', '')).strip(),
            str(entry.get('api_secret', '')).strip())


def nvd_key() -> str:
    """Return the NVD API key (empty string = use public rate limit)."""
    return _get_first_key('nvd', 'api_key')


def virustotal_key() -> str:
    """Return the VirusTotal API key."""
    return _get_first_key('virustotal', 'api_key')


def greynoise_key() -> str:
    """Return the GreyNoise API key."""
    return _get_first_key('greynoise', 'api_key')


def openai_key() -> str:
    """Return the OpenAI API key."""
    return _get_first_key('openai', 'api_key')


def openai_model() -> str:
    """Return the configured OpenAI model name."""
    entry = _get_first_entry('openai')
    return str(entry.get('model', 'gpt-4o-mini')).strip() or 'gpt-4o-mini'


def ml_enabled() -> bool:
    """Return True if the ML engine is enabled in config."""
    return bool(get('ml', 'enabled', False))


def network_timeout() -> float:
    """Return the configured network timeout in seconds."""
    return float(get('network', 'timeout', 5))


def config_path() -> Optional[Path]:
    """Return the path of the loaded config file, or None."""
    return _config_path
