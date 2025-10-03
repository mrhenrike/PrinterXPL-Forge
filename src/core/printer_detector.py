#!/usr/bin/env python3
"""
Printer Compatibility Detector for PrinterReaper
Detects printer capabilities and filters available commands
"""

import re
from typing import Dict, List, Tuple

class PrinterDetector:
    def __init__(self):
        self.compatibility_matrix = {
            # Samsung printers
            "samsung": {
                "models": ["SP", "SCX", "ML", "CLP", "CLX"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # HP printers
            "hp": {
                "models": ["LaserJet", "DeskJet", "OfficeJet", "Color LaserJet"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Brother printers
            "brother": {
                "models": ["HL", "MFC", "DCP"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Canon printers
            "canon": {
                "models": ["imageCLASS", "iR", "LBP", "PIXMA"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Lexmark printers
            "lexmark": {
                "models": ["MS", "CS", "MX", "T"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Ricoh printers
            "ricoh": {
                "models": ["MP", "SP", "Aficio", "P"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Xerox printers
            "xerox": {
                "models": ["WorkCentre", "Phaser", "DocuPrint"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Konica Minolta printers
            "konica_minolta": {
                "models": ["bizhub", "magicolor"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Sharp printers
            "sharp": {
                "models": ["MX", "BP"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Toshiba printers
            "toshiba": {
                "models": ["e-STUDIO"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # OKI printers
            "oki": {
                "models": ["C", "B", "ES"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Pantum printers
            "pantum": {
                "models": ["P"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Dell printers
            "dell": {
                "models": ["B", "C", "E"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            },
            # Epson printers
            "epson": {
                "models": ["WorkForce", "Expression", "Stylus"],
                "capabilities": ["pjl", "ps", "pcl"],
                "supported_commands": [
                    "id", "version", "info", "status", "help", "exit",
                    "ls", "get", "put", "delete", "cat", "edit", "touch",
                    "pwd", "cd", "chvol", "traversal", "find", "mirror",
                    "df", "free", "pagecount", "lock", "unlock", "restart",
                    "reset", "disable", "destroy", "hang", "overlay", "cross",
                    "replace", "capture", "hold", "set", "known", "search",
                    "dicts", "resource", "dump", "config", "printenv", "env",
                    "display", "offline", "selftest", "nvram", "flood",
                    "product", "network", "wifi", "direct", "site", "load",
                    "permissions", "cve", "support", "convert", "fuzz"
                ]
            }
        }
    
    def detect_printer_type(self, device_info: str) -> Tuple[str, str, List[str]]:
        """Detect printer manufacturer, model, and capabilities"""
        device_info = device_info.lower()
        
        # Detect manufacturer
        manufacturer = "unknown"
        model = "unknown"
        capabilities = []
        
        for mfg, info in self.compatibility_matrix.items():
            for model_pattern in info["models"]:
                if model_pattern.lower() in device_info:
                    manufacturer = mfg
                    model = model_pattern
                    capabilities = info["capabilities"]
                    break
            if manufacturer != "unknown":
                break
        
        return manufacturer, model, capabilities
    
    def get_supported_commands(self, device_info: str) -> List[str]:
        """Get list of supported commands for the detected printer"""
        manufacturer, model, capabilities = self.detect_printer_type(device_info)
        
        # Base commands that work on all printers
        base_commands = [
            "id", "version", "info", "status", "help", "exit",
            "ls", "pwd", "cd", "chvol", "traversal", "find", "mirror",
            "df", "free", "pagecount", "printenv", "env",
            "display", "offline", "selftest", "flood",
            "product", "network", "wifi", "direct", "site", "load",
            "permissions", "cve", "support", "convert", "fuzz"
        ]
        
        # Commands that require specific capabilities
        advanced_commands = []
        
        if manufacturer == "samsung":
            # Samsung-specific commands
            advanced_commands = [
                "get", "put", "delete", "cat", "edit", "touch",
                "lock", "unlock", "restart", "reset", "disable", "destroy",
                "hang", "overlay", "cross", "replace", "capture", "hold",
                "set", "known", "search", "dicts", "resource", "dump", "config",
                "nvram", "append", "debug", "format", "loop", "open", "timeout",
                "close", "mkdir", "print", "discover"
            ]
        elif manufacturer == "hp":
            # HP-specific commands (including PML)
            advanced_commands = [
                "get", "put", "delete", "cat", "edit", "touch",
                "lock", "unlock", "restart", "reset", "disable", "destroy",
                "hang", "overlay", "cross", "replace", "capture", "hold",
                "set", "known", "search", "dicts", "resource", "dump", "config",
                "nvram", "append", "debug", "format", "loop", "open", "timeout",
                "close", "mkdir", "print", "discover"
            ]
        elif manufacturer in ["brother", "canon", "lexmark", "ricoh", "xerox", "konica_minolta", "sharp", "toshiba", "oki", "pantum", "dell", "epson"]:
            # Other manufacturers - limited advanced commands
            advanced_commands = [
                "get", "put", "delete", "cat", "edit", "touch",
                "lock", "unlock", "restart", "reset", "disable", "destroy",
                "hang", "overlay", "cross", "replace", "capture", "hold",
                "set", "known", "search", "dicts", "resource", "dump", "config",
                "nvram", "append", "debug", "format", "loop", "open", "timeout",
                "close", "mkdir", "print", "discover"
            ]
        else:
            # Unknown manufacturer - basic commands only
            advanced_commands = [
                "get", "put", "delete", "cat", "edit", "touch",
                "lock", "unlock", "restart", "reset", "disable", "destroy",
                "hang", "overlay", "cross", "replace", "capture", "hold",
                "set", "known", "search", "dicts", "resource", "dump", "config",
                "nvram", "append", "debug", "format", "loop", "open", "timeout",
                "close", "mkdir", "print", "discover"
            ]
        
        return base_commands + advanced_commands
    
    def get_compatibility_info(self, device_info: str) -> Dict:
        """Get detailed compatibility information"""
        manufacturer, model, capabilities = self.detect_printer_type(device_info)
        
        return {
            "manufacturer": manufacturer,
            "model": model,
            "capabilities": capabilities,
            "supported_commands": self.get_supported_commands(device_info),
            "compatibility_level": "Total" if manufacturer != "unknown" else "Partial"
        }
