"""
Base scraper class providing common functionality for all scrapers.
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize base scraper.

        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_request_time = 0

    def rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method to be implemented by subclasses.

        Returns:
            List of dictionaries containing scraped data
        """
        pass

    def safe_scrape(self) -> List[Dict[str, Any]]:
        """
        Wrapper around scrape() with error handling.

        Returns:
            List of scraped data, empty list on error
        """
        try:
            self.logger.info(f"Starting scrape with {self.__class__.__name__}")
            results = self.scrape()
            self.logger.info(f"Scrape completed. Found {len(results)} items")
            return results
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}", exc_info=True)
            return []

    def create_record(
        self,
        url: str,
        source: str,
        source_id: str,
        source_url: str,
        context: str,
        scam_type: str = None,
        date_posted: datetime = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized record dictionary.

        Args:
            url: The scam URL found
            source: Source platform (reddit, twitter, bbb, ftc)
            source_id: Unique ID from the source (post_id, tweet_id, etc.)
            source_url: URL back to the source
            context: Text context where URL was found
            scam_type: Type/category of scam
            date_posted: When the content was posted
            metadata: Additional source-specific data

        Returns:
            Standardized record dictionary
        """
        return {
            'url': url,
            'source': source,
            'source_id': source_id,
            'source_url': source_url,
            'context': context[:500] if context else '',  # Truncate to 500 chars
            'scam_type': scam_type,
            'date_posted': date_posted or datetime.now(),
            'metadata': metadata or {}
        }
