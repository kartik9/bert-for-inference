"""
FTC (Federal Trade Commission) scraper for scam information.
Scrapes news, consumer alerts, and enforcement actions.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from .base_scraper import BaseScraper
from ..utils.url_extractor import URLExtractor
from ..utils.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FTCScraper(BaseScraper):
    """Scraper for FTC consumer alerts and news."""

    FTC_NEWS_URL = "https://www.ftc.gov/news-events/news/browse"
    FTC_CONSUMER_URL = "https://consumer.ftc.gov/articles"
    FTC_BLOG_URL = "https://consumer.ftc.gov/consumer-alerts"

    def __init__(self):
        """Initialize FTC scraper."""
        super().__init__(rate_limit_delay=Config.SLEEP_BETWEEN_REQUESTS)

        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup is required for FTC scraping. Install with: pip install beautifulsoup4")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape scam information from FTC sources.

        Returns:
            List of URL records
        """
        all_results = []

        # Scrape consumer alerts
        self.logger.info("Scraping FTC consumer alerts")
        alerts = self.scrape_consumer_alerts(days_back=Config.FTC_DAYS_BACK)
        all_results.extend(alerts)
        self.rate_limit()

        # Scrape news/press releases
        self.logger.info("Scraping FTC news")
        news = self.scrape_news(days_back=Config.FTC_DAYS_BACK)
        all_results.extend(news)
        self.rate_limit()

        self.logger.info(f"FTC scraping complete. Found {len(all_results)} URL records")
        return all_results

    def scrape_consumer_alerts(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape FTC consumer alerts.

        Args:
            days_back: How many days back to scrape

        Returns:
            List of URL records
        """
        results = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            # Get the consumer alerts page
            response = self.session.get(self.FTC_BLOG_URL, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find article links
            articles = soup.find_all('article') or soup.find_all('div', class_='views-row')

            for article in articles[:20]:  # Limit to recent 20
                try:
                    # Extract article link
                    link_elem = article.find('a', href=True)
                    if not link_elem:
                        continue

                    article_url = link_elem['href']
                    if not article_url.startswith('http'):
                        article_url = f"https://consumer.ftc.gov{article_url}"

                    # Extract title
                    title = link_elem.get_text(strip=True)

                    # Check if scam-related
                    if not self._is_scam_related(title):
                        continue

                    # Extract date if available
                    date_elem = article.find('time') or article.find(class_='date')
                    article_date = datetime.now()

                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                        try:
                            from dateutil import parser
                            article_date = parser.parse(date_str)
                        except:
                            pass

                    # Check if recent enough
                    if article_date < cutoff_date:
                        continue

                    # Fetch and parse the article
                    article_results = self.scrape_article(article_url, title, article_date)
                    results.extend(article_results)

                    self.rate_limit()

                except Exception as e:
                    self.logger.debug(f"Error processing article: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping consumer alerts: {e}", exc_info=True)

        return results

    def scrape_news(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape FTC news and press releases.

        Args:
            days_back: How many days back to scrape

        Returns:
            List of URL records
        """
        results = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            # Get news page
            response = self.session.get(self.FTC_NEWS_URL, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find news items
            news_items = soup.find_all('article') or soup.find_all('div', class_='node')

            for item in news_items[:20]:  # Limit to recent 20
                try:
                    # Extract link
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue

                    news_url = link_elem['href']
                    if not news_url.startswith('http'):
                        news_url = f"https://www.ftc.gov{news_url}"

                    # Extract title
                    title = link_elem.get_text(strip=True)

                    # Check if scam/fraud related
                    if not self._is_scam_related(title):
                        continue

                    # Extract date
                    date_elem = item.find('time') or item.find(class_='date')
                    news_date = datetime.now()

                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                        try:
                            from dateutil import parser
                            news_date = parser.parse(date_str)
                        except:
                            pass

                    if news_date < cutoff_date:
                        continue

                    # Scrape the article
                    article_results = self.scrape_article(news_url, title, news_date)
                    results.extend(article_results)

                    self.rate_limit()

                except Exception as e:
                    self.logger.debug(f"Error processing news item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping news: {e}", exc_info=True)

        return results

    def scrape_article(
        self,
        url: str,
        title: str,
        date_posted: datetime
    ) -> List[Dict[str, Any]]:
        """
        Scrape a single FTC article for URLs.

        Args:
            url: Article URL
            title: Article title
            date_posted: Article publication date

        Returns:
            List of URL records
        """
        results = []

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract main content
            content_elem = (
                soup.find('div', class_='content') or
                soup.find('article') or
                soup.find('main') or
                soup.find('div', class_='article-body')
            )

            if not content_elem:
                self.logger.debug(f"No content found for {url}")
                return results

            # Get text content
            content_text = content_elem.get_text(separator=' ', strip=True)

            # Extract URLs from content
            urls = URLExtractor.extract_urls(content_text, include_bare_domains=True)

            # Also look for explicitly mentioned domains in text
            # Pattern: "site domain.com" or "website example.com"
            import re
            domain_mentions = re.findall(
                r'(?:site|website|domain|url|link to)\s+([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,})',
                content_text,
                re.IGNORECASE
            )

            for domain in domain_mentions:
                urls.append(f"http://{domain}")

            # Process each URL
            for found_url in urls:
                cleaned_url = URLExtractor.clean_url(found_url)

                if not URLExtractor.validate_url(cleaned_url):
                    continue

                # Expand shortened URLs
                if URLExtractor.is_url_shortener(cleaned_url):
                    expanded = URLExtractor.expand_shortened_url(cleaned_url)
                    if expanded:
                        cleaned_url = expanded

                # Find context around URL in text
                domain = URLExtractor.extract_domain(cleaned_url)
                context = self._find_context_around_url(content_text, domain or cleaned_url)

                # Create record
                record = self.create_record(
                    url=cleaned_url,
                    source='ftc',
                    source_id=url.split('/')[-1],  # Use URL slug as ID
                    source_url=url,
                    context=context or f"Mentioned in FTC article: {title}",
                    scam_type=self._classify_scam_from_text(title + ' ' + content_text),
                    date_posted=date_posted,
                    metadata={
                        'article_title': title,
                        'article_type': 'consumer_alert' if 'consumer' in url else 'news'
                    }
                )

                results.append(record)

        except Exception as e:
            self.logger.warning(f"Error scraping article {url}: {e}")

        return results

    def _is_scam_related(self, text: str) -> bool:
        """
        Check if text is scam/fraud related.

        Args:
            text: Text to check

        Returns:
            True if scam-related
        """
        scam_keywords = [
            'scam', 'fraud', 'phishing', 'deceptive', 'fake',
            'imposter', 'robocall', 'identity theft', 'data breach',
            'malware', 'ransomware', 'cryptocurrency scam', 'ponzi',
            'pyramid scheme', 'misleading', 'defrauded', 'swindl'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in scam_keywords)

    def _classify_scam_from_text(self, text: str) -> str:
        """Classify scam type from text content."""
        text_lower = text.lower()

        scam_types = {
            'phishing': ['phish', 'credential', 'login', 'password'],
            'identity_theft': ['identity theft', 'ssn', 'social security', 'personal information'],
            'financial': ['money', 'payment', 'bank', 'wire transfer', 'credit card'],
            'crypto': ['cryptocurrency', 'bitcoin', 'crypto', 'nft', 'blockchain'],
            'tech_support': ['tech support', 'microsoft', 'apple', 'virus', 'malware'],
            'romance': ['romance scam', 'dating', 'lonely'],
            'job': ['job scam', 'employment', 'work from home', 'pyramid'],
            'robocall': ['robocall', 'spoofing', 'caller id'],
            'shopping': ['fake product', 'counterfeit', 'online shopping']
        }

        for scam_type, keywords in scam_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return scam_type

        return 'fraud'

    def _find_context_around_url(self, text: str, search_term: str, window: int = 200) -> str:
        """
        Find text context around a URL or domain mention.

        Args:
            text: Full text
            search_term: URL or domain to find
            window: Characters before/after to include

        Returns:
            Context string
        """
        try:
            # Find position of search term
            pos = text.lower().find(search_term.lower())

            if pos == -1:
                return text[:500]  # Return beginning if not found

            # Extract context window
            start = max(0, pos - window)
            end = min(len(text), pos + len(search_term) + window)

            context = text[start:end].strip()

            # Add ellipsis if truncated
            if start > 0:
                context = '...' + context
            if end < len(text):
                context = context + '...'

            return context

        except:
            return text[:500]
