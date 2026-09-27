#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACL Module for PrinterXPL-Forge
===================================
HP proprietary low-level protocol for remote firmware access and diagnostics.
Operates over RAW/JetDirect (port 9100) after PJL ENTER LANGUAGE=ACL.

Tested on: HP P2035n (CE462A).

SAFETY NOTES
------------
- Read-only commands (version, product, buildtime, fwinfo): safe at any time.
- Destructive commands (burnspiflash, burnflash, fixnvram, reset): require
  explicit confirmation AND the device model to be in the tested allowlist.
  Sending incorrect firmware WILL BRICK the device.
"""
from __future__ import annotations

import array
import binascii
import os
import socket
import struct
from typing import Optional

from core.printer import printer
from utils.helper import const as c
from utils.helper import log, output

# ── Safety allowlist ──────────────────────────────────────────────────────────
# Only allow destructive operations on explicitly tested models.
# Expand ONLY after successful lab validation on a specific unit.
_TESTED_MODELS_DESTRUCTIVE: frozenset = frozenset({
    "CE462A",  # HP LaserJet P2035n
    "CE461A",  # HP LaserJet P2035
})

# Maximum accepted firmware file size (16 MiB safety cap)
_MAX_FW_SIZE_BYTES: int = 16 * 1024 * 1024

# ACL protocol magic
_ACL_MAGIC: int = 0x00AC

# Minimal valid ACL response length (magic 2B + cmd 2B + result 2B + padding)
_MIN_RESPONSE_LEN: int = 6


def hp_checksum(data: bytes) -> int:
    """
    Compute HP ACL 32-bit ones-complement checksum of a byte string.

    The algorithm:
      - Reads the payload as big-endian 16-bit words.
      - If the payload has an odd number of bytes the final byte is added as
        the high byte of a zero-padded word.
      - Accumulates words into a 32-bit sum.
      - Folds carry bits and returns bitwise NOT masked to 32 bits.
    """
    words = array.array("H")
    even_len = (len(data) // 2) * 2
    words.frombytes(data[:even_len])
    words.byteswap()

    csum: int = 0
    for word in words:
        csum = (csum + word) & 0xFFFFFFFF

    # Handle trailing odd byte (high byte of final word, low byte = 0)
    if len(data) % 2:
        csum = (csum + (data[-1] << 8)) & 0xFFFFFFFF

    # Fold 32-bit carry into 16-bit result
    if csum >= 0x10000:
        csum = ((csum & 0xFFFF) + (csum >> 16)) & 0xFFFF

    return (~csum) & 0xFFFF


def _confirm_destructive(model_hint: str = "") -> bool:
    """
    Prompt the user to confirm a destructive operation.

    Also validates that the target model is in the tested allowlist if a
    model string is supplied.
    """
    if model_hint and model_hint.upper() not in _TESTED_MODELS_DESTRUCTIVE:
        output().warning(
            f"Model '{model_hint}' is NOT in the tested allowlist "
            f"({', '.join(sorted(_TESTED_MODELS_DESTRUCTIVE))}). "
            "Proceeding may brick the device."
        )
    print("!! This command is UNTESTED and may BRICK your device. !!")
    return input("Do you want to proceed? [y] ").strip().lower() == "y"


class acl(printer):
    """HP ACL low-level printer shell."""

    def __init__(self, args):
        super().__init__(args, skip_open=True)
        self.target = args.target
        self.prompt = f"{self.target}:acl> "
        self._model: str = ""  # set by do_product if called first

    # ── Connection helpers ────────────────────────────────────────────────────

    def _get_raw_socket(self) -> Optional[socket.socket]:
        """Return the underlying socket object, or None if unavailable."""
        conn = getattr(self, "conn", None)
        if conn is None:
            return None
        # Try common attribute names used by different backend implementations
        for attr in ("_sock", "sock", "_socket", "socket"):
            sock = getattr(conn, attr, None)
            if isinstance(sock, socket.socket):
                return sock
        return None

    def _raw_recv(self, n_bytes: int, timeout: float = 120.0) -> bytes:
        """
        Receive exactly n_bytes from the raw socket.

        Returns empty bytes on any error or if socket is unavailable.
        """
        if n_bytes <= 0:
            return b""
        sock = self._get_raw_socket()
        if sock is None:
            output().errmsg("Raw socket not accessible for extended receive.")
            return b""
        try:
            old_timeout = sock.gettimeout()
            sock.settimeout(timeout)
            data = b""
            while len(data) < n_bytes:
                chunk = sock.recv(n_bytes - len(data))
                if not chunk:
                    break
                data += chunk
            sock.settimeout(old_timeout)
            return data
        except Exception as exc:
            output().errmsg(f"Raw recv error: {exc}")
            return b""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def precmd(self, line: str) -> str:
        self.do_open(self.target, "init")
        self.send(c.UEL)
        self.send("@PJL ENTER LANGUAGE=ACL" + c.EOL)
        return super().precmd(line)

    def postcmd(self, stop: bool, line: str) -> bool:
        # Must send UEL to release the printer; otherwise it stays busy.
        self.send(c.UEL)
        self.do_close()
        return super().postcmd(stop, line)

    # ── Low-level command ─────────────────────────────────────────────────────

    def cmd(self, cmd_bytes: bytes, data: bytes = b"") -> bytes:
        """
        Send an ACL command and receive the fixed-size 16-byte header response.

        Returns the raw response bytes, or b'' on error.
        """
        assert len(cmd_bytes) == 0x10, "ACL command header must be exactly 16 bytes"
        payload = cmd_bytes + data
        log().write(self.logfile, binascii.hexlify(cmd_bytes).decode("ascii") + os.linesep)
        self.send(payload)

        sock = self._get_raw_socket()
        if sock is None:
            output().errmsg("Cannot access raw socket for ACL response.")
            return b""

        try:
            sock.settimeout(120.0)
            raw = sock.recv(0x10)
        except Exception as exc:
            output().errmsg(f"Failed to receive ACL response: {exc}")
            return b""

        return raw

    def _unpack_header(self, raw: bytes, expected_cmd: int) -> Optional[dict]:
        """
        Safely unpack the standard 16-byte ACL response header.

        Returns a dict with parsed fields, or None if the response is invalid.
        """
        if len(raw) < _MIN_RESPONSE_LEN:
            output().errmsg(
                f"Short ACL response: {len(raw)} bytes (expected >= {_MIN_RESPONSE_LEN})."
            )
            return None
        try:
            magic, rcmd, result = struct.unpack_from(">HHH", raw, 0)
        except struct.error as exc:
            output().errmsg(f"ACL response unpack error: {exc}")
            return None
        if magic != _ACL_MAGIC:
            output().errmsg(f"Unexpected ACL magic: 0x{magic:04X} (expected 0x{_ACL_MAGIC:04X})")
        return {"magic": magic, "cmd": rcmd, "result": result, "raw": raw}

    def _print_header(self, hdr: dict, label: str = "") -> None:
        if label:
            print(f"--- {label} ---")
        print(f"  magic : 0x{hdr['magic']:04X}  (expected 0x{_ACL_MAGIC:04X})")
        print(f"  cmd   : 0x{hdr['cmd']:04X}")
        print(f"  result: 0x{hdr['result']:04X}")

    # ── Read-only commands ─────────────────────────────────────────────────────

    def do_version(self, arg: str) -> None:
        """getDeviceVersion — read firmware version (read-only, safe)."""
        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0x0001, 0, 0, 0)
        raw = self.cmd(cmd)
        hdr = self._unpack_header(raw, 0x0001)
        if hdr is None:
            return
        self._print_header(hdr, "getDeviceVersion")
        if len(raw) >= 16:
            try:
                version_bytes = raw[6:14]
                print(f"  version: {repr(version_bytes.decode('ascii', errors='replace').rstrip())}")
            except Exception:
                pass

    def do_product(self, arg: str) -> None:
        """queryProductName — read product/model string (read-only, safe)."""
        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0x0006, 0, 0, 0)
        raw = self.cmd(cmd)
        hdr = self._unpack_header(raw, 0x0006)
        if hdr is None:
            return
        self._print_header(hdr, "queryProductName")
        if len(raw) >= 8:
            try:
                rlen = struct.unpack_from(">H", raw, 6)[0]
                print(f"  rlen: {rlen}")
                if rlen > 0:
                    data = self._raw_recv(rlen)
                    print(f"  data: {data!r}")
                    try:
                        model_str = data.decode("ascii", errors="replace").rstrip("\x00")
                        if model_str:
                            self._model = model_str
                    except Exception:
                        pass
            except struct.error:
                pass

    def do_buildtime(self, arg: str) -> None:
        """getBuildTime — read firmware build timestamp (read-only, safe)."""
        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0x0008, 0, 0, 0)
        raw = self.cmd(cmd)
        hdr = self._unpack_header(raw, 0x0008)
        if hdr is None:
            return
        self._print_header(hdr, "getBuildTime")
        if len(raw) >= 8:
            try:
                rlen = struct.unpack_from(">H", raw, 6)[0]
                print(f"  rlen: {rlen}")
                if rlen > 0:
                    data = self._raw_recv(rlen)
                    print(f"  data: {data!r}")
            except struct.error:
                pass

    def do_fwinfo(self, arg: str) -> None:
        """GetPrinterFwInfo — read full firmware info record (read-only, safe)."""
        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0x0013, 0, 0, 0)
        raw = self.cmd(cmd)
        hdr = self._unpack_header(raw, 0x0013)
        if hdr is None:
            return
        self._print_header(hdr, "GetPrinterFwInfo")
        if len(raw) >= 8:
            try:
                rlen = struct.unpack_from(">H", raw, 6)[0]
                print(f"  rlen: {rlen}")
                if rlen > 0:
                    data = self._raw_recv(rlen)
                    print(f"  data: {data!r}")
            except struct.error:
                pass

    # ── Destructive commands (require confirmation + model allowlist) ──────────

    def _load_fw_file(self, arg: str) -> Optional[bytes]:
        """Load and validate a firmware file. Returns bytes or None."""
        path = arg.strip()
        if not path:
            output().errmsg("Usage: burnspiflash <firmware_file>")
            return None
        try:
            size = os.path.getsize(path)
        except OSError as exc:
            output().errmsg(f"Cannot access file: {exc}")
            return None
        if size > _MAX_FW_SIZE_BYTES:
            output().errmsg(
                f"File too large: {size} bytes (limit {_MAX_FW_SIZE_BYTES})."
                " Refusing to proceed."
            )
            return None
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except OSError as exc:
            output().errmsg(f"File read error: {exc}")
            return None

    def do_burnspiflash(self, arg: str) -> None:
        """BurnSpiFlash — write SPI flash with firmware file.

        DESTRUCTIVE. Only safe on tested models. Incorrect firmware bricks device.
        """
        data = self._load_fw_file(arg)
        if data is None:
            return

        checksum = hp_checksum(data)
        data_with_cs = data + struct.pack(">L", checksum)
        print(f"  HP checksum: 0x{checksum:04X}")

        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0x0005, len(data_with_cs), 0, 0)
        if not _confirm_destructive(self._model):
            return
        raw = self.cmd(cmd, data=data_with_cs)
        hdr = self._unpack_header(raw, 0x0005)
        if hdr:
            self._print_header(hdr, "BurnSpiFlash result")

    def do_burnflash(self, arg: str) -> None:
        """BurnFlash — write main flash with firmware file.

        DESTRUCTIVE. Only safe on tested models. Incorrect firmware bricks device.
        """
        data = self._load_fw_file(arg)
        if data is None:
            return

        checksum = hp_checksum(data)
        print(f"  HP checksum: 0x{checksum:04X}")

        cmd = struct.pack(">HHHHLL", _ACL_MAGIC, 0x000F, 3, checksum, 0, len(data))
        if not _confirm_destructive(self._model):
            return
        raw = self.cmd(cmd, data=data)
        hdr = self._unpack_header(raw, 0x000F)
        if hdr:
            self._print_header(hdr, "BurnFlash result")

    def do_reset(self, arg: str) -> None:
        """reset — soft-reset the printer.

        DESTRUCTIVE (interrupts all active jobs).
        """
        if not _confirm_destructive(self._model):
            return
        cmd = struct.pack(">HHLLL", _ACL_MAGIC, 0xD1EE, 0, 0, 0)
        raw = self.cmd(cmd)
        hdr = self._unpack_header(raw, 0xD1EE)
        if hdr:
            self._print_header(hdr, "reset result")
            # No variable-length payload expected for reset

    def do_fixnvram(self, arg: str) -> None:
        """FixNvRam — repair NVRAM (P2035n / P2035 only).

        DESTRUCTIVE. Hardcoded for CE462A (P2035n) and CE461A (P2035).
        Sending this to any other model may corrupt device configuration.
        """
        model_up = (self._model or arg.strip()).upper()
        if model_up not in _TESTED_MODELS_DESTRUCTIVE:
            output().errmsg(
                f"fixnvram is hardcoded for {', '.join(sorted(_TESTED_MODELS_DESTRUCTIVE))}. "
                f"Detected model: '{model_up}'. Refusing to proceed."
            )
            return

        nvram_payloads = {
            "CE462A": b"CE462A\x00\x00\x00\x00\x00\x00\x00\x00\x00]\x17\x00\x00\x00\x00\x00\x02",
            "CE461A": b"CE461A\x00\x00\x00\x00\x00\x00\x00\x00\x00]\x17\x00\x00\x00\x00\x00\x01",
        }
        nvram = nvram_payloads.get(model_up)
        if nvram is None:
            output().errmsg("NVRAM payload unavailable for this model.")
            return

        cmd = struct.pack(">HHHHHHL", _ACL_MAGIC, 0xEC1D, 0, 0x013F, 0, len(nvram), 0)
        if not _confirm_destructive(model_up):
            return
        raw = self.cmd(cmd, data=nvram)
        hdr = self._unpack_header(raw, 0xEC1D)
        if hdr:
            self._print_header(hdr, "FixNvRam result")
