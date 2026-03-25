#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper — Print Job Sender
=================================
Sends arbitrary files or raw data to a printer via:
  - RAW/JetDirect (TCP 9100) — fastest, supported by all network printers
  - IPP (TCP 631)            — standard, provides job tracking
  - LPD (TCP 515)            — legacy, RFC 1179

Supported input formats:
  - .ps / .eps   — PostScript (sent as-is)
  - .pcl         — PCL (sent as-is)
  - .pdf         — PDF (convert to PS if Ghostscript available, else raw)
  - .txt         — Plain text (wrapped in PJL/PS envelope)
  - .png/.jpg/.jpeg/.bmp/.gif — Images (convert to PS if Ghostscript available)
  - .doc/.docx   — Word (convert to PDF first if LibreOffice available)
  - any          — Sent as raw binary stream (RAW protocol)
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

from __future__ import annotations

import logging
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_log = logging.getLogger('PrinterReaper.print_job')

UEL = b'\x1b%-12345X'


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class PrintJobResult:
    """Result of a print job submission."""
    success:    bool
    protocol:   str
    host:       str
    port:       int
    file_path:  str
    file_size:  int
    job_id:     Optional[int] = None
    message:    str = ''
    error:      str = ''
    elapsed_ms: float = 0.0

    def __str__(self) -> str:
        status = 'OK' if self.success else 'FAILED'
        return (
            f"[{status}] {self.protocol.upper()} {self.host}:{self.port}  "
            f"file={self.file_path}  size={self.file_size}B  "
            f"elapsed={self.elapsed_ms:.0f}ms"
            + (f"  job_id={self.job_id}" if self.job_id else '')
            + (f"  msg={self.message}" if self.message else '')
            + (f"  err={self.error}" if self.error else '')
        )


# ── Format detection & conversion ──────────────────────────────────────────────

def _detect_format(path: str) -> str:
    """Return the detected format string based on file extension and magic bytes."""
    p = Path(path)
    ext = p.suffix.lower()
    ext_map = {
        '.ps':   'ps',
        '.eps':  'ps',
        '.pcl':  'pcl',
        '.prn':  'raw',
        '.pdf':  'pdf',
        '.txt':  'text',
        '.png':  'image',
        '.jpg':  'image',
        '.jpeg': 'image',
        '.bmp':  'image',
        '.gif':  'image',
        '.tiff': 'image',
        '.tif':  'image',
        '.doc':  'word',
        '.docx': 'word',
        '.odt':  'word',
        '.rtf':  'text',
    }
    fmt = ext_map.get(ext, 'raw')
    # Check magic bytes for PDF and PS regardless of extension
    try:
        with open(path, 'rb') as f:
            magic = f.read(4)
        if magic[:4] == b'%PDF':
            return 'pdf'
        if magic[:2] == b'%!':
            return 'ps'
        if magic[:2] == b'\x1b%':
            return 'pcl'
    except OSError:
        pass
    return fmt


def _text_to_ps(text: str, copies: int = 1) -> bytes:
    """Wrap plain text in a minimal PostScript document."""
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    ps_lines = []
    for i in range(copies):
        ps_lines.append('%!PS-Adobe-3.0')
        ps_lines.append('%%Pages: 1')
        ps_lines.append('%%EndComments')
        ps_lines.append('/Courier 10 selectfont')
        ps_lines.append('%%Page: 1 1')
        y = 750
        for line in lines[:72]:
            safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            ps_lines.append(f'72 {y} moveto')
            ps_lines.append(f'({safe}) show')
            y -= 14
            if y < 50:
                break
        ps_lines.append('showpage')
        ps_lines.append('%%Trailer')
        ps_lines.append('%%EOF')
    return '\n'.join(ps_lines).encode('latin-1', errors='replace')


