"""
Structured logging utility for the FPL Data Collection System.
"""
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import structlog
from config.settings import config


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if config.environment == "production" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: The logger name (usually __name__)
        
    Returns:
        A configured structured logger
    """
    return structlog.get_logger(name)


class ScraperLogger:
    """Specialized logger for scrapers with additional context."""
    
    def __init__(self, scraper_name: str):
        self.logger = get_logger(f"scraper.{scraper_name}")
        self.scraper_name = scraper_name
    
    def log_scrape_start(self, url: str, **kwargs) -> None:
        """Log the start of a scraping operation."""
        self.logger.info(
            "Scraping started",
            scraper=self.scraper_name,
            url=url,
            **kwargs
        )
    
    def log_scrape_success(self, data_count: int, duration: float, **kwargs) -> None:
        """Log successful scraping completion."""
        self.logger.info(
            "Scraping completed successfully",
            scraper=self.scraper_name,
            data_count=data_count,
            duration_seconds=duration,
            **kwargs
        )
    
    def log_scrape_error(self, error: Exception, url: str, **kwargs) -> None:
        """Log scraping errors."""
        self.logger.error(
            "Scraping failed",
            scraper=self.scraper_name,
            url=url,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )
    
    def log_data_validation(self, is_valid: bool, issues: Optional[list] = None, **kwargs) -> None:
        """Log data validation results."""
        self.logger.info(
            "Data validation completed",
            scraper=self.scraper_name,
            is_valid=is_valid,
            issues=issues or [],
            **kwargs
        )


class ProcessorLogger:
    """Specialized logger for data processors."""
    
    def __init__(self, processor_name: str):
        self.logger = get_logger(f"processor.{processor_name}")
        self.processor_name = processor_name
    
    def log_processing_start(self, data_count: int, source: str, **kwargs) -> None:
        """Log the start of data processing."""
        self.logger.info(
            "Data processing started",
            processor=self.processor_name,
            data_count=data_count,
            source=source,
            **kwargs
        )
    
    def log_processing_success(self, processed_count: int, duration: float, **kwargs) -> None:
        """Log successful processing completion."""
        self.logger.info(
            "Data processing completed successfully",
            processor=self.processor_name,
            processed_count=processed_count,
            duration_seconds=duration,
            **kwargs
        )
    
    def log_processing_error(self, error: Exception, **kwargs) -> None:
        """Log processing errors."""
        self.logger.error(
            "Data processing failed",
            processor=self.processor_name,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )


class StorageLogger:
    """Specialized logger for storage operations."""
    
    def __init__(self):
        self.logger = get_logger("storage")
    
    def log_save_start(self, table: str, record_count: int, **kwargs) -> None:
        """Log the start of a save operation."""
        self.logger.info(
            "Saving data to storage",
            table=table,
            record_count=record_count,
            **kwargs
        )
    
    def log_save_success(self, table: str, saved_count: int, duration: float, **kwargs) -> None:
        """Log successful save completion."""
        self.logger.info(
            "Data saved successfully",
            table=table,
            saved_count=saved_count,
            duration_seconds=duration,
            **kwargs
        )
    
    def log_save_error(self, error: Exception, table: str, **kwargs) -> None:
        """Log save errors."""
        self.logger.error(
            "Data save failed",
            table=table,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )


# Initialize logging when module is imported
setup_logging()

# Create default loggers
logger = get_logger(__name__) 