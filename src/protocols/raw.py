#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAW Protocol Support for PrinterReaper
======================================
Direct TCP/IP printing on port 9100 (AppSocket/JetDirect)

This is the default protocol used by PrinterReaper.
"""

import socket
import time

class RAWProtocol:
    """
    RAW protocol implementation (Port 9100)
    This is the most common protocol for network printers.
    """
    
    DEFAULT_PORT = 9100
    
    def __init__(self, host, port=None, timeout=30):
        self.host = host
        self.port = port or self.DEFAULT_PORT
        self.timeout = timeout
        self.sock = None

    def connect(self):
        """Establish RAW connection"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            return False

    def send(self, data):
        """Send data via RAW protocol"""
        if not self.sock:
            raise ConnectionError("Not connected")
        
        if isinstance(data, str):
            data = data.encode()
        
        return self.sock.sendall(data)

    def recv(self, size=4096):
        """Receive data via RAW protocol"""
        if not self.sock:
            raise ConnectionError("Not connected")
        
        return self.sock.recv(size)

    def close(self):
        """Close RAW connection"""
        if self.sock:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

