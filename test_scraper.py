"""
Simple test script to run FTC scraper.
"""
import sys
import os

# Add scam_url_collector to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scam_url_collector'))

import logging
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def extract_urls_from_text(text):
    """Extract URLs from text."""
    import re
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.findall(text)

def scrape_ftc_alerts():
    """Scrape FTC consumer alerts."""
    logger.info("Scraping FTC Consumer Alerts...")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    urls_found = []

    try:
        # Scrape consumer alerts
        url = "https://consumer.ftc.gov/consumer-alerts"
        logger.info(f"Fetching {url}")

        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find article links
        articles = soup.find_all('article')[:10] or soup.find_all('div', class_='views-row')[:10]

        logger.info(f"Found {len(articles)} articles")

        for article in articles:
            try:
                link_elem = article.find('a', href=True)
                if not link_elem:
                    continue

                article_url = link_elem['href']
                if not article_url.startswith('http'):
                    article_url = f"https://consumer.ftc.gov{article_url}"

                title = link_elem.get_text(strip=True)

                # Check if scam-related
                scam_keywords = ['scam', 'fraud', 'phishing', 'fake', 'imposter']
                if not any(k in title.lower() for k in scam_keywords):
                    continue

                logger.info(f"  Processing: {title[:60]}...")

                # Fetch article
                try:
                    article_response = session.get(article_url, timeout=10)
                    article_response.raise_for_status()

                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    content_elem = article_soup.find('article') or article_soup.find('main')

                    if content_elem:
                        content_text = content_elem.get_text(separator=' ', strip=True)

                        # Extract URLs
                        found_urls = extract_urls_from_text(content_text)

                        # Filter out FTC and common sites
                        filtered_urls = [
                            u for u in found_urls
                            if 'ftc.gov' not in u.lower()
                            and 'youtube.com' not in u.lower()
                            and 'twitter.com' not in u.lower()
                            and 'facebook.com' not in u.lower()
                        ]

                        for found_url in filtered_urls:
                            urls_found.append({
                                'url': found_url,
                                'source': 'ftc',
                                'source_url': article_url,
                                'title': title,
                                'date': datetime.now().isoformat()
                            })
                            logger.info(f"    ✓ Found URL: {found_url}")

                    import time
                    time.sleep(2)  # Rate limiting

                except Exception as e:
                    logger.warning(f"    Error processing article: {e}")
                    continue

            except Exception as e:
                logger.warning(f"  Error processing article link: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping FTC: {e}", exc_info=True)

    return urls_found

def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("FTC Scam URL Scraper Test")
    logger.info("=" * 60)

    urls = scrape_ftc_alerts()

    logger.info("\n" + "=" * 60)
    logger.info(f"Collection Complete - Found {len(urls)} URLs")
    logger.info("=" * 60)

    if urls:
        logger.info("\nCollected URLs:\n")
        for i, url_data in enumerate(urls, 1):
            logger.info(f"{i}. {url_data['url']}")
            logger.info(f"   Source: {url_data['title'][:80]}")
            logger.info(f"   Article: {url_data['source_url']}\n")

    # Save to file
    if urls:
        import json
        os.makedirs('scam_url_collector/data', exist_ok=True)
        with open('scam_url_collector/data/ftc_test_results.json', 'w') as f:
            json.dump({
                'collection_date': datetime.now().isoformat(),
                'total_urls': len(urls),
                'urls': urls
            }, f, indent=2)

        logger.info(f"✓ Results saved to scam_url_collector/data/ftc_test_results.json")

if __name__ == '__main__':
    main()
