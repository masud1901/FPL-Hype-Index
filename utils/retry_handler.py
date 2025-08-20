"""
Retry handler utilities for making scrapers resilient to transient errors.
"""

import asyncio
import time
import random
from typing import Callable, Any, Optional, List, Dict, Type
from functools import wraps
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter_factor: float = 0.1
    retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                OSError,
                Exception  # Generic fallback
            ]


class RetryHandler:
    """Handler for retrying failed operations with exponential backoff"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        
    async def execute_with_retry(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Execute a function with retry logic"""
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                # If we get here, the function succeeded
                if attempt > 1:
                    logger.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception is retryable
                if not self._is_retryable_exception(e):
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise e
                
                # Log the failure
                logger.warning(
                    f"Attempt {attempt}/{self.config.max_attempts} failed for {func.__name__}: {e}"
                )
                
                # If this is the last attempt, don't wait
                if attempt == self.config.max_attempts:
                    break
                    
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                logger.info(f"Retrying {func.__name__} in {delay:.2f}s")
                
                await asyncio.sleep(delay)
        
        # If we get here, all attempts failed
        logger.error(
            f"Function {func.__name__} failed after {self.config.max_attempts} attempts. "
            f"Last exception: {last_exception}"
        )
        raise last_exception
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """Check if an exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Exponential backoff
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.config.jitter_factor * random.uniform(-1, 1)
        delay += jitter
        
        return max(delay, 0.1)  # Minimum 0.1 second delay


class RetryManager:
    """Manager for multiple retry handlers"""
    
    def __init__(self):
        self.handlers: Dict[str, RetryHandler] = {}
        
    def get_handler(self, name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """Get or create a retry handler for a specific operation"""
        if name not in self.handlers:
            if config is None:
                config = RetryConfig()
            self.handlers[name] = RetryHandler(config)
        return self.handlers[name]
        
    async def execute_with_retry(
        self, 
        name: str, 
        func: Callable, 
        *args, 
        config: Optional[RetryConfig] = None,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic using a named handler"""
        handler = self.get_handler(name, config)
        return await handler.execute_with_retry(func, *args, **kwargs)


# Global retry manager instance
retry_manager = RetryManager()


def retry_on_failure(
    name: str = "default", 
    config: Optional[RetryConfig] = None
):
    """Decorator to apply retry logic to functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            return await retry_manager.execute_with_retry(
                name, func, *args, config=config, **kwargs
            )
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions, we need to run them in an event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            return loop.run_until_complete(
                retry_manager.execute_with_retry(name, func, *args, config=config, **kwargs)
            )
            
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


# Predefined retry configurations for common scenarios
class RetryConfigs:
    """Predefined retry configurations for different scenarios"""
    
    # Conservative retry for critical operations
    CONSERVATIVE = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=2.0,
        jitter_factor=0.2
    )
    
    # Aggressive retry for non-critical operations
    AGGRESSIVE = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=30.0,
        exponential_base=1.5,
        jitter_factor=0.1
    )
    
    # Quick retry for fast operations
    QUICK = RetryConfig(
        max_attempts=2,
        base_delay=0.1,
        max_delay=5.0,
        exponential_base=2.0,
        jitter_factor=0.05
    )
    
    # Network-specific retry for HTTP requests
    NETWORK = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter_factor=0.1,
        retryable_exceptions=[
            ConnectionError,
            TimeoutError,
            OSError,
            Exception
        ]
    ) 