"""
Tools package - external APIs and utilities for agents
"""

from .search import SearchAPI, SearchAPIFactory, SearchResult
from .rss_reader import RSSReader, RSSArticle
from .web_scraper import WebScraper, ArticleContent

__all__ = [
    "SearchAPI",
    "SearchAPIFactory",
    "SearchResult",
    "RSSReader",
    "RSSArticle",
    "WebScraper",
    "ArticleContent"
]
