"""
Web Scraper
Fetches and extracts content from web pages
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import html2text
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class ArticleContent:
    """Extracted article content"""
    url: str
    title: str
    content: str  # Main text content
    html: str  # Raw HTML
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    fetch_time: datetime = None

    def __post_init__(self):
        if self.fetch_time is None:
            self.fetch_time = datetime.now()


class WebScraper:
    """Web scraper for fetching article content"""

    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 (compatible; TSNewsBot/1.0)",
        timeout: int = 30,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize web scraper

        Args:
            user_agent: User agent string for requests
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests (seconds)
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

        # HTML to text converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def fetch_url(self, url: str) -> Optional[ArticleContent]:
        """
        Fetch and extract content from a URL

        Args:
            url: URL to fetch

        Returns:
            ArticleContent object or None if fetch fails
        """
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        try:
            # Make request
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string
            elif soup.find('h1'):
                title = soup.find('h1').get_text()

            # Extract author (common meta tags)
            author = None
            author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                         soup.find('meta', attrs={'property': 'article:author'})
            if author_meta:
                author = author_meta.get('content')

            # Extract published date (common meta tags)
            published_date = None
            date_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                       soup.find('meta', attrs={'name': 'publication_date'}) or \
                       soup.find('meta', attrs={'name': 'date'})
            if date_meta:
                date_str = date_meta.get('content')
                try:
                    from dateutil import parser
                    published_date = parser.parse(date_str)
                except:
                    pass

            # Extract main content
            # Try to find article body using common selectors
            content_html = None

            # Try semantic HTML5 elements
            article_tag = soup.find('article')
            if article_tag:
                content_html = article_tag

            # Try common content class names
            if not content_html:
                for selector in [
                    {'class': 'article-content'},
                    {'class': 'post-content'},
                    {'class': 'entry-content'},
                    {'class': 'content'},
                    {'id': 'article-body'},
                    {'id': 'content'}
                ]:
                    content_html = soup.find('div', selector)
                    if content_html:
                        break

            # Fallback: use entire body
            if not content_html:
                content_html = soup.find('body')

            # Remove unwanted elements
            if content_html:
                for tag in content_html.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    tag.decompose()

            # Convert to text
            content_text = ""
            if content_html:
                content_text = self.h2t.handle(str(content_html))

            # Clean up text
            content_text = content_text.strip()

            return ArticleContent(
                url=url,
                title=title,
                content=content_text,
                html=response.text,
                author=author,
                published_date=published_date
            )

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error fetching {url}: {e}")
            return None

        except requests.exceptions.Timeout:
            print(f"Timeout fetching {url}")
            return None

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

        finally:
            self._last_request_time = time.time()

    def extract_metadata(self, url: str) -> dict:
        """
        Extract only metadata from a URL without full content

        Args:
            url: URL to analyze

        Returns:
            Dictionary with metadata
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.head(url, headers=headers, timeout=10)

            return {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type"),
                "content_length": response.headers.get("content-length"),
                "last_modified": response.headers.get("last-modified")
            }

        except Exception as e:
            return {
                "url": url,
                "error": str(e)
            }


# Example usage:
if __name__ == "__main__":
    scraper = WebScraper()

    # Fetch article
    article = scraper.fetch_url("https://krebsonsecurity.com/")

    if article:
        print(f"Title: {article.title}")
        print(f"Author: {article.author}")
        print(f"Published: {article.published_date}")
        print(f"Content length: {len(article.content)} chars")
        print(f"\nFirst 500 chars:\n{article.content[:500]}")
