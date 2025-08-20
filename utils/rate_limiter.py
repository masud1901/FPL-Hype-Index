"""
Rate limiting utilities for scrapers to prevent getting blocked by data sources.
"""

import time
import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    cooldown_period: float = 1.0  # seconds between requests
    jitter_factor: float = 0.1  # Add randomness to prevent synchronized requests


class RateLimiter:
    """Rate limiter for controlling request frequency"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times: Dict[str, list] = defaultdict(list)
        self.last_request_time: Dict[str, float] = defaultdict(float)
        
    async def acquire(self, source_name: str = "default") -> None:
        """Acquire permission to make a request"""
        current_time = time.time()
        
        # Clean old request times (older than 1 hour)
        self._cleanup_old_requests(source_name, current_time)
        
        # Check rate limits
        await self._check_minute_limit(source_name, current_time)
        await self._check_hour_limit(source_name, current_time)
        await self._check_burst_limit(source_name, current_time)
        
        # Apply cooldown with jitter
        await self._apply_cooldown(source_name, current_time)
        
        # Record this request
        self.request_times[source_name].append(current_time)
        self.last_request_time[source_name] = current_time
        
    def _cleanup_old_requests(self, source_name: str, current_time: float) -> None:
        """Remove request times older than 1 hour"""
        cutoff_time = current_time - 3600  # 1 hour
        self.request_times[source_name] = [
            req_time for req_time in self.request_times[source_name]
            if req_time > cutoff_time
        ]
        
    async def _check_minute_limit(self, source_name: str, current_time: float) -> None:
        """Check requests per minute limit"""
        minute_ago = current_time - 60
        recent_requests = [
            req_time for req_time in self.request_times[source_name]
            if req_time > minute_ago
        ]
        
        if len(recent_requests) >= self.config.requests_per_minute:
            wait_time = 60 - (current_time - recent_requests[0])
            logger.warning(f"Rate limit exceeded for {source_name}. Waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
    async def _check_hour_limit(self, source_name: str, current_time: float) -> None:
        """Check requests per hour limit"""
        hour_ago = current_time - 3600
        recent_requests = [
            req_time for req_time in self.request_times[source_name]
            if req_time > hour_ago
        ]
        
        if len(recent_requests) >= self.config.requests_per_hour:
            wait_time = 3600 - (current_time - recent_requests[0])
            logger.warning(f"Hourly rate limit exceeded for {source_name}. Waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
    async def _check_burst_limit(self, source_name: str, current_time: float) -> None:
        """Check burst limit (requests in short time window)"""
        burst_window = 5  # 5 seconds
        recent_requests = [
            req_time for req_time in self.request_times[source_name]
            if req_time > current_time - burst_window
        ]
        
        if len(recent_requests) >= self.config.burst_limit:
            wait_time = burst_window - (current_time - recent_requests[0])
            logger.warning(f"Burst limit exceeded for {source_name}. Waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
    async def _apply_cooldown(self, source_name: str, current_time: float) -> None:
        """Apply cooldown period between requests"""
        time_since_last = current_time - self.last_request_time[source_name]
        if time_since_last < self.config.cooldown_period:
            wait_time = self.config.cooldown_period - time_since_last
            
            # Add jitter to prevent synchronized requests
            jitter = wait_time * self.config.jitter_factor * (2 * (hash(source_name) % 100) / 100 - 1)
            wait_time += jitter
            
            await asyncio.sleep(wait_time)


class RateLimitManager:
    """Manager for multiple rate limiters"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        
    def get_limiter(self, source_name: str, config: Optional[RateLimitConfig] = None) -> RateLimiter:
        """Get or create a rate limiter for a specific source"""
        if source_name not in self.limiters:
            if config is None:
                config = RateLimitConfig()
            self.limiters[source_name] = RateLimiter(config)
        return self.limiters[source_name]
        
    async def acquire(self, source_name: str, config: Optional[RateLimitConfig] = None) -> None:
        """Acquire permission to make a request for a specific source"""
        limiter = self.get_limiter(source_name, config)
        await limiter.acquire(source_name)


# Global rate limit manager instance
rate_limit_manager = RateLimitManager()


def rate_limited(source_name: str, config: Optional[RateLimitConfig] = None):
    """Decorator to apply rate limiting to async functions"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            await rate_limit_manager.acquire(source_name, config)
            return await func(*args, **kwargs)
        return wrapper
    return decorator 