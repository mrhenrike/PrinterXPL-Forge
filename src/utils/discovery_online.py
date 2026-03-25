#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Online Discovery Module
========================================
Structured dork-based discovery of exposed printers via Shodan and Censys APIs.

Supports parameterized filters: vendor, model, country, city, region, port, org, CPE.
Printer search terms are implicit — user does not need to specify "printer".
Requires at least one filter parameter when no direct IP target is given.
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import csv
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_log = logging.getLogger(__name__)

try:
    import shodan as _shodan_lib
    SHODAN_AVAILABLE = True
except ImportError:
    SHODAN_AVAILABLE = False

try:
    from censys.search import CensysHosts
    CENSYS_AVAILABLE = True
except ImportError:
    CENSYS_AVAILABLE = False


# ── Geographic region → ISO-3166-1 alpha-2 code map ─────────────────────────

_REGION_COUNTRIES: Dict[str, List[str]] = {
    'latin_america':   ['AR', 'BO', 'BR', 'CL', 'CO', 'CR', 'CU', 'DO', 'EC',
                        'GT', 'HN', 'MX', 'NI', 'PA', 'PE', 'PR', 'SV', 'UY', 'VE'],
    'south_america':   ['AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'GY', 'PE', 'PY', 'SR', 'UY', 'VE'],
    'central_america': ['CR', 'GT', 'HN', 'MX', 'NI', 'PA', 'SV', 'BZ'],
    'north_america':   ['US', 'CA', 'MX'],
    'europe':          ['GB', 'DE', 'FR', 'IT', 'ES', 'PT', 'NL', 'BE', 'CH',
                        'AT', 'SE', 'NO', 'DK', 'FI', 'PL', 'CZ', 'HU', 'RO',
                        'BG', 'HR', 'GR', 'IE', 'SK', 'SI', 'EE', 'LT', 'LV'],
    'asia':            ['CN', 'JP', 'KR', 'IN', 'SG', 'MY', 'TH', 'VN', 'ID',
                        'PH', 'TW', 'HK', 'BD', 'PK', 'LK', 'MM'],
    'middle_east':     ['SA', 'AE', 'IL', 'TR', 'EG', 'IR', 'IQ', 'JO', 'KW', 'LB', 'QA', 'OM', 'BH', 'YE'],
    'africa':          ['ZA', 'NG', 'EG', 'KE', 'MA', 'TN', 'GH', 'ET', 'CI', 'TZ', 'SN', 'UG', 'CM'],
    'oceania':         ['AU', 'NZ', 'FJ', 'PG', 'WS', 'SB'],
    'north_africa':    ['EG', 'MA', 'TN', 'LY', 'DZ', 'SD'],
    'southeast_asia':  ['SG', 'MY', 'TH', 'VN', 'ID', 'PH', 'MM', 'KH', 'LA', 'BN'],
    'eastern_europe':  ['PL', 'CZ', 'HU', 'RO', 'BG', 'SK', 'UA', 'BY', 'MD', 'RS', 'BA', 'AL', 'MK'],
}

# Country name → ISO code (pt-BR and en-US)
_COUNTRY_NAME_TO_CODE: Dict[str, str] = {
    # Portuguese / Spanish
    'brasil': 'BR', 'brazil': 'BR',
    'argentina': 'AR',
    'mexico': 'MX', 'méxico': 'MX',
    'colombia': 'CO',
    'chile': 'CL',
    'peru': 'PE', 'perú': 'PE',
    'venezuela': 'VE',
    'equador': 'EC', 'ecuador': 'EC',
    'bolivia': 'BO',
    'paraguai': 'PY', 'paraguay': 'PY',
    'uruguai': 'UY', 'uruguay': 'UY',
    'cuba': 'CU',
    'costa rica': 'CR',
    'panama': 'PA', 'panamá': 'PA',
    'guatemala': 'GT',
    'honduras': 'HN',
    'el salvador': 'SV',
    'nicaragua': 'NI',
    'republica dominicana': 'DO', 'dominican republic': 'DO',
    # English
    'united states': 'US', 'usa': 'US', 'united states of america': 'US',
    'estados unidos': 'US',
    'canada': 'CA', 'canadá': 'CA',
    'united kingdom': 'GB', 'uk': 'GB', 'england': 'GB',
    'reino unido': 'GB',
    'germany': 'DE', 'alemanha': 'DE', 'deutschland': 'DE',
    'france': 'FR', 'franca': 'FR', 'frança': 'FR',
    'italy': 'IT', 'italia': 'IT', 'itália': 'IT',
    'spain': 'ES', 'espanha': 'ES', 'españa': 'ES',
    'portugal': 'PT',
    'netherlands': 'NL', 'holanda': 'NL', 'holland': 'NL',
    'belgium': 'BE', 'bélgica': 'BE',
    'switzerland': 'CH', 'suíça': 'CH',
    'austria': 'AT', 'áustria': 'AT',
    'sweden': 'SE', 'suécia': 'SE',
    'norway': 'NO', 'noruega': 'NO',
    'denmark': 'DK', 'dinamarca': 'DK',
    'finland': 'FI', 'finlândia': 'FI',
    'poland': 'PL', 'polônia': 'PL',
    'russia': 'RU', 'rússia': 'RU',
    'china': 'CN',
    'japan': 'JP', 'japão': 'JP',
    'south korea': 'KR', 'coreia do sul': 'KR',
    'india': 'IN',
    'australia': 'AU', 'austrália': 'AU',
    'new zealand': 'NZ', 'nova zelândia': 'NZ',
    'south africa': 'ZA', 'africa do sul': 'ZA',
    'nigeria': 'NG',
    'egypt': 'EG', 'egito': 'EG',
    'turkey': 'TR', 'turquia': 'TR',
    'israel': 'IL',
    'saudi arabia': 'SA', 'arabia saudita': 'SA',
    'united arab emirates': 'AE', 'emirates': 'AE', 'emirados arabes': 'AE',
    'singapore': 'SG', 'singapura': 'SG',
}

# Vendor name → canonical Shodan/Censys search strings
_VENDOR_SEARCH_TERMS: Dict[str, List[str]] = {
    'hp':            ['"HP LaserJet"', '"HP OfficeJet"', '"HP DeskJet"', '"HP Color LaserJet"', '"Hewlett-Packard"'],
    'epson':         ['"EPSON"', '"Epson"'],
    'ricoh':         ['"Ricoh"', '"Aficio"', '"RICOH"'],
    'xerox':         ['"Xerox"', '"Phaser"', '"WorkCentre"'],
    'brother':       ['"Brother"', '"BROTHER"'],
    'canon':         ['"Canon"', '"imageRUNNER"', '"CANON"'],
    'kyocera':       ['"Kyocera"', '"TASKalfa"', '"FS-"', '"KYOCERA"'],
    'konica':        ['"Konica Minolta"', '"bizhub"', '"KONICA MINOLTA"'],
    'samsung':       ['"Samsung"', '"SAMSUNG"'],
    'lexmark':       ['"Lexmark"', '"LEXMARK"'],
    'sharp':         ['"Sharp"', '"SHARP"', '"MX-"'],
    'oki':           ['"OKI"', '"OKIDATA"'],
    'toshiba':       ['"Toshiba"', '"TOSHIBA"', '"e-Studio"'],
    'fujifilm':      ['"Fujifilm"', '"Fuji Xerox"', '"FUJIFILM"'],
    'zebra':         ['"Zebra"', '"ZEBRA"'],
    'pantum':        ['"Pantum"', '"PANTUM"'],
    'sindoh':        ['"Sindoh"'],
    'develop':       ['"Develop"', '"ineo"'],
    'utax':          ['"UTAX"', '"Triumph-Adler"'],
    'dell':          ['"Dell"', '"DELL"'],
}

# Implicit printer-related Shodan filter terms (always appended)
_SHODAN_PRINTER_BASE = '(port:9100 OR port:515 OR port:631)'
_CENSYS_PRINTER_BASE = '(services.port=9100 OR services.port=515 OR services.port=631)'

# Port → protocol label
_PORT_LABELS = {9100: 'RAW/PJL', 515: 'LPD', 631: 'IPP', 80: 'HTTP-EWS', 443: 'HTTPS-EWS'}


@dataclass
class DiscoveryParams:
    """Structured parameters for a targeted online printer search."""
    vendors:   List[str]       = field(default_factory=list)   # e.g. ['epson', 'ricoh']
    model:     Optional[str]   = None                           # e.g. "deskjet pro 5500"
    countries: List[str]       = field(default_factory=list)   # ISO codes e.g. ['BR', 'AR']
    city:      Optional[str]   = None                           # e.g. "Sao Paulo"
    regions:   List[str]       = field(default_factory=list)   # e.g. ['latin_america']
    ports:     List[int]       = field(default_factory=list)   # e.g. [515, 9100]
    org:       Optional[str]   = None                           # e.g. "Telefonica"
    cpe:       Optional[str]   = None                           # Censys CPE e.g. "cpe:/h:hp:laserjet"
    limit:     int             = 100

    def has_filters(self) -> bool:
        """Returns True if at least one discovery filter was provided."""
        return bool(
            self.vendors or self.model or self.countries or
            self.city or self.regions or self.ports or
            self.org or self.cpe
        )

    def resolve_country_codes(self) -> List[str]:
        """Resolve names to ISO codes and expand regions."""
        codes: Set[str] = set()
        for c in self.countries:
            normalized = c.strip().lower()
            if len(c) == 2 and c.upper() == c:
                codes.add(c.upper())
            elif normalized in _COUNTRY_NAME_TO_CODE:
                codes.add(_COUNTRY_NAME_TO_CODE[normalized])
            else:
                # Try partial match
                for name, code in _COUNTRY_NAME_TO_CODE.items():
                    if normalized in name or name in normalized:
                        codes.add(code)
                        break
        for region in self.regions:
            region_key = region.lower().replace('-', '_').replace(' ', '_')
            codes.update(_REGION_COUNTRIES.get(region_key, []))
        return sorted(codes)


class DorkQueryBuilder:
    """
    Builds structured Shodan and Censys dork queries from DiscoveryParams.

    Printer context is always implicit — user only provides filtering criteria.
    Supports multi-vendor, multi-country, region expansion, and CPE filtering.
    """

    def __init__(self, params: DiscoveryParams) -> None:
        self.params = params

    # ── Shodan ────────────────────────────────────────────────────────────────

    def build_shodan_queries(self) -> List[Dict[str, str]]:
        """
        Returns a list of Shodan query dicts: {query, description}.

        Each vendor generates its own query (API-efficient).
        If no vendor is specified, uses generic printer banner terms.
        Country/region/port/city are always appended as Shodan filters.
        """
        geo_part   = self._shodan_geo_part()
        port_part  = self._shodan_port_part()
        city_part  = self._shodan_city_part()
        org_part   = f' org:"{self.params.org}"' if self.params.org else ''
        model_part = f' "{self.params.model}"' if self.params.model else ''
        suffix     = f"{geo_part}{city_part}{org_part}{model_part}{port_part}"

        queries: List[Dict[str, str]] = []

        if self.params.vendors:
            for vendor in self.params.vendors:
                vendor_key = vendor.lower()
                search_terms = _VENDOR_SEARCH_TERMS.get(vendor_key, [f'"{vendor}"'])
                # Use the first 2 search terms per vendor to avoid too many queries
                for term in search_terms[:2]:
                    query = f"{term}{suffix}"
                    queries.append({
                        'query': query,
                        'description': f"{vendor.title()} printers{self._geo_label()}",
                        'vendor': vendor,
                    })
        else:
            # Generic: use printer banner signatures
            generic_terms = [
                '"@PJL INFO"',
                '"@PJL USTATUS"',
                '"READY" port:9100',
                '"PJL"',
            ]
            for term in generic_terms:
                query = f"{term}{suffix}"
                if not port_part:
                    query += f" {_SHODAN_PRINTER_BASE}"
                queries.append({
                    'query': query.strip(),
                    'description': f"Generic printers{self._geo_label()}",
                    'vendor': None,
                })

        return queries

    def _shodan_geo_part(self) -> str:
        codes = self.params.resolve_country_codes()
        if not codes:
            return ''
        if len(codes) == 1:
            return f' country:{codes[0]}'
        # Multiple countries → join with OR in Shodan
        return ' (' + ' OR '.join(f'country:{c}' for c in codes) + ')'

    def _shodan_port_part(self) -> str:
        if not self.params.ports:
            return ''
        if len(self.params.ports) == 1:
            return f' port:{self.params.ports[0]}'
        return ' (' + ' OR '.join(f'port:{p}' for p in self.params.ports) + ')'

    def _shodan_city_part(self) -> str:
        if not self.params.city:
            return ''
        return f' city:"{self.params.city}"'

    # ── Censys ────────────────────────────────────────────────────────────────

    def build_censys_queries(self) -> List[Dict[str, str]]:
        """Returns a list of Censys query dicts: {query, description}."""
        geo_part  = self._censys_geo_part()
        port_part = self._censys_port_part()
        city_part = self._censys_city_part()
        org_part  = f' AND autonomous_system.name="{self.params.org}"' if self.params.org else ''
        cpe_part  = f' AND services.software.uniform_resource_identifier="{self.params.cpe}"' if self.params.cpe else ''
        model_part = f' AND services.banner="{self.params.model}"' if self.params.model else ''
        suffix     = f"{geo_part}{city_part}{org_part}{cpe_part}{model_part}{port_part}"

        queries: List[Dict[str, str]] = []

        if self.params.vendors:
            for vendor in self.params.vendors:
                vendor_key = vendor.lower()
                raw_terms  = _VENDOR_SEARCH_TERMS.get(vendor_key, [f'"{vendor}"'])
                # Strip Shodan quoting style → Censys banner search
                censys_terms = [t.strip('"') for t in raw_terms[:2]]
                for term in censys_terms:
                    query = f'services.banner="{term}"{suffix}'
                    if not port_part:
                        # Append implicit printer port filter
                        query += f' AND ({_CENSYS_PRINTER_BASE.lstrip("(")}'
                    queries.append({
                        'query': query,
                        'description': f"{vendor.title()} printers (Censys){self._geo_label()}",
                        'vendor': vendor,
                    })
        else:
            generic_censys = [
                'services.banner="@PJL"',
                'services.banner="READY"',
            ]
            for term in generic_censys:
                query = f"{term}{suffix}"
                if not port_part:
                    query += f' AND {_CENSYS_PRINTER_BASE}'
                queries.append({
                    'query': query,
                    'description': f"Generic printers (Censys){self._geo_label()}",
                    'vendor': None,
                })

        return queries

    def _censys_geo_part(self) -> str:
        codes = self.params.resolve_country_codes()
        if not codes:
            return ''
        if len(codes) == 1:
            return f' AND location.country_code="{codes[0]}"'
        return ' AND (' + ' OR '.join(f'location.country_code="{c}"' for c in codes) + ')'

    def _censys_port_part(self) -> str:
        if not self.params.ports:
            return ''
        if len(self.params.ports) == 1:
            return f' AND services.port={self.params.ports[0]}'
        return ' AND (' + ' OR '.join(f'services.port={p}' for p in self.params.ports) + ')'

    def _censys_city_part(self) -> str:
        if not self.params.city:
            return ''
        return f' AND location.city="{self.params.city}"'

    # ── Labels ────────────────────────────────────────────────────────────────

    def _geo_label(self) -> str:
        parts = []
        codes = self.params.resolve_country_codes()
        if codes:
            parts.append('/'.join(codes[:4]) + ('...' if len(codes) > 4 else ''))
        if self.params.city:
            parts.append(self.params.city)
        if self.params.regions:
            parts.append('+'.join(self.params.regions))
        return (', ' + ', '.join(parts)) if parts else ''

    def describe(self) -> str:
        """Human-readable summary of the query being built."""
        parts = []
        if self.params.vendors:
            parts.append(f"vendors={','.join(self.params.vendors)}")
        if self.params.model:
            parts.append(f"model={self.params.model!r}")
        codes = self.params.resolve_country_codes()
        if codes:
            label = ','.join(codes[:6]) + ('...' if len(codes) > 6 else '')
            parts.append(f"countries=[{label}]")
        if self.params.city:
            parts.append(f"city={self.params.city!r}")
        if self.params.regions:
            parts.append(f"regions={','.join(self.params.regions)}")
        if self.params.ports:
            labels = [_PORT_LABELS.get(p, str(p)) for p in self.params.ports]
            parts.append(f"ports={','.join(labels)}")
        if self.params.org:
            parts.append(f"org={self.params.org!r}")
        if self.params.cpe:
            parts.append(f"cpe={self.params.cpe!r}")
        return ' | '.join(parts) if parts else 'generic (all printers)'


# ── Result model ─────────────────────────────────────────────────────────────

@dataclass
class PrinterHit:
    """A single discovered printer from Shodan or Censys."""
    ip:           str
    port:         int
    source:       str
    country:      str  = ''
    country_code: str  = ''
    city:         str  = ''
    org:          str  = ''
    hostnames:    List[str] = field(default_factory=list)
    banner:       str  = ''
    product:      str  = ''
    version:      str  = ''
    vendor:       str  = ''
    timestamp:    str  = ''

    def to_dict(self) -> Dict:
        return self.__dict__.copy()


# ── Shodan search ─────────────────────────────────────────────────────────────

class ShodanSearcher:
    """Thin wrapper around the Shodan API with structured-query support."""

    def __init__(self, api_key: str) -> None:
        if not SHODAN_AVAILABLE:
            raise ImportError("shodan package not installed — pip install shodan")
        self._api = _shodan_lib.Shodan(api_key)

    def plan_info(self) -> Dict:
        try:
            return self._api.info()
        except Exception:
            return {}

    def search(self, query: str, limit: int = 100, vendor: str = '') -> List[PrinterHit]:
        hits: List[PrinterHit] = []
        try:
            _log.debug("Shodan query: %s", query)
            result = self._api.search(query, limit=limit)
            for m in result.get('matches', []):
                loc  = m.get('location', {})
                hits.append(PrinterHit(
                    ip           = m.get('ip_str', ''),
                    port         = m.get('port', 9100),
                    source       = 'shodan',
                    country      = loc.get('country_name', ''),
                    country_code = loc.get('country_code', ''),
                    city         = loc.get('city', ''),
                    org          = m.get('org', ''),
                    hostnames    = m.get('hostnames', []),
                    banner       = (m.get('data', '') or '')[:600],
                    product      = m.get('product', ''),
                    version      = m.get('version', ''),
                    vendor       = vendor,
                    timestamp    = m.get('timestamp', ''),
                ))
        except _shodan_lib.APIError as exc:
            _log.warning("Shodan API error: %s", exc)
        except Exception as exc:
            _log.warning("Shodan search error: %s", exc)
        return hits


# ── Censys search ─────────────────────────────────────────────────────────────

class CensysSearcher:
    """Thin wrapper around Censys Hosts API with structured-query support."""

    def __init__(self, api_id: str, api_secret: str) -> None:
        if not CENSYS_AVAILABLE:
            raise ImportError("censys package not installed — pip install censys")
        self._api = CensysHosts(api_id, api_secret)

    def search(self, query: str, limit: int = 100, vendor: str = '') -> List[PrinterHit]:
        hits: List[PrinterHit] = []
        count = 0
        try:
            _log.debug("Censys query: %s", query)
            for page in self._api.search(query, per_page=min(100, limit), pages=-1):
                for host in page:
                    if count >= limit:
                        break
                    loc = host.get('location', {})
                    asn = host.get('autonomous_system', {})
                    svcs = host.get('services', [{}])
                    port = svcs[0].get('port', 9100) if svcs else 9100
                    hits.append(PrinterHit(
                        ip           = host.get('ip', ''),
                        port         = port,
                        source       = 'censys',
                        country      = loc.get('country', ''),
                        country_code = loc.get('country_code', ''),
                        city         = loc.get('city', ''),
                        org          = asn.get('name', ''),
                        hostnames    = host.get('names', []),
                        banner       = str(svcs[0])[:600] if svcs else '',
                        product      = '',
                        version      = '',
                        vendor       = vendor,
                        timestamp    = host.get('last_updated_at', ''),
                    ))
                    count += 1
                if count >= limit:
                    break
        except Exception as exc:
            _log.warning("Censys search error: %s", exc)
        return hits


# ── Manager (main public API) ─────────────────────────────────────────────────

class OnlineDiscoveryManager:
    """
    Orchestrates dork-based printer discovery across Shodan and Censys.

    Usage:
        params = DiscoveryParams(vendors=['epson','ricoh'], regions=['latin_america'], ports=[515])
        mgr    = OnlineDiscoveryManager(shodan_key='...', censys_id='...', censys_secret='...')
        hits   = mgr.targeted_search(params)
        mgr.print_results(hits)
    """

    # ── ANSI colours ──────────────────────────────────────────────────────────
    _GRN = '\033[0;32m'
    _YEL = '\033[1;33m'
    _CYN = '\033[1;36m'
    _RED = '\033[1;31m'
    _DIM = '\033[2;37m'
    _RST = '\033[0m'

    def __init__(self,
                 shodan_key:     Optional[str] = None,
                 censys_id:      Optional[str] = None,
                 censys_secret:  Optional[str] = None) -> None:

        # Try loading credentials from config if not passed directly
        try:
            from utils.config import load_config, shodan_key as _sk, censys_credentials
            load_config()
            if not shodan_key:
                shodan_key = _sk()
            if not (censys_id and censys_secret):
                censys_id, censys_secret = censys_credentials()
        except Exception:
            pass

        self._shodan:  Optional[ShodanSearcher]  = None
        self._censys:  Optional[CensysSearcher]  = None
        self._hits:    List[PrinterHit]           = []

        if shodan_key:
            try:
                self._shodan = ShodanSearcher(shodan_key)
                _log.info("Shodan API initialized")
            except Exception as exc:
                print(f"  {self._YEL}[!]{self._RST} Shodan init failed: {exc}")

        if censys_id and censys_secret:
            try:
                self._censys = CensysSearcher(censys_id, censys_secret)
                _log.info("Censys API initialized")
            except Exception as exc:
                print(f"  {self._YEL}[!]{self._RST} Censys init failed: {exc}")

    # ── Public entry points ───────────────────────────────────────────────────

    def targeted_search(self, params: DiscoveryParams) -> List[PrinterHit]:
        """
        Run a structured dork search using provided parameters.

        Raises ValueError if params.has_filters() returns False (no criteria given).
        Returns deduplicated list of PrinterHit, sorted by country + IP.
        """
        if not params.has_filters():
            raise ValueError(
                "At least one discovery filter is required: --dork-vendor, --dork-country, "
                "--dork-city, --dork-region, --dork-port, --dork-org, --dork-cpe, or --dork-model\n"
                "When searching without geographic/vendor filters, provide a direct IP target instead."
            )

        builder = DorkQueryBuilder(params)
        print(f"\n  {self._CYN}{'='*68}{self._RST}")
        print(f"  {self._CYN}Online Printer Discovery — Dork Mode{self._RST}")
        print(f"  Filter: {builder.describe()}")
        print(f"  Limit : {params.limit} results per query")
        print(f"  {self._CYN}{'='*68}{self._RST}\n")

        all_hits: List[PrinterHit] = []
        delay = 1.2  # seconds between API calls

        if self._shodan:
            queries = builder.build_shodan_queries()
            print(f"  {self._GRN}[Shodan]{self._RST} {len(queries)} queries")
            for idx, q in enumerate(queries, 1):
                print(f"    [{idx}/{len(queries)}] {q['description']}")
                print(f"           Query: {self._DIM}{q['query']}{self._RST}")
                hits = self._shodan.search(q['query'], limit=params.limit, vendor=q.get('vendor', ''))
                print(f"           Found: {self._GRN}{len(hits)}{self._RST}")
                all_hits.extend(hits)
                if idx < len(queries):
                    time.sleep(delay)

        if self._censys:
            queries = builder.build_censys_queries()
            print(f"\n  {self._GRN}[Censys]{self._RST} {len(queries)} queries")
            for idx, q in enumerate(queries, 1):
                print(f"    [{idx}/{len(queries)}] {q['description']}")
                print(f"           Query: {self._DIM}{q['query']}{self._RST}")
                hits = self._censys.search(q['query'], limit=params.limit, vendor=q.get('vendor', ''))
                print(f"           Found: {self._GRN}{len(hits)}{self._RST}")
                all_hits.extend(hits)
                if idx < len(queries):
                    time.sleep(delay)

        if not self._shodan and not self._censys:
            print(f"  {self._RED}[!]{self._RST} No API credentials configured.")
            print(f"      Add shodan/censys keys to config.json — see: python printer-reaper.py --check-config")
            return []

        # Deduplicate by IP:port
        seen: Set[Tuple[str, int]] = set()
        unique: List[PrinterHit] = []
        for h in all_hits:
            key = (h.ip, h.port)
            if key not in seen:
                seen.add(key)
                unique.append(h)

        unique.sort(key=lambda h: (h.country_code, h.ip))
        self._hits = unique
        return unique

    def print_results(self, hits: List[PrinterHit]) -> None:
        """Print a formatted table of discovered printers."""
        if not hits:
            print(f"  {self._YEL}[!]{self._RST} No printers found matching the given filters.")
            return

        print(f"\n  {self._CYN}{'='*68}{self._RST}")
        print(f"  {self._CYN}Results — {len(hits)} unique printer(s) found{self._RST}")
        print(f"  {self._CYN}{'='*68}{self._RST}")
        print(f"  {'IP':<16} {'Port':<6} {'CC':<4} {'City':<18} {'Org':<28} {'Src':<8}")
        print(f"  {'-'*68}")

        for h in hits:
            port_label = _PORT_LABELS.get(h.port, str(h.port))
            org_short  = (h.org[:26] + '..') if len(h.org) > 28 else h.org
            city_short = (h.city[:16] + '..') if len(h.city) > 18 else h.city
            print(f"  {self._GRN}{h.ip:<16}{self._RST} {port_label:<6} {h.country_code:<4} "
                  f"{city_short:<18} {org_short:<28} {h.source}")

        print()
        # Country stats
        by_cc: Dict[str, int] = defaultdict(int)
        for h in hits:
            by_cc[h.country_code or '??'] += 1
        stat_line = '  '.join(f"{cc}:{n}" for cc, n in sorted(by_cc.items(), key=lambda x: -x[1])[:10])
        print(f"  Distribution: {stat_line}")
        print()

    def export_results(self, hits: List[PrinterHit], output_path: Optional[str] = None) -> Optional[str]:
        """Export results to JSON. Returns path to saved file."""
        if not hits:
            return None
        ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = output_path or f'.log/discovery_{ts}.json'
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        data = {
            'generated': datetime.now().isoformat(),
            'total':     len(hits),
            'results':   [h.to_dict() for h in hits],
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"  {self._GRN}[+]{self._RST} Results saved to {path}")
        return path

    # ── Legacy compatibility shim (for old --discover-online without dorks) ───

    def discover(self, max_results_per_query: int = 100,
                 delay_between_queries: float = 1.2,
                 use_shodan: bool = True,
                 use_censys: bool = True) -> Dict:
        """
        Legacy broad discovery (no filters).
        Deprecated — use targeted_search(DiscoveryParams(...)) instead.
        """
        params = DiscoveryParams(
            vendors=list(_VENDOR_SEARCH_TERMS.keys())[:6],
            ports=[9100],
            limit=max_results_per_query,
        )
        hits = self.targeted_search(params)
        self.print_results(hits)
        self.export_results(hits)
        return {'total_devices': len(hits), 'timestamp': datetime.now().isoformat()}
