"""
Scrapers package for collecting scam URLs from various sources.
"""
from .base_scraper import BaseScraper
from .reddit_scraper import RedditScraper
from .twitter_scraper import TwitterScraper
from .bbb_scraper import BBBScraper
from .ftc_scraper import FTCScraper

__all__ = [
    'BaseScraper',
    'RedditScraper',
    'TwitterScraper',
    'BBBScraper',
    'FTCScraper'
]