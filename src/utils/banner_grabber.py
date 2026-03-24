#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Banner Grabber
================================
Collects identification banners from all relevant printer protocols:
  HTTP / HTTPS  — headers + title + WSD
  IPP           — Get-Printer-Attributes (model, firmware, serial, langs)
  RAW/9100      — PJL INFO ID
  LPD/515       — RFC 1179 queue listing
  SNMP          — sysDescr, hrDeviceDescr, prtInterpreterDescription
  SMB/445       — optional share enumeration

Returns a unified PrinterFingerprint dataclass with everything collected.
"""

# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import logging
import re
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_log = logging.getLogger(__name__)

# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class PrinterFingerprint:
    """Aggregated banner/fingerprint data from all probed protocols."""

    host: str
    open_ports: List[int]             = field(default_factory=list)

    # Identification
    make:    str = ''
    model:   str = ''
    firmware:str = ''
    serial:  str = ''
    uuid:    str = ''
    mac_hint:str = ''

    # Protocol data
    http_title:   str = ''
    http_server:  str = ''
    https_server: str = ''
    ipp_attrs:    Dict[str, str] = field(default_factory=dict)
    pjl_id:       str = ''
    snmp_descr:   str = ''
    snmp_langs:   List[str] = field(default_factory=list)
    wsd_info:     Dict[str, str] = field(default_factory=dict)
    lpd_queues:   List[str] = field(default_factory=list)
    smb_shares:   List[str] = field(default_factory=list)

    # Supported printer languages (CMD: field from device-id or SNMP)
    printer_langs: List[str] = field(default_factory=list)

    # Supported document formats (from IPP)
    doc_formats:   List[str] = field(default_factory=list)

    # Raw banners for ML and CVE matching
    raw_banners: Dict[str, str] = field(default_factory=dict)

    # Attack surface assessment
    attack_surface: Dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        """One-line human-readable summary."""
        model_str = f"{self.make} {self.model}".strip() or '?'
        fw_str    = f" fw={self.firmware}" if self.firmware else ''
        langs_str = ','.join(self.printer_langs) if self.printer_langs else 'unknown'
        ports_str = ','.join(str(p) for p in sorted(self.open_ports))
        return (f"{self.host} — {model_str}{fw_str} "
                f"| langs={langs_str} | ports={ports_str}")

    def as_dict(self) -> dict:
        """Return a flat dict suitable for JSON serialisation."""
        import dataclasses
        return dataclasses.asdict(self)


# ── Port scanner ──────────────────────────────────────────────────────────────

PRINTER_PORTS = {
    80:   'HTTP',
    443:  'HTTPS',
    515:  'LPD',
    631:  'IPP',
    9100: 'RAW',
    445:  'SMB',
    139:  'NetBIOS',
    161:  'SNMP',
    3702: 'WSD',
    5357: 'WSD-HTTP',
    9000: 'AltHTTP',
}


def scan_ports(host: str, timeout: float = 2.0) -> List[int]:
    """Return list of open TCP ports from the standard printer port set."""
    open_ports = []
    for port in PRINTER_PORTS:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            open_ports.append(port)
        except OSError:
            pass
    return open_ports


# ── Individual protocol grabbers ──────────────────────────────────────────────

def _grab_http(host: str, timeout: float) -> dict:
    result = {}
    for scheme in ('http', 'https'):
        port = 443 if scheme == 'https' else 80
        try:
            r = requests.get(
                f'{scheme}://{host}:{port}/',
                timeout=timeout, verify=False,
                allow_redirects=False,
            )
            server = r.headers.get('Server', '')
            title  = re.findall(r'<title[^>]*>(.*?)</title>', r.text, re.I | re.S)
            key = 'https' if scheme == 'https' else 'http'
            result[f'{key}_status'] = str(r.status_code)
            result[f'{key}_server'] = server
            result[f'{key}_title']  = (title[0].strip() if title else '')
            # Collect all response headers as potential fingerprint
            result[f'{key}_headers'] = dict(r.headers)
        except Exception as exc:
            result[f'{key}_error'] = str(exc)[:80]
    return result


def _grab_ipp(host: str, timeout: float) -> dict:
    """
    Send IPP 1.1 GET-PRINTER-ATTRIBUTES to the printer and parse the response.

    Tries HTTP:631 first, then HTTPS:631 (some printers require TLS).
    """

    def _build_ipp_request(printer_uri: str) -> bytes:
        def attr(tag: int, name: str, value: str) -> bytes:
            nb = name.encode()
            vb = value.encode()
            return (bytes([tag]) +
                    struct.pack('>H', len(nb)) + nb +
                    struct.pack('>H', len(vb)) + vb)

        body = b'\x01\x01'                      # IPP 1.1
        body += struct.pack('>H', 0x000B)        # Get-Printer-Attributes
        body += struct.pack('>I', 1)             # request-id
        body += b'\x01'                          # operation-attributes-tag
        body += attr(0x47, 'attributes-charset', 'utf-8')
        body += attr(0x48, 'attributes-natural-language', 'en')
        body += attr(0x45, 'printer-uri', printer_uri)
        body += attr(0x44, 'requested-attributes', 'all')
        body += b'\x03'                          # end-of-attributes
        return body

    result = {}
    candidates = [
        ('http',  631, '/ipp/'),
        ('http',  631, '/ipp/print'),
        ('https', 631, '/ipp/print'),
        ('https', 631, '/ipp/'),
    ]
    for scheme, port, path in candidates:
        try:
            uri  = f'ipp://{host}{path}'
            body = _build_ipp_request(uri)
            r = requests.post(
                f'{scheme}://{host}:{port}{path}',
                data=body,
                headers={'Content-type': 'application/ipp'},
                timeout=timeout, verify=False,
            )
            if r.status_code == 200 and len(r.content) > 8:
                raw = r.content.decode('latin-1', errors='replace')
                result['ipp_raw'] = raw[:2000]
                result['ipp_endpoint'] = f'{scheme}:{port}{path}'

                # Extract key attributes using regex on the decoded response
                for pattern, key in [
                    (r'MDL:([^;]+);', 'model'),
                    (r'MFG:([^;]+);', 'make'),
                    (r'CMD:([^;]+);', 'langs'),
                    (r'DES:([^;]+);', 'description'),
                    (r'CID:([^;]+);', 'color_id'),
                    (r'FID:([^;]+);', 'feature_id'),
                    (r'RID:([^;]+);', 'res_id'),
                ]:
                    m = re.search(pattern, raw)
                    if m:
                        result[f'ipp_{key}'] = m.group(1).strip()

                # Parse text attributes (e.g. printer-make-and-model)
                for attr_name in ['printer-make-and-model', 'printer-name',
                                   'printer-info', 'printer-location',
                                   'printer-firmware-version',
                                   'printer-device-id', 'printer-uuid',
                                   'printer-dns-sd-name', 'printer-state']:
                    idx = raw.find(attr_name)
                    if idx >= 0:
                        chunk = raw[idx:idx+200]
                        printable = ''.join(c if 32 <= ord(c) < 127 else '|' for c in chunk)
                        result[f'ipp_attr_{attr_name.replace("-","_")}'] = printable[:80]

                # Document formats — extract only valid MIME types from binary response
                fmts = re.findall(
                    r'(application/(?:postscript|pdf|pcl|vnd\.epson\.\w+|octet-stream)|'
                    r'image/(?:pwg-raster|jpeg|png|urf)|text/plain)',
                    raw, re.I,
                )
                # Filter to printable MIME types only (no binary artifacts)
                clean_fmts = [f for f in dict.fromkeys(fmts)
                              if all(32 <= ord(c) <= 127 for c in f) and len(f) < 60]
                if clean_fmts:
                    result['ipp_doc_formats'] = clean_fmts

                # IPP version
                result['ipp_version_raw'] = f'{r.content[0]}.{r.content[1]}'
                break
        except Exception as exc:
            _log.debug("IPP %s:%d%s failed: %s", scheme, port, path, exc)

    return result


def _grab_pjl(host: str, timeout: float) -> dict:
    """Send PJL INFO ID to port 9100 and capture the response."""
    result = {}
    try:
        s = socket.create_connection((host, 9100), timeout=timeout)
        s.settimeout(timeout)
        uel = b'\x1b%-12345X'
        s.sendall(uel + b'@PJL INFO ID\r\n' + uel)
        time.sleep(min(timeout, 2.0))
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 8192:
                    break
        except (socket.timeout, BlockingIOError):
            pass
        s.close()
        if data:
            text = data.decode('latin-1', errors='replace')
            result['pjl_response'] = text[:500]
            m = re.search(r'INFO ID\s*\r?\n(.+)', text)
            if m:
                result['pjl_id'] = m.group(1).strip()
    except Exception as exc:
        result['pjl_error'] = str(exc)[:60]
    return result


def _grab_lpd(host: str, timeout: float) -> dict:
    """Probe LPD port 515 for queue names and capabilities."""
    result = {}
    try:
        s = socket.create_connection((host, 515), timeout=timeout)
        s.settimeout(timeout)
        # LPD: receive any banner, then request queue status
        s.sendall(b'\x03default\n')   # receive queue state
        time.sleep(0.5)
        data = b''
        try:
            data = s.recv(1024)
        except socket.timeout:
            pass
        s.close()
        if data:
            text = data.decode('latin-1', errors='replace')
            result['lpd_response'] = text[:300]
            # Extract queue names from the response
            queues = re.findall(r'Printer:\s*(\S+)', text)
            if queues:
                result['lpd_queues'] = queues
    except Exception as exc:
        result['lpd_error'] = str(exc)[:60]
    return result


def _grab_wsd(host: str, timeout: float) -> dict:
    """Probe WSD (Web Services for Devices) endpoint for device metadata."""
    result = {}
    import uuid as _uuid
    soap = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">
  <s:Header>
    <a:To>http://{host}/WSD/DEVICE</a:To>
    <a:Action>http://schemas.xmlsoap.org/ws/2004/09/transfer/Get</a:Action>
    <a:MessageID>urn:uuid:{_uuid.uuid4()}</a:MessageID>
    <a:ReplyTo>
      <a:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</a:Address>
    </a:ReplyTo>
  </s:Header>
  <s:Body/>
</s:Envelope>"""
    for path in ('/WSD/DEVICE', '/wsd/device', '/WSD/PRINTER'):
        try:
            r = requests.post(
                f'http://{host}{path}', data=soap.encode(),
                headers={'Content-Type': 'application/soap+xml; charset=utf-8',
                         'SOAPAction': '""'},
                timeout=timeout,
            )
            if r.status_code == 200:
                text = r.text
                for tag in ['Manufacturer', 'ModelName', 'FriendlyName',
                             'FirmwareVersion', 'SerialNumber', 'PresentationUrl',
                             'XAddrs', 'Types']:
                    m = re.search(f'<[^>]*{tag}[^>]*>(.*?)</', text, re.I | re.S)
                    if m:
                        val = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:80]
                        result[f'wsd_{tag.lower()}'] = val
                result['wsd_raw'] = text[:500]
                break
        except Exception as exc:
            _log.debug("WSD %s failed: %s", path, exc)
    return result


