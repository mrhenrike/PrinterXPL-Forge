#!/usr/bin/env python3
"""
Enhanced Logging Module for PrinterReaper
Provides structured logging with different levels and output formats
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional

class PrinterReaperLogger:
    def __init__(self, log_file: Optional[str] = None, debug: bool = False):
        self.log_file = log_file
        self.debug = debug
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger with appropriate handlers"""
        logger = logging.getLogger('PrinterReaper')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler if log file specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
            
        return logger
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
        
    def connection(self, target: str, port: int, status: str):
        """Log connection events"""
        self.info(f"Connection to {target}:{port} - {status}")
        
    def command(self, command: str, response: str = "", success: bool = True):
        """Log command execution"""
        status = "SUCCESS" if success else "FAILED"
        self.debug(f"Command: {command} - {status}")
        if response and self.debug:
            self.debug(f"Response: {response[:100]}...")
            
    def detection(self, target: str, languages: list, method: str = "port_9100"):
        """Log language detection results"""
        self.info(f"Language detection for {target} via {method}: {', '.join(languages)}")
        
    def timeout(self, target: str, command: str, timeout_value: int):
        """Log timeout events"""
        self.warning(f"Timeout on {target} for command '{command}' after {timeout_value}s")
        
    def retry(self, command: str, attempt: int, max_attempts: int):
        """Log retry attempts"""
        self.info(f"Retry {attempt}/{max_attempts} for command: {command}")

# Global logger instance
_logger_instance = None

def get_logger(log_file: Optional[str] = None, debug: bool = False) -> PrinterReaperLogger:
    """Get or create logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PrinterReaperLogger(log_file, debug)
    return _logger_instance

def setup_logging(log_file: Optional[str] = None, debug: bool = False):
    """Setup global logging configuration"""
    global _logger_instance
    _logger_instance = PrinterReaperLogger(log_file, debug)
    return _logger_instance
