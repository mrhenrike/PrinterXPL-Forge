#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACL Module for PrinterXPL-Forge
===================================
HP specific protocol for low-level access / remote firmware upgrade.

See HP Firmware Upgrade Utility, FWUpdate.exe.

Tested on HP P2035n only.
"""
import array, binascii, os, socket, struct

from core.printer import printer
from utils.helper import log, output, const as c

def hp_checksum(data):
    words = array.array('H')
    words.frombytes(data[:(len(data)//2)*2])
    words.byteswap()
    csum = 0
    for word in words:
        csum = (csum + word) & 0xffffffff
    if len(data) % 1:
        csum += data[-1]
    if csum >= 0x10000:
        csum = (csum + (csum >> 16)) & 0xffff
    return (~csum) & 0xffffffff

def confirm():
    print('!! This command is UNTESTED and may BRICK your device. !!')
    return input('Do you want to proceed? [y] ') == 'y'

class acl(printer):

    def __init__(self, args):
        super().__init__(args, skip_open=True)
        self.target = args.target
        self.prompt = f"{self.target}:acl> "

    def precmd(self, line):
        self.do_open(self.target, "init")
        self.send(c.UEL)
        self.send('@PJL ENTER LANGUAGE=ACL' + c.EOL)
        return super().precmd(line)

    def cmd(self, cmd, data=b''):
        assert len(cmd) == 0x10
        payload = cmd + data
        log().write(self.logfile, binascii.hexlify(cmd).decode('ascii') + os.linesep)
        self.send(payload)
        try:
            if hasattr(self.conn, '_sock') and self.conn._sock:
                # firmware update on P2035n takes ~50 seconds
                self.conn._sock.settimeout(120.0)

            raw = self.conn._sock.recv(0x10)
        except Exception as e:
            output().errmsg(f"Failed to receive response: {str(e)}")
            return b""

        return raw

    def postcmd(self, stop, line):
        # must send this, otherwise connection keeps printer busy and becomes
        # unresponsive
        self.send(c.UEL)
        self.do_close()
        return super().postcmd(stop, line)

    def do_version(self, arg):
        """getDeviceVersion"""
        # for some products, command is 0x16
        cmd = struct.pack('>HHLLL', 0x00ac, 1, 0, 0, 0)
        result = self.cmd(cmd)
        magic, cmd, result, version, unk2 = struct.unpack('>HHH8sH', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x0001)')
        print(f'result: 0x{result:04x}')
        print(f'version: {repr(version.decode())}')
        print(f'unk2: 0x{unk2:04x}')

    def do_burnspiflash(self, arg):
        """BurnSpiFlash"""
        try:
            data = open(arg, 'rb').read()
        except Exception as e:
            output().errmsg(f"open failed: {e}")
            return

        checksum = hp_checksum(data)
        data += struct.pack('>L', checksum)

        cmd = struct.pack('>HHLLL', 0x00ac, 5, len(data), 0, 0)
        if not confirm(): return
        result = self.cmd(cmd, data=data)
        magic, cmd, result, unk1 = struct.unpack('>HHH10s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x0005)')
        print(f'result: 0x{result:04x}')
        print(f'unk1: {unk1}')

    def do_product(self, arg):
        """queryProductName"""
        cmd = struct.pack('>HHLLL', 0x00ac, 6, 0, 0, 0)
        result = self.cmd(cmd)
        magic, cmd, result, rlen, unk1 = struct.unpack('>HHHH8s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x0006)')
        print(f'result: 0x{result:04x}')
        print(f'rlen: {rlen}')
        print(f'unk1: {unk1}')

        data = self.conn._sock.recv(rlen)
        print(f'data: {data}')

    def do_buildtime(self, arg):
        cmd = struct.pack('>HHLLL', 0x00ac, 8, 0, 0, 0)
        result = self.cmd(cmd)
        magic, cmd, result, rlen, unk1 = struct.unpack('>HHHH8s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x0008)')
        print(f'result: 0x{result:04x}')
        print(f'rlen: {rlen}')
        print(f'unk1: {unk1}')

        data = self.conn._sock.recv(rlen)
        print(f'data: {data}')

    def do_burnflash(self, arg):
        """BurnFlash"""

        try:
            data = open(arg, 'rb').read()
        except Exception as e:
            output().errmsg(f"open failed: {e}")
            return

        checksum = hp_checksum(data) & 0xffff
        print(f'HP checksum: 0x{checksum:04x}')

        cmd = struct.pack('>HHHHLL', 0x00ac, 0xf, 3, checksum, 0, len(data))
        if not confirm(): return
        result = self.cmd(cmd, data=data)
        magic, cmd, result, unk1 = struct.unpack('>HHH10s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x000f)')
        print(f'result: 0x{result:04x}')
        print(f'unk1: {unk1}')

    def do_fwinfo(self, arg):
        """GetPrinterFwInfo"""
        cmd = struct.pack('>HHLLL', 0x00ac, 0x13, 0, 0, 0)
        result = self.cmd(cmd)
        magic, cmd, result, rlen, unk1 = struct.unpack('>HHHH8s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0x0013)')
        print(f'result: 0x{result:04x}')
        print(f'rlen: {rlen}')
        print(f'unk1: {unk1}')

        data = self.conn._sock.recv(rlen)
        print(f'data: {data}')

    def do_reset(self, arg):
        """reset"""
        cmd = struct.pack('>HHLLL', 0x00ac, 0xd1ee, 0, 0, 0)
        result = self.cmd(cmd)
        magic, cmd, result, unk1 = struct.unpack('>HHH10s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0xd1ee)')
        print(f'result: 0x{result:04x}')
        print(f'unk1: {unk1}')

        data = self.conn._sock.recv(rlen)
        print(f'data: {data}')

    def do_fixnvram(self, arg):
        """FixNvRam
        
        Hardcoded for P2035n (CE462A)!!!
        """
        nvram = b'CE462A\x00\x00\x00\x00\x00\x00\x00\x00\x00]\x17\x00\x00\x00\x00\x00\x02'
        # also: b'CE461A\x00\x00\x00\x00\x00\x00\x00\x00\x00]\x17\x00\x00\x00\x00\x00\x01'
        cmd = struct.pack('>HHHHHHL', 0x00ac, 0xec1d, 0, 0x13f, 0, len(nvram), 0)
        if not confirm(): return
        result = self.cmd(cmd, data=nvram)
        magic, cmd, result, unk1 = struct.unpack('>HHH10s', result)
        print(f'magic: 0x{magic:04x} (should be 0x00ac)')
        print(f'cmd: 0x{cmd:04x} (should be 0xec1d)')
        print(f'result: 0x{result:04x}')
        print(f'unk1: {unk1}')
