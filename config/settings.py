"""
Application configuration settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration (PostgreSQL - Main Storage)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "fpl_data")
    DB_USER: str = os.getenv("DB_USER", "fpl_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "fpl_password")

    # Redis Configuration (Caching Layer)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_VERSION: str = "v1"

    # Prediction Engine Configuration
    PREDICTION_CACHE_TTL: int = int(os.getenv("PREDICTION_CACHE_TTL", "3600"))  # 1 hour
    TRANSFER_CACHE_TTL: int = int(os.getenv("TRANSFER_CACHE_TTL", "1800"))  # 30 minutes
    BACKTEST_CACHE_TTL: int = int(os.getenv("BACKTEST_CACHE_TTL", "7200"))  # 2 hours

    # Scraper Configuration
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "30"))
    SCRAPER_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    SCRAPER_RATE_LIMIT: float = float(os.getenv("SCRAPER_RATE_LIMIT", "1.0"))

    # FPL API Configuration
    FPL_API_BASE_URL: str = "https://fantasy.premierleague.com/api/"
    FPL_API_TIMEOUT: int = int(os.getenv("FPL_API_TIMEOUT", "30"))

    # Data Collection Configuration
    DATA_COLLECTION_INTERVAL: int = int(
        os.getenv("DATA_COLLECTION_INTERVAL", "3600")
    )  # 1 hour
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "365"))

    # Performance Configuration
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))

    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        return self.REDIS_URL

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
