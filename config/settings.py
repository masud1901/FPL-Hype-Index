"""
Application configuration settings.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class ScraperConfig:
    """Configuration for scrapers and data sources."""

    fpl_api_url: str = "https://fantasy.premierleague.com/api/"
    understat_url: str = "https://understat.com/"
    fbref_url: str = "https://fbref.com/"
    transfermarkt_url: str = "https://www.transfermarkt.com/"
    whoscored_url: str = "https://www.whoscored.com/"
    football_data_url: str = "https://api.football-data.org/v4"

    # API Keys
    football_data_api_key: str = os.getenv("FOOTBALL_DATA_API_KEY", "")

    # Request settings
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    rate_limit_delay: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

    # User agent for web scraping
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "fpl_data")
    username: str = os.getenv("DB_USER", "fpl_user")
    password: str = os.getenv("DB_PASSWORD", "")

    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        """Generate async SQLAlchemy connection string."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class PredictionConfig:
    """Configuration for prediction engine."""

    # Model settings
    model_version: str = os.getenv("MODEL_VERSION", "3.0")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    
    # Caching settings
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    # Performance settings
    max_recommendations: int = int(os.getenv("MAX_RECOMMENDATIONS", "5"))
    backtest_lookback_seasons: int = int(os.getenv("BACKTEST_LOOKBACK_SEASONS", "2"))
    
    # Feature engineering settings
    feature_lookback_gameweeks: int = int(os.getenv("FEATURE_LOOKBACK_GAMEWEEKS", "6"))
    fixture_lookahead_gameweeks: int = int(os.getenv("FIXTURE_LOOKAHEAD_GAMEWEEKS", "5"))


@dataclass
class AppConfig:
    """Main application configuration."""

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Sub-configurations
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    prediction: PredictionConfig = field(default_factory=PredictionConfig)

    # Application settings
    timezone: str = "UTC"
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.environment == "production" and not self.database.password:
            raise ValueError(
                "Database password must be set via DB_PASSWORD environment variable"
            )


# Global configuration instance
config = AppConfig()
