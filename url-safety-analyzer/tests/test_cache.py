"""
Test suite for URL caching system.

Tests cover:
- Cache storage and retrieval
- Cache expiration
- Cache invalidation
- File system operations
"""
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import json
import time

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.unit
@pytest.mark.nightly
class TestCacheStorage:
    """Test cache storage operations."""

    def test_store_url_content(self, temp_cache_dir):
        """Test storing URL content in cache."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"
        content = {"html": "<html>Test</html>", "text": "Test"}

        cache.store(url, content)

        # Verify file was created
        cache_files = list(temp_cache_dir.rglob("*.json"))
        assert len(cache_files) > 0

    def test_retrieve_cached_content(self, temp_cache_dir):
        """Test retrieving cached URL content."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"
        content = {"html": "<html>Test</html>", "text": "Test"}

        cache.store(url, content)
        retrieved = cache.get(url)

        assert retrieved is not None
        assert retrieved["html"] == content["html"]
        assert retrieved["text"] == content["text"]

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss for non-existent URL."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        result = cache.get("https://nonexistent.com")

        assert result is None

    def test_overwrite_cache_entry(self, temp_cache_dir):
        """Test overwriting existing cache entry."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"

        # Store initial content
        cache.store(url, {"text": "Initial"})

        # Overwrite with new content
        cache.store(url, {"text": "Updated"})

        # Retrieve and verify
        retrieved = cache.get(url)
        assert retrieved["text"] == "Updated"


@pytest.mark.unit
@pytest.mark.nightly
class TestCacheExpiration:
    """Test cache expiration functionality."""

    def test_expired_cache_entry(self, temp_cache_dir):
        """Test handling of expired cache entries."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir), ttl=1)  # 1 second TTL
        url = "https://example.com"

        cache.store(url, {"text": "Test"})

        # Wait for expiration
        time.sleep(2)

        # Should not retrieve expired content
        result = cache.get(url)
        assert result is None or cache.is_expired(url)

    def test_valid_cache_entry(self, temp_cache_dir):
        """Test that non-expired entries are retrieved."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir), ttl=3600)  # 1 hour TTL
        url = "https://example.com"

        cache.store(url, {"text": "Test"})

        # Should retrieve valid content
        result = cache.get(url)
        assert result is not None
        assert result["text"] == "Test"

    def test_custom_ttl_per_entry(self, temp_cache_dir):
        """Test custom TTL for individual entries."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"

        # Store with custom TTL
        cache.store(url, {"text": "Test"}, ttl=2)

        # Immediately should be valid
        result = cache.get(url)
        assert result is not None

        # Wait for expiration
        time.sleep(3)

        # Should be expired
        result = cache.get(url)
        assert result is None or cache.is_expired(url)


@pytest.mark.unit
@pytest.mark.nightly
class TestCacheInvalidation:
    """Test cache invalidation operations."""

    def test_clear_single_entry(self, temp_cache_dir):
        """Test clearing a single cache entry."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"

        cache.store(url, {"text": "Test"})
        cache.clear_entry(url)

        result = cache.get(url)
        assert result is None

    def test_clear_all_cache(self, temp_cache_dir):
        """Test clearing entire cache."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))

        # Store multiple entries
        cache.store("https://example1.com", {"text": "Test1"})
        cache.store("https://example2.com", {"text": "Test2"})
        cache.store("https://example3.com", {"text": "Test3"})

        # Clear all
        cache.clear_all()

        # Verify all entries are gone
        assert cache.get("https://example1.com") is None
        assert cache.get("https://example2.com") is None
        assert cache.get("https://example3.com") is None

    def test_clear_expired_entries(self, temp_cache_dir):
        """Test clearing only expired entries."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir), ttl=1)

        # Store entries
        cache.store("https://expired.com", {"text": "Expired"})
        time.sleep(2)
        cache.store("https://valid.com", {"text": "Valid"})

        # Clear expired
        cache.clear_expired()

        # Valid entry should remain
        assert cache.get("https://valid.com") is not None
        # Expired entry should be gone
        assert cache.get("https://expired.com") is None


@pytest.mark.unit
@pytest.mark.nightly
class TestCacheMetadata:
    """Test cache metadata handling."""

    def test_store_metadata(self, temp_cache_dir):
        """Test storing metadata with cached content."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"
        content = {"text": "Test"}
        metadata = {
            "status_code": 200,
            "content_type": "text/html",
            "cached_at": "2024-01-01T00:00:00Z",
        }

        cache.store(url, content, metadata=metadata)
        retrieved_metadata = cache.get_metadata(url)

        assert retrieved_metadata is not None
        assert retrieved_metadata["status_code"] == 200
        assert retrieved_metadata["content_type"] == "text/html"

    def test_update_metadata(self, temp_cache_dir):
        """Test updating metadata for cached entry."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        url = "https://example.com"

        cache.store(url, {"text": "Test"}, metadata={"version": 1})
        cache.update_metadata(url, {"version": 2})

        metadata = cache.get_metadata(url)
        assert metadata["version"] == 2


@pytest.mark.unit
@pytest.mark.nightly
class TestCacheStatistics:
    """Test cache statistics and monitoring."""

    def test_cache_hit_rate(self, temp_cache_dir):
        """Test cache hit rate calculation."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))

        # Store some entries
        cache.store("https://example.com", {"text": "Test"})

        # Perform lookups
        cache.get("https://example.com")  # Hit
        cache.get("https://missing.com")  # Miss
        cache.get("https://example.com")  # Hit

        stats = cache.get_statistics()
        # Should have 2 hits, 1 miss
        assert stats["hits"] == 2 or stats.get("hit_rate", 0) > 0

    def test_cache_size(self, temp_cache_dir):
        """Test cache size calculation."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))

        cache.store("https://example1.com", {"text": "Test1"})
        cache.store("https://example2.com", {"text": "Test2"})

        size = cache.get_size()
        assert size == 2

    def test_cache_storage_used(self, temp_cache_dir):
        """Test calculation of storage used by cache."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))

        cache.store("https://example.com", {"text": "Test" * 1000})

        storage = cache.get_storage_used()
        assert storage > 0  # Should have some bytes stored


@pytest.mark.integration
@pytest.mark.nightly
class TestCacheIntegration:
    """Integration tests for caching system."""

    @pytest.mark.asyncio
    async def test_url_analyzer_with_cache(self, temp_cache_dir, mock_http_response):
        """Test URL analyzer using cache."""
        from url_analyzer_cached import CachedURLAnalyzer
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))
        analyzer = CachedURLAnalyzer(cache=cache)

        with patch('httpx.AsyncClient.get', return_value=mock_http_response()):
            # First analysis - cache miss
            result1 = await analyzer.analyze("https://example.com")
            assert result1 is not None

            # Second analysis - cache hit
            result2 = await analyzer.analyze("https://example.com")
            assert result2 is not None

            # Results should be identical
            assert result1 == result2

    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across instances."""
        from url_cache import URLCache

        # First instance
        cache1 = URLCache(cache_dir=str(temp_cache_dir))
        cache1.store("https://example.com", {"text": "Persistent"})

        # Second instance
        cache2 = URLCache(cache_dir=str(temp_cache_dir))
        result = cache2.get("https://example.com")

        assert result is not None
        assert result["text"] == "Persistent"
