"""
Redis Caching Utility

This module provides Redis-based caching functionality for the FPL prediction engine,
allowing expensive computations to be cached and reused.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from functools import wraps

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based caching utility for the FPL prediction engine.

    This class provides methods to cache and retrieve data from Redis,
    with support for automatic serialization/deserialization and TTL management.
    """

    def __init__(
        self, redis_url: str = "redis://localhost:6379", default_ttl: int = 86400
    ):
        """
        Initialize Redis cache connection.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Establish connection to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Successfully connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        # Create a hash of the arguments
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_hash = hashlib.md5(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()
        return f"fpl:{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"Error setting cache value: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Error deleting from cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Error checking cache existence: {e}")
            return False

    def get_or_set(
        self, key: str, value_func: callable, ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it if not found.

        Args:
            key: Cache key
            value_func: Function to compute value if not cached
            ttl: Time-to-live in seconds

        Returns:
            Cached or computed value
        """
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        # Compute value if not in cache
        logger.debug(f"Cache miss for key: {key}, computing value")
        computed_value = value_func()

        # Cache the computed value
        self.set(key, computed_value, ttl)

        return computed_value

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "fpl:player_scores:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Error invalidating cache pattern: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        # Initialize with settings from environment
        from config.settings import get_settings

        settings = get_settings()
        _cache_instance = RedisCache(redis_url=settings.redis_url)
    return _cache_instance


def cache_result(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results.

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            key = cache._generate_key(prefix, *args, **kwargs)

            def compute_value():
                return func(*args, **kwargs)

            return cache.get_or_set(key, compute_value, ttl)

        return wrapper

    return decorator


# ============================================================================
# PREDICTION-SPECIFIC CACHING FUNCTIONS
# ============================================================================


def cache_player_score(
    player_id: str, score_data: Dict[str, Any], ttl: int = 3600
) -> bool:
    """
    Cache player score data.

    Args:
        player_id: Player ID
        score_data: Score data to cache
        ttl: Time-to-live in seconds

    Returns:
        True if successful, False otherwise
    """
    cache = get_cache()
    key = f"fpl:player_score:{player_id}"
    return cache.set(key, score_data, ttl)


def get_cached_player_score(player_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached player score data.

    Args:
        player_id: Player ID

    Returns:
        Cached score data or None
    """
    cache = get_cache()
    key = f"fpl:player_score:{player_id}"
    return cache.get(key)


def cache_transfer_recommendations(
    squad_hash: str, recommendations: List[Dict[str, Any]], ttl: int = 1800
) -> bool:
    """
    Cache transfer recommendations.

    Args:
        squad_hash: Hash of current squad
        recommendations: Transfer recommendations to cache
        ttl: Time-to-live in seconds (30 minutes)

    Returns:
        True if successful, False otherwise
    """
    cache = get_cache()
    key = f"fpl:transfer_recommendations:{squad_hash}"
    return cache.set(key, recommendations, ttl)


def get_cached_transfer_recommendations(
    squad_hash: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get cached transfer recommendations.

    Args:
        squad_hash: Hash of current squad

    Returns:
        Cached recommendations or None
    """
    cache = get_cache()
    key = f"fpl:transfer_recommendations:{squad_hash}"
    return cache.get(key)


def cache_backtest_result(
    test_id: str, result_data: Dict[str, Any], ttl: int = 7200
) -> bool:
    """
    Cache backtest result.

    Args:
        test_id: Unique test identifier
        result_data: Backtest result data
        ttl: Time-to-live in seconds (2 hours)

    Returns:
        True if successful, False otherwise
    """
    cache = get_cache()
    key = f"fpl:backtest_result:{test_id}"
    return cache.set(key, result_data, ttl)


def get_cached_backtest_result(test_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached backtest result.

    Args:
        test_id: Unique test identifier

    Returns:
        Cached result data or None
    """
    cache = get_cache()
    key = f"fpl:backtest_result:{test_id}"
    return cache.get(key)


def invalidate_player_cache(player_id: Optional[str] = None):
    """
    Invalidate player-related cache entries.

    Args:
        player_id: Specific player ID to invalidate, or None for all players
    """
    cache = get_cache()
    if player_id:
        pattern = f"fpl:player_score:{player_id}"
    else:
        pattern = "fpl:player_score:*"

    deleted_count = cache.invalidate_pattern(pattern)
    logger.info(f"Invalidated {deleted_count} player cache entries")


def invalidate_transfer_cache():
    """Invalidate all transfer recommendation cache entries."""
    cache = get_cache()
    pattern = "fpl:transfer_recommendations:*"
    deleted_count = cache.invalidate_pattern(pattern)
    logger.info(f"Invalidated {deleted_count} transfer cache entries")


def invalidate_backtest_cache():
    """Invalidate all backtest result cache entries."""
    cache = get_cache()
    pattern = "fpl:backtest_result:*"
    deleted_count = cache.invalidate_pattern(pattern)
    logger.info(f"Invalidated {deleted_count} backtest cache entries")


# ============================================================================
# CACHE MONITORING
# ============================================================================


def get_cache_health() -> Dict[str, Any]:
    """
    Get cache health status.

    Returns:
        Dictionary with cache health information
    """
    cache = get_cache()
    stats = cache.get_stats()

    health = {
        "status": stats.get("status", "unknown"),
        "connected": stats.get("status") == "connected",
        "stats": stats,
    }

    return health


def clear_all_cache() -> int:
    """
    Clear all FPL-related cache entries.

    Returns:
        Number of keys deleted
    """
    cache = get_cache()
    pattern = "fpl:*"
    deleted_count = cache.invalidate_pattern(pattern)
    logger.info(f"Cleared all FPL cache: {deleted_count} entries deleted")
    return deleted_count