def _grab_snmp(host: str, timeout: float) -> dict:
    """Query SNMP for device description and language support."""
    result = {}
    try:
        from pysnmp.hlapi import (
            getCmd, nextCmd, CommunityData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity, SnmpEngine,
        )
        engine    = SnmpEngine()
        community = CommunityData('public', mpModel=0)
        transport = UdpTransportTarget((host, 161), timeout=timeout, retries=0)
        context   = ContextData()

        oids = {
            '1.3.6.1.2.1.1.1.0':          'sys_descr',
            '1.3.6.1.2.1.1.5.0':          'sys_name',
            '1.3.6.1.2.1.25.3.2.1.3.1':   'hr_device_descr',
            '1.3.6.1.2.1.43.5.1.1.16.1':  'prt_console_display',
        }
        for oid, key in oids.items():
            for err_ind, err_stat, _, binds in getCmd(
                engine, community, transport, context,
                ObjectType(ObjectIdentity(oid)),
            ):
                if not err_ind and not err_stat and binds:
                    result[f'snmp_{key}'] = str(binds[0][1])[:200]

    except ImportError:
        result['snmp_error'] = 'pysnmp not installed'
    except Exception as exc:
        result['snmp_error'] = str(exc)[:80]
    return result


# ── Attack surface assessment ─────────────────────────────────────────────────

