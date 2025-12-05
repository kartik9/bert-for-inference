"""
BBB (Better Business Bureau) Scam Tracker scraper.
Uses Playwright for JavaScript-rendered content.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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


class BBBScraper(BaseScraper):
    """Scraper for BBB Scam Tracker."""

    BBB_SCAM_TRACKER_URL = "https://www.bbb.org/scamtracker/us/"

    def __init__(self, headless: bool = None):
        """
        Initialize BBB scraper.

        Args:
            headless: Run browser in headless mode (default from config)
        """
        super().__init__(rate_limit_delay=Config.SLEEP_BETWEEN_REQUESTS)

        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Install with: pip install playwright && playwright install")

        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup not installed, HTML parsing may be limited")

        self.headless = headless if headless is not None else Config.HEADLESS_BROWSER
        self.browser_type = Config.BROWSER_TYPE

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape scam reports from BBB Scam Tracker.

        Returns:
            List of URL records
        """
        all_results = []

        try:
            with sync_playwright() as p:
                # Launch browser
                if self.browser_type == 'firefox':
                    browser = p.firefox.launch(headless=self.headless)
                elif self.browser_type == 'webkit':
                    browser = p.webkit.launch(headless=self.headless)
                else:  # chromium (default)
                    browser = p.chromium.launch(headless=self.headless)

                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                self.logger.info("Scraping BBB Scam Tracker")

                # Scrape reports
                results = self.scrape_reports(page, pages=Config.BBB_PAGES_TO_SCRAPE)
                all_results.extend(results)

                browser.close()

        except Exception as e:
            self.logger.error(f"Error during BBB scraping: {e}", exc_info=True)

        self.logger.info(f"BBB scraping complete. Found {len(all_results)} URL records")
        return all_results

    def scrape_reports(self, page, pages: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape scam reports from BBB.

        Args:
            page: Playwright page object
            pages: Number of pages to scrape

        Returns:
            List of URL records
        """
        results = []

        try:
            # Navigate to scam tracker
            self.logger.info(f"Navigating to {self.BBB_SCAM_TRACKER_URL}")
            page.goto(self.BBB_SCAM_TRACKER_URL, timeout=30000)

            # Wait for content to load
            try:
                page.wait_for_selector('.bbb-result-card, .report-card, article', timeout=10000)
            except PlaywrightTimeout:
                self.logger.warning("Timeout waiting for report cards, trying to parse anyway")

            # Scrape multiple pages
            for page_num in range(pages):
                self.logger.info(f"Scraping BBB page {page_num + 1}/{pages}")

                # Get page content
                content = page.content()

                # Parse reports from current page
                page_results = self._parse_reports_from_html(content)
                results.extend(page_results)

                self.logger.info(f"Found {len(page_results)} URLs on page {page_num + 1}")

                # Try to click "Next" or "Load More" button
                if page_num < pages - 1:
                    try:
                        # Look for various pagination elements
                        next_button = page.locator('button:has-text("Load More"), button:has-text("Next"), a:has-text("Next")').first

                        if next_button.is_visible(timeout=2000):
                            next_button.click()
                            # Wait for new content to load
                            time.sleep(2)
                            page.wait_for_load_state('networkidle', timeout=10000)
                        else:
                            self.logger.info("No more pages available")
                            break

                    except Exception as e:
                        self.logger.warning(f"Could not navigate to next page: {e}")
                        break

                self.rate_limit()

        except Exception as e:
            self.logger.error(f"Error scraping BBB reports: {e}", exc_info=True)

        return results

    def _parse_reports_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse scam reports from HTML content.

        Args:
            html_content: HTML content to parse

        Returns:
            List of URL records
        """
        results = []

        if not BS4_AVAILABLE:
            self.logger.warning("BeautifulSoup not available, cannot parse HTML")
            return results

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find report cards (BBB structure may vary)
            # Try multiple selectors
            report_cards = (
                soup.find_all('div', class_='bbb-result-card') or
                soup.find_all('article') or
                soup.find_all('div', class_='report-card') or
                soup.find_all('div', class_='scam-report')
            )

            self.logger.debug(f"Found {len(report_cards)} report cards")

            for card in report_cards:
                try:
                    report_data = self._extract_report_data(card)

                    if report_data:
                        # Extract URLs from description
                        description = report_data.get('description', '')
                        urls = URLExtractor.extract_urls(description, include_bare_domains=True)

                        for url in urls:
                            cleaned_url = URLExtractor.clean_url(url)

                            if not URLExtractor.validate_url(cleaned_url):
                                continue

                            # Expand shortened URLs
                            if URLExtractor.is_url_shortener(cleaned_url):
                                expanded = URLExtractor.expand_shortened_url(cleaned_url)
                                if expanded:
                                    cleaned_url = expanded

                            # Create record
                            record = self.create_record(
                                url=cleaned_url,
                                source='bbb',
                                source_id=report_data.get('id', ''),
                                source_url=report_data.get('url', self.BBB_SCAM_TRACKER_URL),
                                context=description[:500],
                                scam_type=report_data.get('scam_type', 'unknown'),
                                date_posted=report_data.get('date'),
                                metadata={
                                    'title': report_data.get('title', ''),
                                    'location': report_data.get('location', ''),
                                    'category': report_data.get('scam_type', ''),
                                    'similar_reports': report_data.get('similar_count', 0)
                                }
                            )

                            results.append(record)

                except Exception as e:
                    self.logger.debug(f"Error parsing report card: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}", exc_info=True)

        return results

    def _extract_report_data(self, card_element) -> Dict[str, Any]:
        """
        Extract data from a report card element.

        Args:
            card_element: BeautifulSoup element

        Returns:
            Dictionary of report data
        """
        try:
            report_data = {}

            # Extract title
            title_elem = (
                card_element.find('h3') or
                card_element.find('h2') or
                card_element.find(class_='title')
            )
            report_data['title'] = title_elem.get_text(strip=True) if title_elem else 'Unknown'

            # Extract scam type/category
            category_elem = (
                card_element.find(class_='category') or
                card_element.find(class_='scam-type') or
                card_element.find('span', class_='type')
            )
            scam_type = category_elem.get_text(strip=True) if category_elem else 'unknown'
            report_data['scam_type'] = self._normalize_scam_type(scam_type)

            # Extract description
            desc_elem = (
                card_element.find(class_='description') or
                card_element.find(class_='details') or
                card_element.find('p')
            )
            report_data['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

            # Extract date
            date_elem = (
                card_element.find(class_='date') or
                card_element.find('time') or
                card_element.find(class_='reported-date')
            )

            if date_elem:
                date_str = date_elem.get_text(strip=True)
                report_data['date'] = self._parse_date(date_str)
            else:
                report_data['date'] = datetime.now()

            # Extract location
            location_elem = (
                card_element.find(class_='location') or
                card_element.find(class_='city-state')
            )
            report_data['location'] = location_elem.get_text(strip=True) if location_elem else 'Unknown'

            # Try to extract report ID from data attributes or links
            report_link = card_element.find('a', href=True)
            if report_link:
                href = report_link['href']
                report_data['url'] = href if href.startswith('http') else f"https://www.bbb.org{href}"
                # Extract ID from URL
                import re
                id_match = re.search(r'/(\d+)/?$', href)
                report_data['id'] = id_match.group(1) if id_match else ''
            else:
                report_data['id'] = ''
                report_data['url'] = self.BBB_SCAM_TRACKER_URL

            # Extract similar reports count if available
            similar_elem = card_element.find(class_='similar-reports')
            if similar_elem:
                try:
                    import re
                    count_match = re.search(r'(\d+)', similar_elem.get_text())
                    report_data['similar_count'] = int(count_match.group(1)) if count_match else 0
                except:
                    report_data['similar_count'] = 0
            else:
                report_data['similar_count'] = 0

            return report_data

        except Exception as e:
            self.logger.debug(f"Error extracting report data: {e}")
            return {}

    def _normalize_scam_type(self, scam_type: str) -> str:
        """Normalize scam type to standard categories."""
        scam_type_lower = scam_type.lower()

        type_mapping = {
            'phishing': 'phishing',
            'identity theft': 'identity_theft',
            'financial': 'financial',
            'investment': 'financial',
            'employment': 'job',
            'tech support': 'tech_support',
            'online shopping': 'shopping',
            'romance': 'romance',
            'cryptocurrency': 'crypto',
            'advance fee': 'financial',
            'lottery': 'financial'
        }

        for key, value in type_mapping.items():
            if key in scam_type_lower:
                return value

        return scam_type_lower if scam_type_lower else 'unknown'

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string

        Returns:
            datetime object
        """
        try:
            # Try various date formats
            from dateutil import parser
            return parser.parse(date_str)
        except:
            try:
                # Common formats
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
            except:
                pass

        # Default to now if parsing fails
        return datetime.now()