def _convert_to_ps(path: str) -> Optional[bytes]:
    """
    Try to convert PDF/image/Word to PostScript using Ghostscript or LibreOffice.
    Returns None if conversion tools are not available.
    """
    fmt = _detect_format(path)
    gs = shutil.which('gs') or shutil.which('gswin64c') or shutil.which('gswin32c')
    lo = shutil.which('libreoffice') or shutil.which('soffice')

    if fmt == 'pdf' and gs:
        try:
            with tempfile.NamedTemporaryFile(suffix='.ps', delete=False) as tmp:
                tmp_path = tmp.name
            result = subprocess.run(
                [gs, '-q', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pswrite',
                 f'-sOutputFile={tmp_path}', path],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                data = Path(tmp_path).read_bytes()
                os.unlink(tmp_path)
                return data
        except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
            pass

    if fmt == 'image' and gs:
        try:
            with tempfile.NamedTemporaryFile(suffix='.ps', delete=False) as tmp:
                tmp_path = tmp.name
            result = subprocess.run(
                [gs, '-q', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pswrite',
                 '-sPAPERSIZE=a4', f'-sOutputFile={tmp_path}', path],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                data = Path(tmp_path).read_bytes()
                os.unlink(tmp_path)
                return data
        except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
            pass

    if fmt == 'word' and lo:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    [lo, '--headless', '--convert-to', 'pdf',
                     '--outdir', tmpdir, path],
                    capture_output=True, timeout=30
                )
                if result.returncode == 0:
                    pdf_path = Path(tmpdir) / (Path(path).stem + '.pdf')
                    if pdf_path.exists() and gs:
                        return _convert_to_ps(str(pdf_path))
                    elif pdf_path.exists():
                        return pdf_path.read_bytes()
        except (subprocess.TimeoutExpired, OSError, subprocess.SubprocessError):
            pass

    return None


def _prepare_payload(path: str, copies: int = 1) -> bytes:
    """
    Prepare the raw bytes to send to the printer.
    Attempts conversion when useful tools are available; falls back to raw.
    """
    fmt = _detect_format(path)
    _log.debug("Detected format: %s for %s", fmt, path)

    raw_data = Path(path).read_bytes()

    if fmt == 'ps':
        if copies > 1:
            # Wrap in PJL to repeat copies
            payload = UEL + f'@PJL SET COPIES={copies}\r\n'.encode() + UEL
            return payload + raw_data
        return raw_data

    if fmt == 'pcl':
        return raw_data

    if fmt == 'text':
        text = raw_data.decode('utf-8', errors='replace')
        return _text_to_ps(text, copies=copies)

    if fmt in ('pdf', 'image', 'word'):
        converted = _convert_to_ps(path)
        if converted:
            _log.info("Successfully converted %s to PostScript", fmt)
            return converted
        # Fall back to raw PDF/image — printer may or may not handle it
        _log.warning("No conversion tool found for %s; sending raw bytes", fmt)
        return raw_data

    return raw_data


# ── Protocol senders ─────────────────────────────────────────────────────────

def send_raw(host: str, port: int, data: bytes, timeout: float = 15.0) -> PrintJobResult:
    """
    Send data via RAW/JetDirect protocol (TCP port 9100).
    No handshake — just connect, write, close.
    """
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            total = len(data)
            sent  = 0
            while sent < total:
                chunk = s.send(data[sent:sent+4096])
                if chunk == 0:
                    raise OSError("Connection closed by remote")
                sent += chunk
        elapsed = (time.time() - t0) * 1000
        return PrintJobResult(
            success=True, protocol='raw', host=host, port=port,
            file_path='', file_size=total, elapsed_ms=elapsed,
            message=f"Sent {total} bytes via RAW"
        )
    except OSError as exc:
        elapsed = (time.time() - t0) * 1000
        return PrintJobResult(
            success=False, protocol='raw', host=host, port=port,
            file_path='', file_size=0, elapsed_ms=elapsed, error=str(exc)
        )


def send_ipp(host: str, port: int, data: bytes,
             job_name: str = 'PrinterReaper-Job',
             timeout: float = 20.0) -> PrintJobResult:
    """
    Send data via IPP (Internet Printing Protocol) over HTTP.
    Builds a minimal Print-Job IPP/1.1 request.
    """
    t0 = time.time()

    def _str(name: str, value: str, tag: int = 0x44) -> bytes:
        nb = name.encode(); vb = value.encode()
        return struct.pack('>BHH', tag, len(nb), len(nb)) + nb + struct.pack('>H', len(vb)) + vb

    printer_uri = f'ipp://{host}:{port}/ipp/print'
    ipp_attrs  = b'\x01'  # operation-attributes
    ipp_attrs += _str('attributes-charset', 'utf-8', 0x47)
    ipp_attrs += _str('attributes-natural-language', 'en-us', 0x48)
    ipp_attrs += _str('printer-uri', printer_uri, 0x45)
    ipp_attrs += _str('requesting-user-name', 'printerreaper', 0x42)
    ipp_attrs += _str('job-name', job_name, 0x42)
    ipp_attrs += _str('document-format', 'application/octet-stream', 0x49)
    ipp_attrs += b'\x03'  # end-of-attributes

    ipp_hdr   = struct.pack('>BBHI', 1, 1, 0x0002, 1)  # IPP/1.1 Print-Job req_id=1
    ipp_req   = ipp_hdr + ipp_attrs + data

    http_req  = (
        f"POST /ipp/print HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Content-Type: application/ipp\r\n"
        f"Content-Length: {len(ipp_req)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + ipp_req

    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(http_req)
            resp = b''
            s.settimeout(5)
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    resp += chunk
            except socket.timeout:
                pass

        elapsed = (time.time() - t0) * 1000
        # Parse IPP response job-id
        job_id = None
        sep = resp.find(b'\r\n\r\n')
        ipp_resp = resp[sep+4:] if sep != -1 else b''
        if len(ipp_resp) >= 4:
            status = struct.unpack('>H', ipp_resp[2:4])[0]
            success = (status == 0x0000)
        else:
            success = b'200' in resp[:100]

        return PrintJobResult(
            success=success, protocol='ipp', host=host, port=port,
            file_path='', file_size=len(data), job_id=job_id,
            elapsed_ms=elapsed,
            message=f"IPP Print-Job submitted ({len(data)} bytes)"
            if success else f"IPP error status {status:04X}"
        )
    except OSError as exc:
        elapsed = (time.time() - t0) * 1000
        return PrintJobResult(
            success=False, protocol='ipp', host=host, port=port,
            file_path='', file_size=0, elapsed_ms=elapsed, error=str(exc)
        )


def send_lpd(host: str, port: int, data: bytes,
             queue: str = 'lp', job_name: str = 'printerreaper',
             timeout: float = 20.0) -> PrintJobResult:
    """
    Send data via LPD (Line Printer Daemon, RFC 1179) on TCP port 515.
    """
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)

            # Command 0x02: Receive a printer job
            s.sendall(b'\x02' + queue.encode() + b'\n')
            ack = s.recv(1)
            if ack != b'\x00':
                raise OSError(f"LPD NAK on receive-job: {ack!r}")

            # Sub-command 0x02: Receive control file
            ctrl = (
                f"H{host}\n"
                f"P{job_name}\n"
                f"J{job_name}\n"
                f"ldfA001{host}\n"
                f"N{job_name}\n"
            ).encode()
            ctrl_name = f'cfA001{host[:15]}'
            s.sendall(f'\x02{len(ctrl)} {ctrl_name}\n'.encode())
            ack = s.recv(1)
            if ack != b'\x00':
                raise OSError(f"LPD NAK on control file: {ack!r}")
            s.sendall(ctrl + b'\x00')
            ack = s.recv(1)

            # Sub-command 0x03: Receive data file
            data_name = f'dfA001{host[:15]}'
            s.sendall(f'\x03{len(data)} {data_name}\n'.encode())
            ack = s.recv(1)
            if ack != b'\x00':
                raise OSError(f"LPD NAK on data file: {ack!r}")
            s.sendall(data + b'\x00')
            ack = s.recv(1)

        elapsed = (time.time() - t0) * 1000
        return PrintJobResult(
            success=True, protocol='lpd', host=host, port=port,
            file_path='', file_size=len(data), elapsed_ms=elapsed,
            message=f"LPD job submitted on queue '{queue}' ({len(data)} bytes)"
        )
    except OSError as exc:
        elapsed = (time.time() - t0) * 1000
        return PrintJobResult(
            success=False, protocol='lpd', host=host, port=port,
            file_path='', file_size=0, elapsed_ms=elapsed, error=str(exc)
        )


# ── Public API ────────────────────────────────────────────────────────────────

def send_print_job(
    host:     str,
    path:     str,
    protocol: str  = 'raw',
    port:     int  = 0,
    copies:   int  = 1,
    queue:    str  = 'lp',
    timeout:  float = 20.0,
) -> PrintJobResult:
    """
    High-level function: prepare the file and send it to the printer.

    Args:
        host:     Target IP or hostname.
        path:     Path to file to print (absolute or relative).
        protocol: 'raw' (port 9100), 'ipp' (port 631), or 'lpd' (port 515).
        port:     Override default port. 0 = use protocol default.
        copies:   Number of copies.
        queue:    LPD queue name (only used with protocol='lpd').
        timeout:  Socket timeout in seconds.

    Returns:
        PrintJobResult with success flag, message, and timing.
    """
    proto = protocol.lower().strip()
    default_ports = {'raw': 9100, 'ipp': 631, 'lpd': 515}
    actual_port = port or default_ports.get(proto, 9100)

    p = Path(path)
    if not p.exists():
        return PrintJobResult(
            success=False, protocol=proto, host=host, port=actual_port,
            file_path=path, file_size=0,
            error=f"File not found: {path}"
        )

    _log.info("Preparing print job: %s → %s:%d via %s", path, host, actual_port, proto)
    try:
        payload = _prepare_payload(str(p), copies=copies)
    except Exception as exc:
        return PrintJobResult(
            success=False, protocol=proto, host=host, port=actual_port,
            file_path=path, file_size=0, error=f"Payload preparation failed: {exc}"
        )

    result: PrintJobResult
    if proto == 'raw':
        result = send_raw(host, actual_port, payload, timeout=timeout)
    elif proto == 'ipp':
        result = send_ipp(host, actual_port, payload, job_name=p.name, timeout=timeout)
    elif proto == 'lpd':
        result = send_lpd(host, actual_port, payload, queue=queue,
                          job_name=p.stem, timeout=timeout)
    else:
        return PrintJobResult(
            success=False, protocol=proto, host=host, port=actual_port,
            file_path=path, file_size=0, error=f"Unknown protocol: {proto}"
        )

    result.file_path = path
    result.file_size = len(payload)
    return result