def _assess_attack_surface(fp: PrinterFingerprint) -> Dict[str, str]:
    """
    Derive the attack surface from the fingerprint.

    Returns a dict of {attack_vector: 'high'/'medium'/'low'/'not_applicable'}.
    """
    surface: Dict[str, str] = {}
    open_p = set(fp.open_ports)
    langs  = [l.upper() for l in fp.printer_langs]
    fmts   = [f.lower() for f in fp.doc_formats]

    # PJL attacks (requires port 9100 + PJL language)
    if 9100 in open_p and 'PJL' in langs:
        surface['pjl_info_disclosure']   = 'high'
        surface['pjl_path_traversal']    = 'high'
        surface['pjl_eeprom_access']     = 'medium'
        surface['pjl_factory_reset']     = 'medium'
        surface['pjl_dos_infinite_loop'] = 'medium'
        surface['pjl_print_job_sniff']   = 'low'
    elif 9100 in open_p:
        surface['raw_print_flooding']    = 'medium'
        surface['raw_dos']               = 'medium'

    # PostScript attacks
    if 'PS' in langs or 'POSTSCRIPT' in langs or 'BR-SCRIPT' in langs:
        surface['ps_code_execution']     = 'high'
        surface['ps_file_read']          = 'high'
        surface['ps_exfiltration']       = 'medium'
        surface['ps_dos_loop']           = 'medium'

    # IPP attacks
    if 631 in open_p:
        surface['ipp_job_manipulation']  = 'medium'
        surface['ipp_queue_listing']     = 'low'
        if 'application/postscript' in fmts:
            surface['ipp_ps_job_exec']   = 'high'
        if any('epson' in f for f in fmts):
            surface['ipp_escpr_job']     = 'low'   # send raw ESC/P-R print job

    # LPD attacks
    if 515 in open_p:
        surface['lpd_queue_manipulation']= 'medium'
        surface['lpd_dos']               = 'low'

    # Web interface attacks
    if 80 in open_p or 443 in open_p:
        surface['web_default_creds']     = 'medium'
        surface['web_path_traversal']    = 'medium'
        surface['web_info_disclosure']   = 'low'
        surface['web_csrf']              = 'low'

    # SMB attacks (rare on modern printers)
    if 445 in open_p:
        surface['smb_null_session']      = 'medium'
        surface['smb_share_access']      = 'low'

    # WSD attacks
    if 3702 in open_p or 5357 in open_p or 'WSD' in langs:
        surface['wsd_ssrf_probe']        = 'low'

    # Information disclosure (always available)
    surface['banner_info_leak']          = 'info'
    surface['snmp_public_community']     = 'info' if 161 in open_p else 'not_applicable'

    return surface


