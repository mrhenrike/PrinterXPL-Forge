#!/usr/bin/env python3
"""
PrinterReaper v2.0 - Advanced Printer Penetration Testing Toolkit
Main entry point for PJL-focused security testing
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run main
if __name__ == "__main__":
    from main import main
    main()
