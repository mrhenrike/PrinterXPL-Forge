#!/usr/bin/env python3
"""
Error Handler for PrinterReaper
Provides robust error handling and user-friendly error messages
"""

import functools
import time
import socket
from typing import Any, Callable, Optional
from utils.helper import output

class PrinterReaperError(Exception):
    """Base exception for PrinterReaper errors"""
    pass

class ConnectionError(PrinterReaperError):
    """Connection-related errors"""
    pass

class TimeoutError(PrinterReaperError):
    """Timeout-related errors"""
    pass

class CommandError(PrinterReaperError):
    """Command execution errors"""
    pass

def handle_errors(max_retries: int = 3, timeout: int = 10, silent: bool = False):
    """
    Decorator to handle common errors gracefully
    
    Args:
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds
        silent: If True, suppress error messages
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except socket.timeout as e:
                    last_error = TimeoutError(f"Connection timeout after {timeout}s")
                    if not silent and attempt < max_retries:
                        output().warning(f"Timeout on attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(1)
                    elif not silent:
                        output().errmsg("Command timed out - printer may be busy or unresponsive")
                        
                except ConnectionResetError as e:
                    last_error = ConnectionError("Connection reset by printer")
                    if not silent and attempt < max_retries:
                        output().warning(f"Connection reset on attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(2)
                    elif not silent:
                        output().errmsg("Connection lost - printer may have disconnected")
                        
                except BrokenPipeError as e:
                    last_error = ConnectionError("Broken pipe - connection lost")
                    if not silent and attempt < max_retries:
                        output().warning(f"Broken pipe on attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(2)
                    elif not silent:
                        output().errmsg("Connection broken - printer may be offline")
                        
                except OSError as e:
                    last_error = ConnectionError(f"Network error: {e}")
                    if not silent and attempt < max_retries:
                        output().warning(f"Network error on attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(1)
                    elif not silent:
                        output().errmsg("Network error - check connection")
                        
                except Exception as e:
                    last_error = CommandError(f"Unexpected error: {e}")
                    if not silent:
                        output().errmsg(f"Command failed: {str(e)}")
                    break
            
            # If we get here, all retries failed
            if not silent and last_error:
                output().errmsg(f"Command failed after {max_retries + 1} attempts")
            
            return None
            
        return wrapper
    return decorator

def safe_command(func: Callable) -> Callable:
    """
    Decorator for safe command execution with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error but don't show traceback to user
            output().errmsg(f"Command failed: {str(e)}")
            return None
    return wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        output().warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        output().errmsg(f"All {max_retries + 1} attempts failed")
                        break
            
            return None
        return wrapper
    return decorator

class ErrorHandler:
    """Centralized error handling for PrinterReaper"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.error_count = 0
        self.last_error = None
    
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """
        Handle an error and return True if it should be retried
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        self.error_count += 1
        self.last_error = error
        
        if isinstance(error, socket.timeout):
            if self.verbose:
                output().warning(f"Timeout in {context}")
            return True
            
        elif isinstance(error, ConnectionResetError):
            if self.verbose:
                output().warning(f"Connection reset in {context}")
            return True
            
        elif isinstance(error, BrokenPipeError):
            if self.verbose:
                output().warning(f"Broken pipe in {context}")
            return True
            
        elif isinstance(error, OSError):
            if self.verbose:
                output().warning(f"Network error in {context}: {error}")
            return True
            
        else:
            if self.verbose:
                output().errmsg(f"Unexpected error in {context}: {error}")
            return False
    
    def should_retry(self, error: Exception) -> bool:
        """Check if an error should trigger a retry"""
        return isinstance(error, (socket.timeout, ConnectionResetError, BrokenPipeError, OSError))
    
    def get_user_friendly_message(self, error: Exception) -> str:
        """Get a user-friendly error message"""
        if isinstance(error, socket.timeout):
            return "Command timed out - printer may be busy"
        elif isinstance(error, ConnectionResetError):
            return "Connection lost - printer may have disconnected"
        elif isinstance(error, BrokenPipeError):
            return "Connection broken - printer may be offline"
        elif isinstance(error, OSError):
            return "Network error - check connection"
        else:
            return f"Command failed: {str(error)}"
    
    def reset(self):
        """Reset error counter"""
        self.error_count = 0
        self.last_error = None
