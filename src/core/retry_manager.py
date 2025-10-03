#!/usr/bin/env python3
"""
Retry Manager for PrinterReaper
Handles automatic retries for failed commands
"""

import time
import socket
from typing import Callable, Any, Optional
from utils.helper import output

class RetryManager:
    """Manages retry logic for commands"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_count = 0
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry"""
        retryable_errors = (
            socket.timeout,
            ConnectionResetError,
            BrokenPipeError,
            OSError
        )
        return isinstance(error, retryable_errors)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt (exponential backoff)"""
        return self.base_delay * (2 ** attempt)
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    self.retry_count = 0  # Reset on success
                    return result
            except Exception as e:
                last_error = e
                
                if not self.should_retry(e) or attempt >= self.max_retries:
                    break
                
                delay = self.get_delay(attempt)
                output().warning(f"Command failed (attempt {attempt + 1}/{self.max_retries + 1}), retrying in {delay:.1f}s...")
                time.sleep(delay)
                self.retry_count += 1
        
        # All retries failed
        if last_error:
            if isinstance(last_error, socket.timeout):
                output().errmsg("Command timed out after all retries")
            elif isinstance(last_error, (ConnectionResetError, BrokenPipeError)):
                output().errmsg("Connection lost after all retries")
            elif isinstance(last_error, OSError):
                output().errmsg("Network error after all retries")
            else:
                output().errmsg(f"Command failed after all retries: {str(last_error)}")
        
        return None
    
    def reset(self):
        """Reset retry counter"""
        self.retry_count = 0

def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for automatic retry on failure"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            retry_manager = RetryManager(max_retries, base_delay)
            return retry_manager.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator
