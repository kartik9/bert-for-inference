"""
RSS Feed Reader
Monitors and fetches articles from RSS feeds
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import feedparser
from dateutil import parser as date_parser


@dataclass
class RSSArticle:
    """Article from RSS feed"""
    title: str
    url: str
    summary: str
    published_date: Optional[datetime] = None
    source_feed: str = ""
    author: Optional[str] = None


class RSSReader:
    """RSS Feed Reader"""

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Initialize RSS reader

        Args:
            rate_limit_delay: Delay between feed requests (seconds)
        """
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

    def fetch_feed(
        self,
        feed_url: str,
        feed_name: str = "",
        max_age_days: Optional[int] = 7
    ) -> List[RSSArticle]:
        """
        Fetch articles from a single RSS feed

        Args:
            feed_url: URL of the RSS feed
            feed_name: Human-readable name of the feed
            max_age_days: Only return articles newer than this (None for all)

        Returns:
            List of RSSArticle objects
        """
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        articles = []

        try:
            # Parse feed
            feed = feedparser.parse(feed_url)

            # Use feed title if name not provided
            if not feed_name and feed.get('feed', {}).get('title'):
                feed_name = feed.feed.title

            # Calculate age threshold
            age_threshold = None
            if max_age_days:
                age_threshold = datetime.now() - timedelta(days=max_age_days)

            # Process entries
            for entry in feed.entries:
                # Parse published date
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'published'):
                    try:
                        published_date = date_parser.parse(entry.published)
                    except:
                        pass

                # Filter by age
                if age_threshold and published_date:
                    if published_date < age_threshold:
                        continue

                # Extract article data
                article = RSSArticle(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    summary=entry.get('summary', entry.get('description', '')),
                    published_date=published_date,
                    source_feed=feed_name,
                    author=entry.get('author', None)
                )

                articles.append(article)

        except Exception as e:
            print(f"Error fetching RSS feed {feed_url}: {e}")

        finally:
            self._last_request_time = time.time()

        return articles

    def fetch_multiple_feeds(
        self,
        feed_configs: List[dict],
        max_age_days: Optional[int] = 7
    ) -> List[RSSArticle]:
        """
        Fetch articles from multiple RSS feeds

        Args:
            feed_configs: List of dicts with 'name' and 'url' keys
            max_age_days: Only return articles newer than this

        Returns:
            Combined list of RSSArticle objects from all feeds
        """
        all_articles = []

        for feed_config in feed_configs:
            feed_url = feed_config.get('url')
            feed_name = feed_config.get('name', '')

            if not feed_url:
                continue

            articles = self.fetch_feed(
                feed_url=feed_url,
                feed_name=feed_name,
                max_age_days=max_age_days
            )

            all_articles.extend(articles)

        return all_articles


# Example usage:
if __name__ == "__main__":
    reader = RSSReader()

    # Fetch single feed
    articles = reader.fetch_feed(
        feed_url="https://krebsonsecurity.com/feed/",
        feed_name="Krebs on Security",
        max_age_days=7
    )

    print(f"Found {len(articles)} articles from Krebs on Security:\n")
    for article in articles[:3]:
        print(f"Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Published: {article.published_date}")
        print(f"Summary: {article.summary[:100]}...")
        print()
