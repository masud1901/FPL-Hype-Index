"""
Abstract base class for all scrapers.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import aiohttp
from config.settings import config
from utils.logger import ScraperLogger
from .exceptions import (
    ScraperException, ScraperConnectionError, ScraperTimeoutError,
    ScraperRateLimitError, ScraperDataValidationError
)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, name: str, config_overrides: Optional[Dict[str, Any]] = None):
        """Initialize the base scraper.
        
        Args:
            name: Name of the scraper
            config_overrides: Optional configuration overrides
        """
        self.name = name
        self.logger = ScraperLogger(name)
        self.config = config.scraper
        
        # Override config if provided
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0
        
        # Rate limiting
        self.rate_limit_delay = self.config.rate_limit_delay
        self.max_retries = self.config.max_retries
        self.request_timeout = self.config.request_timeout
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the scraper session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': self.config.user_agent}
            )
            self.logger.logger.info("Scraper session initialized", scraper=self.name)
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.logger.info("Scraper session closed", scraper=self.name)
    
    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic and rate limiting.
        
        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data
            
        Raises:
            ScraperConnectionError: If connection fails
            ScraperTimeoutError: If request times out
            ScraperRateLimitError: If rate limited
        """
        await self._rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.logger.debug(
                    f"Making {method} request to {url}",
                    scraper=self.name,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1
                )
                
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        self.logger.logger.warning(
                            "Rate limited, waiting before retry",
                            scraper=self.name,
                            retry_after=retry_after
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    
                    # Try to parse as JSON first
                    try:
                        data = await response.json()
                    except:
                        # Fall back to text
                        data = await response.text()
                    
                    self.logger.logger.debug(
                        "Request successful",
                        scraper=self.name,
                        status_code=response.status,
                        data_size=len(str(data))
                    )
                    
                    return data
                    
            except asyncio.TimeoutError:
                if attempt == self.max_retries:
                    raise ScraperTimeoutError(f"Request to {url} timed out after {self.request_timeout}s")
                self.logger.logger.warning(
                    "Request timed out, retrying",
                    scraper=self.name,
                    attempt=attempt + 1
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except aiohttp.ClientError as e:
                if attempt == self.max_retries:
                    raise ScraperConnectionError(f"Failed to connect to {url}: {e}")
                self.logger.logger.warning(
                    "Request failed, retrying",
                    scraper=self.name,
                    attempt=attempt + 1,
                    error=str(e)
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise ScraperConnectionError(f"Failed to make request to {url} after {self.max_retries + 1} attempts")
    
    @abstractmethod
    async def scrape(self) -> Dict[str, Any]:
        """Main scraping method to be implemented by each scraper.
        
        Returns:
            Scraped data in a standardized format
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    async def run(self) -> Dict[str, Any]:
        """Execute scraper with error handling and logging.
        
        Returns:
            Scraped data if successful
            
        Raises:
            ScraperException: If scraping fails
        """
        start_time = time.time()
        
        try:
            await self.initialize()
            
            self.logger.log_scrape_start(f"{self.name} scraper")
            
            # Perform scraping
            data = await self.scrape()
            
            # Validate data
            if not self.validate_data(data):
                raise ScraperDataValidationError(f"Data validation failed for {self.name}")
            
            duration = time.time() - start_time
            data_count = len(data) if isinstance(data, (list, dict)) else 1
            
            self.logger.log_scrape_success(data_count, duration)
            self.logger.log_data_validation(True)
            
            return data
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_scrape_error(e, f"{self.name} scraper")
            raise
            
        finally:
            await self.cleanup()
    
    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the scraper.
        
        Returns:
            Dictionary with scraper information
        """
        return {
            'name': self.name,
            'rate_limit_delay': self.rate_limit_delay,
            'max_retries': self.max_retries,
            'request_timeout': self.request_timeout
        } 