# ── Main entry point ──────────────────────────────────────────────────────────

def grab_all(
    host:    str,
    timeout: float = 5.0,
    verbose: bool  = False,
) -> PrinterFingerprint:
    """
    Probe *host* with every available protocol and return a PrinterFingerprint.

    Args:
        host:    Printer IP address or hostname.
        timeout: Per-connection timeout in seconds.
        verbose: Print progress to stdout.

    Returns:
        A fully populated PrinterFingerprint instance.
    """
    fp = PrinterFingerprint(host=host)

    if verbose:
        print(f"[*] Banner grabbing {host} ...")

    # 1. Port scan
    if verbose:
        print("    Scanning ports ...", end='', flush=True)
    fp.open_ports = scan_ports(host, timeout=timeout)
    if verbose:
        print(f" open: {fp.open_ports}")

    # 2. HTTP / HTTPS
    if 80 in fp.open_ports or 443 in fp.open_ports:
        if verbose:
            print("    Grabbing HTTP/HTTPS ...", end='', flush=True)
        http_data = _grab_http(host, timeout)
        fp.http_title   = http_data.get('http_title', '')
        fp.http_server  = http_data.get('http_server', '')
        fp.https_server = http_data.get('https_server', '')
        fp.raw_banners['http'] = str(http_data)
        if verbose:
            print(f" server={fp.http_server or fp.https_server}")

    # 3. IPP
    if 631 in fp.open_ports:
        if verbose:
            print("    Grabbing IPP ...", end='', flush=True)
        ipp_data = _grab_ipp(host, timeout)
        fp.ipp_attrs = ipp_data
        fp.raw_banners['ipp'] = str(ipp_data)
        # Extract identification from IPP
        if 'ipp_make' in ipp_data:
            fp.make = ipp_data['ipp_make']
        if 'ipp_model' in ipp_data:
            fp.model = ipp_data['ipp_model']
        if 'ipp_langs' in ipp_data:
            fp.printer_langs = [l.strip() for l in ipp_data['ipp_langs'].split(',')]
        if 'ipp_doc_formats' in ipp_data:
            fp.doc_formats = ipp_data['ipp_doc_formats']
        # Firmware from header attributes
        fw_val = ipp_data.get('ipp_attr_printer_firmware_version', '')
        if fw_val:
            fp.firmware = re.sub(r'[|.]+', '', fw_val).strip()[:30]
        if verbose:
            print(f" model={fp.model or '?'} langs={fp.printer_langs}")

    # 4. PJL (RAW / port 9100)
    if 9100 in fp.open_ports:
        if verbose:
            print("    Grabbing PJL ...", end='', flush=True)
        pjl_data = _grab_pjl(host, timeout)
        fp.pjl_id = pjl_data.get('pjl_id', '')
        fp.raw_banners['pjl'] = str(pjl_data)
        # If PJL responds, add PJL to langs if not already there
        if fp.pjl_id and 'PJL' not in fp.printer_langs:
            fp.printer_langs.append('PJL')
        if verbose:
            print(f" pjl_id={fp.pjl_id[:40] or 'none'!r}")

    # 5. LPD
    if 515 in fp.open_ports:
        if verbose:
            print("    Grabbing LPD ...", end='', flush=True)
        lpd_data = _grab_lpd(host, timeout)
        fp.lpd_queues = lpd_data.get('lpd_queues', [])
        fp.raw_banners['lpd'] = str(lpd_data)
        if verbose:
            print(f" queues={fp.lpd_queues}")

    # 6. WSD
    if 80 in fp.open_ports:
        if verbose:
            print("    Grabbing WSD ...", end='', flush=True)
        wsd_data = _grab_wsd(host, timeout)
        fp.wsd_info = wsd_data
        fp.raw_banners['wsd'] = str(wsd_data)
        # Fill model/make if not already set
        if not fp.make and wsd_data.get('wsd_manufacturer'):
            fp.make = wsd_data['wsd_manufacturer']
        if not fp.model and wsd_data.get('wsd_modelname'):
            fp.model = wsd_data['wsd_modelname']
        if verbose:
            print(f" model={wsd_data.get('wsd_modelname','?')}")

    # 7. SNMP (UDP — probe even if port 161 not in TCP list)
    if verbose:
        print("    Grabbing SNMP ...", end='', flush=True)
    snmp_data = _grab_snmp(host, timeout)
    fp.snmp_descr = snmp_data.get('snmp_sys_descr', snmp_data.get('snmp_hr_device_descr', ''))
    fp.raw_banners['snmp'] = str(snmp_data)
    if verbose:
        print(f" descr={fp.snmp_descr[:40] or 'none'!r}")

    # 8. Fallback: extract make/model from HTTP server header or SNMP
    if not fp.model:
        for src in (fp.http_server, fp.https_server, fp.snmp_descr):
            m = re.search(r'(EPSON|HP|Brother|Kyocera|Ricoh|Xerox|Canon|Lexmark)'
                          r'[\s_/-]*([\w\s-]{2,30})', src, re.I)
            if m:
                fp.make  = m.group(1).title()
                fp.model = m.group(2).strip()
                break

    # 9. Attack surface assessment
    fp.attack_surface = _assess_attack_surface(fp)

    if verbose:
        print(f"[+] Fingerprint: {fp.summary()}")
        high_vectors = [k for k, v in fp.attack_surface.items() if v == 'high']
        if high_vectors:
            print(f"[!] High-risk attack vectors: {', '.join(high_vectors)}")

    return fp


