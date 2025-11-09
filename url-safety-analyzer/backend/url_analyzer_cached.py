"""
URL Analyzer with Cache Integration

Extends URLAnalyzer to use local cache before fetching from internet.

Benefits:
- Evaluation works even if malicious URLs go offline
- Faster repeated evaluations
- Consistent test data
- Reduced network requests
"""

import logging
from typing import Dict, Any, Optional
import httpx

from url_analyzer import URLAnalyzer
from url_cache import URLCache, get_global_cache

logger = logging.getLogger(__name__)


class CachedURLAnalyzer(URLAnalyzer):
    """
    URL Analyzer with cache-first approach

    Workflow:
    1. Check if URL is in cache
    2. If cached, use cached content
    3. If not cached, fetch from internet and cache
    4. Perform analysis on content
    """

    def __init__(self, cache_dir: str = "./url_cache", use_cache: bool = True):
        """
        Initialize cached URL analyzer

        Args:
            cache_dir: Directory for URL cache
            use_cache: Enable/disable caching (default: True)
        """
        super().__init__()
        self.use_cache = use_cache
        self.cache = get_global_cache(cache_dir) if use_cache else None

    async def _get_http_response(
        self,
        url: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Get HTTP response with cache-first approach

        Args:
            url: URL to fetch
            timeout: Request timeout

        Returns:
            Dict with response data
        """
        # Try cache first if enabled
        if self.use_cache and self.cache:
            try:
                cached_data = await self.cache.get_or_fetch(
                    url=url,
                    timeout=timeout,
                    force_refresh=False
                )

                if cached_data:
                    logger.info(f"Using {'cached' if cached_data.get('from_cache') else 'fresh'} data for {url}")

                    return {
                        "status_code": cached_data.get("status_code", 200),
                        "headers": cached_data.get("headers", {}),
                        "content": cached_data.get("content_html", ""),
                        "from_cache": cached_data.get("from_cache", False)
                    }
            except Exception as e:
                logger.warning(f"Cache error for {url}, falling back to direct fetch: {str(e)}")
                # Fall through to direct fetch

        # Direct fetch (no cache or cache failed)
        return await self._fetch_url_direct(url, timeout)

    async def _fetch_url_direct(
        self,
        url: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch URL directly from internet (original behavior)

        Args:
            url: URL to fetch
            timeout: Request timeout

        Returns:
            Dict with response data
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                response = await client.get(url, headers=headers)

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "from_cache": False
                }

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return {
                "status_code": 0,
                "headers": {},
                "content": "",
                "error": "timeout",
                "from_cache": False
            }
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return {
                "status_code": 0,
                "headers": {},
                "content": "",
                "error": str(e),
                "from_cache": False
            }

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyze URL with cache integration

        Args:
            url: URL to analyze

        Returns:
            Dict with comprehensive analysis
        """
        logger.info(f"Analyzing URL: {url} (cache {'enabled' if self.use_cache else 'disabled'})")

        # Call parent class analyze method
        # The HTTP fetching will use our overridden _get_http_response
        result = await super().analyze(url)

        # Add cache metadata
        if self.use_cache and self.cache:
            result["cache_info"] = {
                "cache_enabled": True,
                "was_cached": result.get("http_response", {}).get("from_cache", False)
            }

        return result

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_statistics()
        return {"cache_enabled": False}

    def clear_cache(self, url: Optional[str] = None):
        """
        Clear cache

        Args:
            url: Optional specific URL to clear. If None, clears all.
        """
        if self.cache:
            self.cache.clear_cache(url)


# Convenience function for creating cached analyzer
def create_cached_analyzer(cache_dir: str = "./url_cache", use_cache: bool = True) -> CachedURLAnalyzer:
    """
    Create cached URL analyzer

    Args:
        cache_dir: Directory for cache
        use_cache: Enable caching

    Returns:
        CachedURLAnalyzer instance
    """
    return CachedURLAnalyzer(cache_dir=cache_dir, use_cache=use_cache)
