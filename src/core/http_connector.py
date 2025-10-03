#!/usr/bin/env python3
"""
HTTP Connector for PrinterReaper
Handles HTTP-based printer connections when port 9100 is not available
"""

import urllib.request
import urllib.error
import urllib.parse
import socket
import time
from typing import Optional, Dict, Any

class HTTPConnector:
    def __init__(self, target: str, timeout: int = 10):
        self.target = target
        self.timeout = timeout
        self.session = None
        self.base_url = None
        
    def connect(self) -> bool:
        """Establish HTTP connection to printer"""
        try:
            # Try common printer HTTP ports
            http_ports = [80, 8080, 631, 443]
            
            for port in http_ports:
                try:
                    if port == 443:
                        url = f"https://{self.target}:{port}/"
                    else:
                        url = f"http://{self.target}:{port}/"
                    
                    response = urllib.request.urlopen(url, timeout=self.timeout)
                    if response.getcode() == 200:
                        self.base_url = url
                        return True
                except Exception:
                    continue
                    
            return False
            
        except Exception:
            return False
    
    def send_command(self, command: str) -> str:
        """Send command via HTTP"""
        try:
            if not self.base_url:
                return ""
                
            # Encode command for HTTP transmission
            data = urllib.parse.urlencode({'command': command}).encode('utf-8')
            
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            response = urllib.request.urlopen(req, timeout=self.timeout)
            return response.read().decode('utf-8', errors='ignore')
            
        except Exception as e:
            return f"HTTP Error: {e}"
    
    def send_pjl(self, pjl_command: str) -> str:
        """Send PJL command via HTTP"""
        try:
            if not self.base_url:
                return ""
                
            # Create HTTP request with PJL command
            data = f"@PJL {pjl_command}\n".encode('utf-8')
            
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers={
                    'Content-Type': 'application/pjl',
                    'Content-Length': str(len(data))
                }
            )
            
            response = urllib.request.urlopen(req, timeout=self.timeout)
            return response.read().decode('utf-8', errors='ignore')
            
        except Exception as e:
            return f"PJL HTTP Error: {e}"
    
    def send_postscript(self, ps_command: str) -> str:
        """Send PostScript command via HTTP"""
        try:
            if not self.base_url:
                return ""
                
            # Create HTTP request with PostScript command
            data = f"%!PS-Adobe-3.0\n{ps_command}\n".encode('utf-8')
            
            req = urllib.request.Request(
                self.base_url,
                data=data,
                headers={
                    'Content-Type': 'application/postscript',
                    'Content-Length': str(len(data))
                }
            )
            
            response = urllib.request.urlopen(req, timeout=self.timeout)
            return response.read().decode('utf-8', errors='ignore')
            
        except Exception as e:
            return f"PostScript HTTP Error: {e}"
    
    def get_printer_info(self) -> Dict[str, Any]:
        """Get printer information via HTTP"""
        try:
            if not self.base_url:
                return {}
                
            # Try to get printer status page
            status_url = urllib.parse.urljoin(self.base_url, '/status')
            response = urllib.request.urlopen(status_url, timeout=self.timeout)
            
            if response.getcode() == 200:
                content = response.read().decode('utf-8', errors='ignore')
                return self._parse_printer_info(content)
                
            return {}
            
        except Exception:
            return {}
    
    def _parse_printer_info(self, content: str) -> Dict[str, Any]:
        """Parse printer information from HTTP response"""
        info = {}
        
        # Look for common printer info patterns
        import re
        
        # Model information
        model_match = re.search(r'Model[:\s]+([^\n\r]+)', content, re.IGNORECASE)
        if model_match:
            info['model'] = model_match.group(1).strip()
            
        # Firmware version
        firmware_match = re.search(r'Firmware[:\s]+([^\n\r]+)', content, re.IGNORECASE)
        if firmware_match:
            info['firmware'] = firmware_match.group(1).strip()
            
        # Serial number
        serial_match = re.search(r'Serial[:\s]+([^\n\r]+)', content, re.IGNORECASE)
        if serial_match:
            info['serial'] = serial_match.group(1).strip()
            
        return info
    
    def close(self):
        """Close HTTP connection"""
        # HTTP connections are stateless, so just clear the base URL
        self.base_url = None
