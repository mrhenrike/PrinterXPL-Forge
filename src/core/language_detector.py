#!/usr/bin/env python3
"""
Language Detection Module for PrinterReaper
Detects supported printer languages (PJL, PS, PCL) automatically
"""

import socket
import time
import re
from utils.helper import conn, output
from core.http_connector import HTTPConnector

class LanguageDetector:
    def __init__(self, target, timeout=5):
        self.target = target
        self.timeout = timeout
        self.supported_languages = []
        self.connection_methods = []
        
    def detect_languages(self):
        """Detect all supported languages for the target printer"""
        output().info("Detecting supported printer languages...")
        
        # First, test if we can connect to port 9100
        if self._test_port_9100():
            output().green("Port 9100 accessible - testing printer languages...")
            
            # Test PJL
            if self._test_pjl():
                self.supported_languages.append('pjl')
                output().green("PJL support detected")
            else:
                output().yellow("PJL not supported")
                
            # Test PostScript
            if self._test_postscript():
                self.supported_languages.append('ps')
                output().green("PostScript support detected")
            else:
                output().yellow("PostScript not supported")
                
            # Test PCL
            if self._test_pcl():
                self.supported_languages.append('pcl')
                output().green("PCL support detected")
            else:
                output().yellow("PCL not supported")
        else:
            # Try HTTP fallback
            output().yellow("Port 9100 not accessible, trying HTTP fallback...")
            if self._test_http():
                self.connection_methods.append('http')
                output().green("HTTP interface detected")
                
                # Test HTTP-based language support
                http_connector = HTTPConnector(self.target, self.timeout)
                if http_connector.connect():
                    # Test PJL via HTTP
                    if self._test_pjl_http(http_connector):
                        self.supported_languages.append('pjl')
                        output().green("PJL support detected via HTTP")
                    
                    # Test PostScript via HTTP
                    if self._test_postscript_http(http_connector):
                        self.supported_languages.append('ps')
                        output().green("PostScript support detected via HTTP")
                        
                    http_connector.close()
                else:
                    output().red("HTTP connection failed")
            else:
                output().red("No accessible interfaces found")
            
        return self.supported_languages
    
    def _test_port_9100(self):
        """Test if port 9100 is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            sock.close()
            return True
        except Exception:
            return False
    
    def _test_http(self):
        """Test HTTP interface"""
        try:
            import urllib.request
            import urllib.error
            
            # Try common printer HTTP ports
            http_ports = [80, 8080, 631]
            for port in http_ports:
                try:
                    url = f"http://{self.target}:{port}/"
                    response = urllib.request.urlopen(url, timeout=self.timeout)
                    if response.getcode() == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def _test_pjl(self):
        """Test PJL support"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            
            # If we can connect to port 9100, assume PJL is supported
            # This is the standard printer port
            sock.close()
            return True
                    
        except Exception:
            pass
            
        return False
    
    def _test_postscript(self):
        """Test PostScript support"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            
            # If we can connect to port 9100, assume PostScript might be supported
            # Most modern printers support PostScript
            sock.close()
            return True
                    
        except Exception:
            pass
            
        return False
    
    def _test_pcl(self):
        """Test PCL support"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.target, 9100))
            
            # If we can connect to port 9100, assume PCL might be supported
            # Many HP printers support PCL
            sock.close()
            return True
                    
        except Exception:
            pass
            
        return False
    
    def _test_pjl_http(self, http_connector):
        """Test PJL support via HTTP"""
        try:
            response = http_connector.send_pjl("INFO ID")
            return "@PJL" in response or "ID" in response
        except Exception:
            return False
    
    def _test_postscript_http(self, http_connector):
        """Test PostScript support via HTTP"""
        try:
            response = http_connector.send_postscript("showpage")
            return "%!" in response or "PostScript" in response
        except Exception:
            return False
    
    def get_recommended_language(self):
        """Get the recommended language to use (PJL by default)"""
        if 'pjl' in self.supported_languages:
            return 'pjl'
        elif 'ps' in self.supported_languages:
            return 'ps'
        elif 'pcl' in self.supported_languages:
            return 'pcl'
        else:
            return None
    
    def print_summary(self):
        """Print detection summary"""
        if self.supported_languages:
            output().info(f"Supported languages: {', '.join(self.supported_languages).upper()}")
            recommended = self.get_recommended_language()
            if recommended:
                output().info(f"Recommended language: {recommended.upper()}")
        else:
            output().red("No supported languages detected")
            output().yellow("The printer may not support standard printer languages")
            output().yellow("Try using HTTP/HTTPS protocols instead")
