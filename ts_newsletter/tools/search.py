"""
Configurable Search API abstraction
Supports DuckDuckGo (free) and Bing Search API (paid)
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import requests
from duckduckgo_search import DDGS


@dataclass
class SearchResult:
    """Unified search result format"""
    title: str
    url: str
    snippet: str
    published_date: Optional[datetime] = None
    source: Optional[str] = None


class SearchAPI(ABC):
    """Abstract base class for search APIs"""

    @abstractmethod
    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """Execute search and return results"""
        pass


class DuckDuckGoSearch(SearchAPI):
    """DuckDuckGo Search (free, no API key required)"""

    def __init__(
        self,
        region: str = "us-en",
        safesearch: str = "moderate",
        time_range: str = "w",  # w=week, m=month, y=year
        rate_limit_delay: float = 1.0
    ):
        self.region = region
        self.safesearch = safesearch
        self.time_range = time_range
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """
        Search using DuckDuckGo

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        results = []

        try:
            with DDGS() as ddgs:
                # Search with time filter
                raw_results = ddgs.text(
                    keywords=query,
                    region=self.region,
                    safesearch=self.safesearch,
                    timelimit=self.time_range,
                    max_results=max_results
                )

                for result in raw_results:
                    search_result = SearchResult(
                        title=result.get("title", ""),
                        url=result.get("href", ""),
                        snippet=result.get("body", ""),
                        source="duckduckgo"
                    )
                    results.append(search_result)

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")

        finally:
            self._last_request_time = time.time()

        return results


class BingSearch(SearchAPI):
    """Bing Search API (paid, requires API key)"""

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.bing.microsoft.com/v7.0/search",
        market: str = "en-US",
        freshness: str = "Week",  # Day, Week, Month
        rate_limit_delay: float = 0.1
    ):
        self.api_key = api_key
        self.endpoint = endpoint
        self.market = market
        self.freshness = freshness
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

        # Request headers
        self.headers = {"Ocp-Apim-Subscription-Key": api_key}

    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """
        Search using Bing Search API

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        results = []

        try:
            params = {
                "q": query,
                "mkt": self.market,
                "freshness": self.freshness,
                "count": max_results,
                "responseFilter": "Webpages"  # Only web results
            }

            response = requests.get(
                self.endpoint,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # Parse web pages results
            if "webPages" in data and "value" in data["webPages"]:
                for result in data["webPages"]["value"]:
                    # Parse date if available
                    published_date = None
                    if "dateLastCrawled" in result:
                        try:
                            published_date = datetime.fromisoformat(
                                result["dateLastCrawled"].replace("Z", "+00:00")
                            )
                        except:
                            pass

                    search_result = SearchResult(
                        title=result.get("name", ""),
                        url=result.get("url", ""),
                        snippet=result.get("snippet", ""),
                        published_date=published_date,
                        source="bing"
                    )
                    results.append(search_result)

        except requests.exceptions.HTTPError as e:
            print(f"Bing Search API HTTP error: {e}")
            if e.response.status_code == 401:
                print("Invalid Bing API key")
            elif e.response.status_code == 403:
                print("Bing API quota exceeded or access denied")

        except Exception as e:
            print(f"Bing search error: {e}")

        finally:
            self._last_request_time = time.time()

        return results


class SearchAPIFactory:
    """Factory for creating search API instances based on configuration"""

    @staticmethod
    def create(config) -> SearchAPI:
        """
        Create search API instance based on configuration

        Args:
            config: Config object from config_loader

        Returns:
            SearchAPI instance (DuckDuckGo or Bing)
        """
        provider = config.search.provider.lower()

        if provider == "duckduckgo":
            # Get DuckDuckGo specific config
            ddg_config = config.raw.get("search", {}).get("duckduckgo", {})

            return DuckDuckGoSearch(
                region=ddg_config.get("region", "us-en"),
                safesearch=ddg_config.get("safesearch", "moderate"),
                time_range=ddg_config.get("time_range", "w"),
                rate_limit_delay=config.raw.get("scraping", {}).get("rate_limit_delay", 1.0)
            )

        elif provider == "bing":
            if not config.search.bing_api_key:
                raise ValueError("Bing API key not configured")

            # Get Bing specific config
            bing_config = config.raw.get("search", {}).get("bing", {})

            return BingSearch(
                api_key=config.search.bing_api_key,
                endpoint=config.search.bing_endpoint,
                market=bing_config.get("market", "en-US"),
                freshness=bing_config.get("freshness", "Week"),
                rate_limit_delay=config.raw.get("scraping", {}).get("rate_limit_delay", 0.1)
            )

        else:
            raise ValueError(f"Unknown search provider: {provider}")


# Example usage:
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config

    # Load config
    config = get_config()

    # Create search API (automatically uses configured provider)
    search_api = SearchAPIFactory.create(config)

    # Search
    results = search_api.search("advertising fraud 2025", max_results=5)

    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Snippet: {result.snippet[:100]}...")
