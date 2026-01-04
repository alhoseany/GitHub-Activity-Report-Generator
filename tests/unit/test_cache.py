# =============================================================================
# FILE: tests/unit/test_cache.py
# TASKS: UC-13.1
# PLAN: Section 4
# =============================================================================
"""
Unit tests for caching functionality.  # UC-13.1 | PLAN-4

Tests:
- ResponseCache class
- get/set operations
- TTL expiration
- Cache key generation
- Cleanup operations
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.cache import ResponseCache, create_cache
from src.config.settings import CacheConfig


class TestResponseCache:  # UC-13.1 | PLAN-4
    """Tests for ResponseCache class."""

    @pytest.fixture
    def cache(self, temp_cache_dir: Path):
        """Create a ResponseCache instance with temp directory."""
        config = CacheConfig(
            enabled=True,
            directory=str(temp_cache_dir),
            ttl_hours=24
        )
        return ResponseCache(config)

    @pytest.fixture
    def disabled_cache(self, temp_cache_dir: Path):
        """Create a disabled ResponseCache instance."""
        config = CacheConfig(
            enabled=False,
            directory=str(temp_cache_dir),
            ttl_hours=24
        )
        return ResponseCache(config)

    def test_init_creates_directory(self, temp_dir: Path):
        """Test that initialization creates cache directory."""
        cache_dir = temp_dir / "new_cache"
        assert not cache_dir.exists()

        config = CacheConfig(
            enabled=True,
            directory=str(cache_dir),
            ttl_hours=24
        )
        ResponseCache(config)

        assert cache_dir.exists()

    def test_enabled_property(self, cache, disabled_cache):
        """Test enabled property."""
        assert cache.enabled is True
        assert disabled_cache.enabled is False

    def test_ttl_hours_property(self, cache):
        """Test ttl_hours property."""
        assert cache.ttl_hours == 24

    def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        data = {"key": "value", "list": [1, 2, 3]}
        cache.set("test_key", data)

        result = cache.get("test_key")

        assert result == data

    def test_get_nonexistent_key(self, cache):
        """Test get returns None for non-existent key."""
        result = cache.get("nonexistent_key")
        assert result is None

    def test_set_disabled(self, disabled_cache):
        """Test set does nothing when disabled."""
        disabled_cache.set("test_key", {"data": "test"})
        result = disabled_cache.get("test_key")
        assert result is None

    def test_get_disabled(self, disabled_cache, temp_cache_dir: Path):
        """Test get returns None when disabled."""
        # Manually create a cache file
        cache_file = temp_cache_dir / "abc123.json"
        cache_file.write_text('{"data": "test"}')

        result = disabled_cache.get("any_key")
        assert result is None

    def test_delete_existing(self, cache):
        """Test deleting existing cache entry."""
        cache.set("test_key", {"data": "test"})
        assert cache.get("test_key") is not None

        result = cache.delete("test_key")

        assert result is True
        assert cache.get("test_key") is None

    def test_delete_nonexistent(self, cache):
        """Test deleting non-existent entry."""
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear(self, cache):
        """Test clearing all cache entries."""
        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})
        cache.set("key3", {"data": 3})

        count = cache.clear()

        assert count == 3
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_clear_empty_cache(self, cache):
        """Test clearing empty cache."""
        count = cache.clear()
        assert count == 0

    def test_is_expired_nonexistent(self, cache):
        """Test is_expired for non-existent key."""
        assert cache.is_expired("nonexistent") is True

    def test_is_expired_fresh(self, cache):
        """Test is_expired for fresh entry."""
        cache.set("fresh_key", {"data": "test"})
        assert cache.is_expired("fresh_key") is False

    def test_cleanup_expired(self, cache, temp_cache_dir: Path):
        """Test cleanup_expired removes old entries."""
        cache.set("key1", {"data": 1})

        # Manually create an old cache file
        import hashlib
        old_key = "old_key"
        key_hash = hashlib.md5(old_key.encode()).hexdigest()
        old_file = temp_cache_dir / f"{key_hash}.json"
        old_file.write_text('{"data": "old"}')

        # Modify the mtime to be older than TTL
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        import os
        os.utime(old_file, (old_time, old_time))

        count = cache.cleanup_expired()

        assert count == 1
        assert not old_file.exists()
        # Fresh entry should still exist
        assert cache.get("key1") is not None


class TestCacheKeyGeneration:  # UC-13.1 | PLAN-4
    """Tests for cache key generation."""

    @pytest.fixture
    def cache(self, temp_cache_dir: Path):
        """Create a ResponseCache instance."""
        config = CacheConfig(
            enabled=True,
            directory=str(temp_cache_dir),
            ttl_hours=24
        )
        return ResponseCache(config)

    def test_get_cache_key_simple(self, cache):
        """Test simple cache key generation."""
        key = cache.get_cache_key("/users/events")
        assert key == "/users/events"

    def test_get_cache_key_with_params(self, cache):
        """Test cache key with parameters."""
        key = cache.get_cache_key(
            "/users/events",
            {"per_page": 100, "page": 1}
        )

        assert "/users/events" in key
        assert "per_page=100" in key
        assert "page=1" in key

    def test_get_cache_key_params_sorted(self, cache):
        """Test that parameters are sorted for consistent keys."""
        key1 = cache.get_cache_key("/api", {"b": 2, "a": 1})
        key2 = cache.get_cache_key("/api", {"a": 1, "b": 2})

        assert key1 == key2


class TestCacheStats:  # UC-13.1 | PLAN-4
    """Tests for cache statistics."""

    @pytest.fixture
    def cache(self, temp_cache_dir: Path):
        """Create a ResponseCache instance."""
        config = CacheConfig(
            enabled=True,
            directory=str(temp_cache_dir),
            ttl_hours=24
        )
        return ResponseCache(config)

    def test_get_stats_empty(self, cache):
        """Test stats for empty cache."""
        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["total_entries"] == 0
        assert stats["total_size_bytes"] == 0

    def test_get_stats_with_entries(self, cache):
        """Test stats with cache entries."""
        cache.set("key1", {"data": "test1"})
        cache.set("key2", {"data": "test2"})

        stats = cache.get_stats()

        assert stats["total_entries"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["valid_entries"] == 2
        assert stats["expired_entries"] == 0

    def test_get_stats_disabled(self, temp_cache_dir: Path):
        """Test stats for disabled cache."""
        config = CacheConfig(
            enabled=False,
            directory=str(temp_cache_dir),
            ttl_hours=24
        )
        cache = ResponseCache(config)

        stats = cache.get_stats()

        assert stats["enabled"] is False
        assert stats["total_entries"] == 0


class TestCreateCache:  # UC-13.1 | PLAN-4
    """Tests for create_cache factory function."""

    def test_creates_response_cache(self, temp_cache_dir: Path):
        """Test factory creates ResponseCache instance."""
        config = CacheConfig(
            enabled=True,
            directory=str(temp_cache_dir),
            ttl_hours=12
        )

        cache = create_cache(config)

        assert isinstance(cache, ResponseCache)
        assert cache.ttl_hours == 12
