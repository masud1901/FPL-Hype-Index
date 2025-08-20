"""
Custom exceptions for scraper operations.
"""


class ScraperException(Exception):
    """Base exception for all scraper-related errors."""
    pass


class ScrapingError(ScraperException):
    """Raised when scraping fails."""
    pass


class ValidationError(ScraperException):
    """Raised when data validation fails."""
    pass


class ScraperConnectionError(ScraperException):
    """Raised when a scraper cannot connect to the data source."""
    pass


class ScraperTimeoutError(ScraperException):
    """Raised when a scraper request times out."""
    pass


class ScraperRateLimitError(ScraperException):
    """Raised when a scraper hits rate limits."""
    pass


class ScraperDataValidationError(ScraperException):
    """Raised when scraped data fails validation."""
    pass


class ScraperParsingError(ScraperException):
    """Raised when scraped data cannot be parsed."""
    pass


class ScraperAuthenticationError(ScraperException):
    """Raised when authentication fails for a data source."""
    pass


class ScraperNotFoundError(ScraperException):
    """Raised when the requested data is not found."""
    pass 