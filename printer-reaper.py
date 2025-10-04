#!/usr/bin/env python3
"""
PrinterReaper v2.4.2 - Complete Printer Penetration Testing Toolkit
==================================================================
Main entry point supporting:
- PJL (Printer Job Language) - 54 commands
- PostScript - 40 commands  
- PCL (Printer Command Language) - 15 commands
- 4 Network Protocols (RAW, LPD, IPP, SMB)
- 5 Attack Payloads

Total: 109 commands across 3 printer languages

Author: Andre Henrique (mrhenrike)
License: MIT
Website: https://github.com/mrhenrike/PrinterReaper
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run main
if __name__ == "__main__":
    from main import main
    main()