def print_fingerprint(fp: PrinterFingerprint) -> None:
    """Pretty-print a PrinterFingerprint to stdout."""
    print(f"\n{'='*65}")
    print(f"  PRINTER FINGERPRINT — {fp.host}")
    print(f"{'='*65}")
    print(f"  Make/Model : {fp.make} {fp.model}")
    print(f"  Firmware   : {fp.firmware or '?'}")
    print(f"  Serial     : {fp.serial or '?'}")
    print(f"  UUID       : {fp.uuid or '?'}")
    print(f"  Open ports : {fp.open_ports}")
    print(f"  Languages  : {', '.join(fp.printer_langs) or 'none detected'}")
    print(f"  Doc formats: {', '.join(fp.doc_formats) or 'none'}")
    print(f"  HTTP server: {fp.http_server or fp.https_server or '?'}")
    print(f"  SNMP descr : {fp.snmp_descr[:60] or '?'}")

    if fp.lpd_queues:
        print(f"  LPD queues : {fp.lpd_queues}")

    if fp.wsd_info.get('wsd_friendlyname'):
        print(f"  WSD name   : {fp.wsd_info['wsd_friendlyname']}")

    if fp.attack_surface:
        print(f"\n  {'Attack surface':30s} {'Risk'}")
        print(f"  {'-'*50}")
        for vec, risk in sorted(fp.attack_surface.items(), key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2, 'info': 3, 'not_applicable': 4}.get(x[1], 5), x[0])):
            color = {
                'high':          '\033[1;31m',
                'medium':        '\033[1;33m',
                'low':           '\033[1;34m',
                'info':          '\033[0;37m',
                'not_applicable':'\033[2;37m',
            }.get(risk, '')
            reset = '\033[0m'
            print(f"  {color}{vec:<35}{risk.upper():<12}{reset}")
    print()
