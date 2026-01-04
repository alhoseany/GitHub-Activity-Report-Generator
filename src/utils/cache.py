# =============================================================================
# FILE: src/utils/cache.py
# TASKS: UC-8.1
# PLAN: Section 3.5
# =============================================================================
"""
Request/Response Cache.

This module provides file-based caching for API responses:

Cache features (UC-8.1 | PLAN-3.5):
- File-based caching in configurable directory
- TTL-based expiration (configurable via cache.ttl_hours)
- Cache key = hash of request parameters
- Automatic cleanup of expired entries
- Can be disabled via cache.enabled or --no-cache CLI flag

Cache class methods:
- get(key): Get cached value or None
- set(key, value, ttl=None): Store value with optional TTL
- delete(key): Remove cached entry
- clear(): Clear all cached entries
- is_expired(key): Check if entry is expired

Cache key format:
- {endpoint}_{params_hash}.json

Configuration (UC-8.1):
- cache.enabled: Enable/disable caching (default: True)
- cache.directory: Cache directory path (default: ".cache")
- cache.ttl_hours: Time-to-live in hours (default: 24)
"""
# UC-8.1 | PLAN-3.5

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.config.settings import CacheConfig


class ResponseCache:  # UC-8.1, UC-8.1 | PLAN-3.5
    """
    Simple file-based response cache with TTL support.

    Provides caching for API responses to reduce redundant requests
    and improve performance during report generation.

    Configuration is read from CacheConfig:
    - enabled: Whether caching is active
    - directory: Where cache files are stored
    - ttl_hours: How long cache entries remain valid

    Attributes:
        config: CacheConfig with enabled, directory, ttl_hours settings
        cache_dir: Path to cache directory
    """

    def __init__(self, config: CacheConfig) -> None:
        """
        Initialize the cache.

        Args:
            config: CacheConfig instance with cache settings
        """
        self.config = config  # UC-8.1 | PLAN-3.5 - use configured settings
        self.cache_dir = Path(config.directory)
        if config.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:  # UC-8.1 | PLAN-3.5
        """Check if caching is enabled."""
        return self.config.enabled

    @property
    def ttl_hours(self) -> int:  # UC-8.1 | PLAN-3.5
        """Get TTL in hours from config."""
        return self.config.ttl_hours

    def get(self, key: str) -> dict | list | None:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Get cached response if valid (not expired).

        Checks the enabled flag before attempting to read cache.

        Args:
            key: Cache key (typically endpoint + params)

        Returns:
            Cached data if exists and not expired, None otherwise
        """
        if not self.config.enabled:  # UC-8.1 | PLAN-3.5 - check enabled flag
            return None

        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None

        # Check TTL using file modification time  # UC-8.1 | PLAN-3.5 - use configured ttl_hours
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        ttl_seconds = self.config.ttl_hours * 3600

        if datetime.now() - mtime > timedelta(seconds=ttl_seconds):
            # Cache expired, remove file
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # Invalid cache file, remove it
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, data: dict | list) -> None:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Store response in cache.

        Checks the enabled flag before storing data.

        Args:
            key: Cache key (typically endpoint + params)
            data: Data to cache (must be JSON-serializable)
        """
        if not self.config.enabled:  # UC-8.1 | PLAN-3.5 - check enabled flag
            return

        cache_file = self._get_cache_path(key)

        try:
            # Ensure cache directory exists  # UC-8.1 | PLAN-3.5 - use configured directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as e:
            # Log error but don't fail - caching is best-effort
            pass

    def delete(self, key: str) -> bool:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Remove a specific cache entry.

        Args:
            key: Cache key to delete

        Returns:
            True if entry was deleted, False if not found
        """
        if not self.config.enabled:
            return False

        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except OSError:
                return False
        return False

    def clear(self) -> int:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Clear all cached entries.

        Returns:
            Number of cache files deleted
        """
        if not self.config.enabled or not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass
        return count

    def is_expired(self, key: str) -> bool:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Check if a cache entry is expired.

        Uses configured ttl_hours for expiration check.

        Args:
            key: Cache key to check

        Returns:
            True if expired or not found, False if valid
        """
        if not self.config.enabled:
            return True

        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return True

        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        ttl_seconds = self.config.ttl_hours * 3600  # UC-8.1 | PLAN-3.5 - use configured TTL
        return datetime.now() - mtime > timedelta(seconds=ttl_seconds)

    def cleanup_expired(self) -> int:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Remove all expired cache entries.

        Uses configured ttl_hours to determine expiration.

        Returns:
            Number of expired entries removed
        """
        if not self.config.enabled or not self.cache_dir.exists():
            return 0

        count = 0
        ttl_seconds = self.config.ttl_hours * 3600  # UC-8.1 | PLAN-3.5 - use configured TTL
        cutoff = datetime.now() - timedelta(seconds=ttl_seconds)

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    cache_file.unlink()
                    count += 1
            except OSError:
                pass
        return count

    def _get_cache_path(self, key: str) -> Path:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Get cache file path for a key.

        Uses MD5 hash of key to generate consistent, filesystem-safe filename.
        Uses configured directory for cache storage.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"  # UC-8.1 | PLAN-3.5 - use configured directory

    def get_cache_key(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None
    ) -> str:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Generate a cache key from endpoint and parameters.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            Cache key string
        """
        if params:
            # Sort params for consistent keys
            sorted_params = sorted(params.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            return f"{endpoint}?{params_str}"
        return endpoint

    def get_stats(self) -> dict[str, Any]:  # UC-8.1, UC-8.1 | PLAN-3.5
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats:
            - enabled: Whether cache is enabled
            - directory: Cache directory path
            - ttl_hours: Configured TTL
            - total_entries: Number of cached items
            - total_size_bytes: Total size of cache
            - expired_entries: Number of expired items
            - valid_entries: Number of valid items
        """
        stats = {
            "enabled": self.config.enabled,
            "directory": str(self.cache_dir),
            "ttl_hours": self.config.ttl_hours,
        }

        if not self.config.enabled or not self.cache_dir.exists():
            stats.update({
                "total_entries": 0,
                "total_size_bytes": 0,
                "expired_entries": 0,
                "valid_entries": 0,
            })
            return stats

        total = 0
        expired = 0
        size = 0
        ttl_seconds = self.config.ttl_hours * 3600
        cutoff = datetime.now() - timedelta(seconds=ttl_seconds)

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                total += 1
                size += cache_file.stat().st_size
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    expired += 1
            except OSError:
                pass

        stats.update({
            "total_entries": total,
            "total_size_bytes": size,
            "expired_entries": expired,
            "valid_entries": total - expired,
        })
        return stats


def create_cache(config: CacheConfig) -> ResponseCache:  # UC-8.1, UC-8.1 | PLAN-3.5
    """
    Factory function to create a ResponseCache instance.

    Args:
        config: CacheConfig instance

    Returns:
        Configured ResponseCache instance
    """
    return ResponseCache(config)
