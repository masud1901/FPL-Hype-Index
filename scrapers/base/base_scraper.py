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
from utils.rate_limiter import rate_limit_manager, RateLimitConfig
from utils.retry_handler import retry_manager, RetryConfigs
from .exceptions import (
    ScraperException,
    ScraperConnectionError,
    ScraperTimeoutError,
    ScraperRateLimitError,
    ScraperDataValidationError,
)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, name: Optional[str] = None
    ):
        """Initialize the base scraper.

        Args:
            config: Configuration dictionary or None to use default config
            name: Name of the scraper (optional, will be derived from class name)
        """
        if name is None:
            name = self.__class__.__name__.lower().replace("scraper", "")

        self.name = name

        # Handle different config formats
        if config is None:
            self.config = config.scraper
        elif isinstance(config, dict):
            self.config = config
        else:
            self.config = config

        # Initialize logger
        from utils.logger import get_logger

        self.logger = get_logger(f"scraper.{name}")

        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0.0

        # Rate limiting and retry configuration
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1.0)
        self.max_retries = self.config.get("max_retries", 3)
        self.request_timeout = self.config.get("request_timeout", 30)
        
        # Initialize rate limiter and retry handler
        self.rate_limiter = rate_limit_manager.get_limiter(
            self.name, 
            RateLimitConfig(
                requests_per_minute=self.config.get("requests_per_minute", 60),
                requests_per_hour=self.config.get("requests_per_hour", 1000),
                cooldown_period=self.rate_limit_delay
            )
        )
        self.retry_handler = retry_manager.get_handler(
            self.name,
            RetryConfigs.NETWORK
        )

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
                headers={
                    "User-Agent": self.config.get(
                        "user_agent", "FPL-Data-Collection/1.0"
                    )
                },
            )
            self.logger.info("Scraper session initialized", scraper=self.name)

    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Scraper session closed", scraper=self.name)

    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        await self.rate_limiter.acquire(self.name)

    async def _make_request(
        self, url: str, method: str = "GET", **kwargs
    ) -> Dict[str, Any]:
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
        async def _execute_request():
            await self._rate_limit()
            
            self.logger.debug(
                f"Making {method} request to {url}",
                scraper=self.name,
            )

            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.logger.warning(
                        "Rate limited, waiting before retry",
                        scraper=self.name,
                        retry_after=retry_after,
                    )
                    await asyncio.sleep(retry_after)
                    raise ScraperRateLimitError(f"Rate limited by {url}")

                response.raise_for_status()

                # Try to parse as JSON first
                try:
                    data = await response.json()
                except:
                    # Fall back to text
                    data = await response.text()

                self.logger.debug(
                    "Request successful",
                    scraper=self.name,
                    status_code=response.status,
                    data_size=len(str(data)),
                )

                return data

        # Use the retry handler to execute the request
        return await self.retry_handler.execute_with_retry(_execute_request)

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

            self.logger.info("Scraping started", scraper=self.name)

            # Perform scraping
            data = await self.scrape()

            # Validate data
            if not self.validate_data(data):
                raise ScraperDataValidationError(
                    f"Data validation failed for {self.name}"
                )

            duration = time.time() - start_time
            data_count = len(data) if isinstance(data, (list, dict)) else 1

            self.logger.info(
                "Scraping completed successfully",
                scraper=self.name,
                data_count=data_count,
                duration_seconds=duration,
            )
            self.logger.info("Data validation passed", scraper=self.name)

            return data

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Scraping failed",
                scraper=self.name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        finally:
            await self.cleanup()

    def get_scraper_info(self) -> Dict[str, Any]:
        """Get information about the scraper.

        Returns:
            Dictionary with scraper information
        """
        return {
            "name": self.name,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "request_timeout": self.request_timeout,
        }
