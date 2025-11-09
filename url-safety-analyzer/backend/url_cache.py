"""
URL Content Cache System

Stores URL contents locally for evaluation purposes:
- HTML content
- HTTP headers
- Screenshots (if available)
- Technical analysis metadata
- Timestamps

Benefits:
- Evaluation works even if URL goes offline
- Faster repeated evaluations
- Consistent test data
- Historical preservation
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import aiofiles
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class URLCache:
    """
    Local cache for URL contents and metadata

    Cache Structure:
    url_cache/
    ├── index.json                    # URL -> cache_id mapping
    ├── metadata.json                 # Dataset metadata
    └── entries/
        └── <cache_id>/
            ├── info.json             # URL, timestamp, headers
            ├── content.html          # Raw HTML content
            ├── content.txt           # Cleaned text content
            ├── screenshot.png        # Screenshot (optional)
            └── analysis.json         # Technical analysis results
    """

    def __init__(self, cache_dir: str = "./url_cache"):
        """
        Initialize URL cache

        Args:
            cache_dir: Directory to store cache
        """
        self.cache_dir = Path(cache_dir)
        self.entries_dir = self.cache_dir / "entries"
        self.index_file = self.cache_dir / "index.json"
        self.metadata_file = self.cache_dir / "metadata.json"

        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.entries_dir.mkdir(exist_ok=True)

        # Load index
        self.index = self._load_index()
        self.metadata = self._load_metadata()

    def _load_index(self) -> Dict[str, str]:
        """Load URL -> cache_id index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """Save URL -> cache_id index"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "created": datetime.utcnow().isoformat(),
            "total_entries": 0,
            "last_updated": None
        }

    def _save_metadata(self):
        """Save cache metadata"""
        self.metadata["last_updated"] = datetime.utcnow().isoformat()
        self.metadata["total_entries"] = len(self.index)
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _generate_cache_id(self, url: str) -> str:
        """Generate unique cache ID for URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_entry_dir(self, cache_id: str) -> Path:
        """Get directory for cache entry"""
        return self.entries_dir / cache_id

    def has_cached(self, url: str) -> bool:
        """
        Check if URL is cached

        Args:
            url: URL to check

        Returns:
            True if cached, False otherwise
        """
        return url in self.index

    async def get_cached(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content for URL

        Args:
            url: URL to retrieve

        Returns:
            Dict with cached data or None if not cached
        """
        if not self.has_cached(url):
            return None

        cache_id = self.index[url]
        entry_dir = self._get_cache_entry_dir(cache_id)

        try:
            # Load info
            info_file = entry_dir / "info.json"
            if not info_file.exists():
                logger.warning(f"Cache entry corrupt for {url}: missing info.json")
                return None

            with open(info_file, 'r') as f:
                info = json.load(f)

            # Load content
            content_file = entry_dir / "content.html"
            content = None
            if content_file.exists():
                async with aiofiles.open(content_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()

            # Load text content
            text_file = entry_dir / "content.txt"
            text_content = None
            if text_file.exists():
                async with aiofiles.open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = await f.read()

            # Load analysis if available
            analysis_file = entry_dir / "analysis.json"
            analysis = None
            if analysis_file.exists():
                with open(analysis_file, 'r') as f:
                    analysis = json.load(f)

            cached_data = {
                "url": url,
                "cache_id": cache_id,
                "cached_at": info.get("cached_at"),
                "status_code": info.get("status_code"),
                "headers": info.get("headers", {}),
                "content_html": content,
                "content_text": text_content,
                "analysis": analysis,
                "from_cache": True
            }

            logger.info(f"Cache HIT for {url}")
            return cached_data

        except Exception as e:
            logger.error(f"Error reading cache for {url}: {str(e)}")
            return None

    async def save_to_cache(
        self,
        url: str,
        status_code: int,
        headers: Dict[str, str],
        content: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save URL content to cache

        Args:
            url: URL being cached
            status_code: HTTP status code
            headers: Response headers
            content: HTML content
            analysis: Optional technical analysis data

        Returns:
            cache_id
        """
        cache_id = self._generate_cache_id(url)
        entry_dir = self._get_cache_entry_dir(cache_id)
        entry_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save info
            info = {
                "url": url,
                "cache_id": cache_id,
                "cached_at": datetime.utcnow().isoformat(),
                "status_code": status_code,
                "headers": headers,
                "content_length": len(content) if content else 0
            }

            info_file = entry_dir / "info.json"
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)

            # Save HTML content
            if content:
                content_file = entry_dir / "content.html"
                async with aiofiles.open(content_file, 'w', encoding='utf-8') as f:
                    await f.write(content)

                # Extract and save text content
                try:
                    soup = BeautifulSoup(content, 'lxml')
                    # Remove script and style elements
                    for script in soup(["script", "style", "noscript"]):
                        script.decompose()
                    text = soup.get_text(separator=' ', strip=True)

                    text_file = entry_dir / "content.txt"
                    async with aiofiles.open(text_file, 'w', encoding='utf-8') as f:
                        await f.write(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from {url}: {str(e)}")

            # Save analysis if provided
            if analysis:
                analysis_file = entry_dir / "analysis.json"
                with open(analysis_file, 'w') as f:
                    json.dump(analysis, f, indent=2)

            # Update index
            self.index[url] = cache_id
            self._save_index()
            self._save_metadata()

            logger.info(f"Cached {url} -> {cache_id}")
            return cache_id

        except Exception as e:
            logger.error(f"Error saving cache for {url}: {str(e)}")
            raise

    async def fetch_and_cache(
        self,
        url: str,
        timeout: int = 30,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Fetch URL from internet and save to cache

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            user_agent: Optional user agent string

        Returns:
            Dict with fetched data
        """
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                verify=False  # Allow self-signed certs for testing
            ) as client:
                response = await client.get(url, headers=headers)

                # Get response data
                status_code = response.status_code
                response_headers = dict(response.headers)
                content = response.text

                # Save to cache
                cache_id = await self.save_to_cache(
                    url=url,
                    status_code=status_code,
                    headers=response_headers,
                    content=content
                )

                logger.info(f"Fetched and cached {url} (status: {status_code})")

                return {
                    "url": url,
                    "cache_id": cache_id,
                    "status_code": status_code,
                    "headers": response_headers,
                    "content_html": content,
                    "from_cache": False
                }

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            raise
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    async def get_or_fetch(
        self,
        url: str,
        force_refresh: bool = False,
        **fetch_kwargs
    ) -> Dict[str, Any]:
        """
        Get from cache or fetch from internet

        Args:
            url: URL to get
            force_refresh: Force fetch even if cached
            **fetch_kwargs: Arguments for fetch_and_cache

        Returns:
            Dict with URL data
        """
        # Check cache first unless force refresh
        if not force_refresh and self.has_cached(url):
            cached = await self.get_cached(url)
            if cached:
                return cached

        # Fetch from internet
        logger.info(f"Cache MISS for {url}, fetching from internet...")
        return await self.fetch_and_cache(url, **fetch_kwargs)

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = 0
        entry_count = len(self.index)

        # Calculate total cache size
        for cache_id in self.index.values():
            entry_dir = self._get_cache_entry_dir(cache_id)
            if entry_dir.exists():
                for file in entry_dir.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size

        return {
            "total_entries": entry_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "created": self.metadata.get("created"),
            "last_updated": self.metadata.get("last_updated")
        }

    def clear_cache(self, url: Optional[str] = None):
        """
        Clear cache

        Args:
            url: Optional specific URL to clear. If None, clears all.
        """
        if url:
            # Clear specific URL
            if url in self.index:
                cache_id = self.index[url]
                entry_dir = self._get_cache_entry_dir(cache_id)

                # Remove entry directory
                if entry_dir.exists():
                    import shutil
                    shutil.rmtree(entry_dir)

                # Remove from index
                del self.index[url]
                self._save_index()
                self._save_metadata()

                logger.info(f"Cleared cache for {url}")
        else:
            # Clear all
            if self.entries_dir.exists():
                import shutil
                shutil.rmtree(self.entries_dir)
                self.entries_dir.mkdir(exist_ok=True)

            self.index = {}
            self._save_index()
            self._save_metadata()

            logger.info("Cleared entire cache")

    def export_cache_metadata(self, output_file: str):
        """
        Export cache metadata for documentation

        Args:
            output_file: Path to output JSON file
        """
        metadata = {
            "statistics": self.get_statistics(),
            "urls": []
        }

        for url, cache_id in self.index.items():
            entry_dir = self._get_cache_entry_dir(cache_id)
            info_file = entry_dir / "info.json"

            if info_file.exists():
                with open(info_file, 'r') as f:
                    info = json.load(f)
                    metadata["urls"].append({
                        "url": url,
                        "cache_id": cache_id,
                        "cached_at": info.get("cached_at"),
                        "status_code": info.get("status_code")
                    })

        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Exported cache metadata to {output_file}")


# Global cache instance
_global_cache: Optional[URLCache] = None


def get_global_cache(cache_dir: str = "./url_cache") -> URLCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = URLCache(cache_dir=cache_dir)
    return _global_cache
