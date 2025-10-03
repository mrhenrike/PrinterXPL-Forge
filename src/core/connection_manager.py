#!/usr/bin/env python3
"""
Connection Manager for PrinterReaper
Manages different connection methods and fallbacks
"""

import socket
import time
from typing import Optional, Dict, Any, List
from core.http_connector import HTTPConnector
from utils.helper import output

class ConnectionManager:
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.connection_method = None
        self.connector = None
        self.retry_count = 0
        self.max_retries = 3
        
    def connect(self) -> bool:
        """Try to establish connection using multiple methods"""
        methods = [
            ('port_9100', self._try_port_9100),
            ('http', self._try_http),
            ('ipp', self._try_ipp)
        ]
        
        for method_name, method_func in methods:
            output().info(f"Trying connection method: {method_name}")
            
            try:
                if method_func():
                    self.connection_method = method_name
                    output().green(f"Connected via {method_name}")
                    return True
            except Exception as e:
                output().yellow(f"Method {method_name} failed: {e}")
                continue
                
        output().red("All connection methods failed")
        return False
    
    def _try_port_9100(self) -> bool:
        """Try direct connection to port 9100"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            sock.close()
            return True
        except Exception:
            return False
    
    def _try_http(self) -> bool:
        """Try HTTP connection"""
        try:
            self.connector = HTTPConnector(self.target, self.timeout)
            return self.connector.connect()
        except Exception:
            return False
    
    def _try_ipp(self) -> bool:
        """Try IPP (Internet Printing Protocol) connection"""
        try:
            # IPP typically runs on port 631
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 631))
            sock.close()
            return True
        except Exception:
            return False
    
    def send_command(self, command: str) -> str:
        """Send command using appropriate method"""
        if not self.connector:
            return ""
            
        try:
            if self.connection_method == 'http':
                return self.connector.send_command(command)
            elif self.connection_method == 'port_9100':
                # Use direct socket connection
                return self._send_socket_command(command)
            else:
                return ""
        except Exception as e:
            output().error(f"Command failed: {e}")
            return ""
    
    def _send_socket_command(self, command: str) -> str:
        """Send command via direct socket"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            sock.send(command.encode())
            
            # Wait for response
            time.sleep(0.5)
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            return response
        except Exception as e:
            return f"Socket error: {e}"
    
    def get_printer_info(self) -> Dict[str, Any]:
        """Get printer information"""
        if self.connection_method == 'http' and self.connector:
            return self.connector.get_printer_info()
        return {}
    
    def close(self):
        """Close connection"""
        if self.connector:
            self.connector.close()
        self.connector = None
        self.connection_method = None
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.connection_method is not None and self.connector is not None
