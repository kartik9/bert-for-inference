"""
Real scraper for Twitter and BBB to collect actual scam URLs.
"""
import sys
import os
import re
import json
import time
import logging
from datetime import datetime, timedelta

# Try importing snscrape
try:
    import snscrape.modules.twitter as sntwitter
    SNSCRAPE_AVAILABLE = True
except ImportError:
    SNSCRAPE_AVAILABLE = False
    print("WARNING: snscrape not available, skipping Twitter")

# Try importing playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: playwright not available, skipping BBB")

from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_urls_from_text(text):
    """Extract URLs from text using regex."""
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = url_pattern.findall(text)

    # Also try to find bare domains
    domain_pattern = re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b', re.IGNORECASE)
    domains = domain_pattern.findall(text)

    for domain in domains:
        if domain not in [u.replace('http://', '').replace('https://', '').split('/')[0] for u in urls]:
            if '.' in domain and not domain.startswith('.'):
                urls.append(f'http://{domain}')

    return urls

def clean_url(url):
    """Clean and validate URL."""
    # Skip common legitimate sites
    exclude_domains = ['twitter.com', 'x.com', 't.co', 'youtube.com', 'facebook.com',
                       'instagram.com', 'reddit.com', 'bbb.org', 'ftc.gov', 'gov',
                       'bit.ly', 'tinyurl.com', 'ow.ly']

    url_lower = url.lower()
    for excluded in exclude_domains:
        if excluded in url_lower:
            return None

    return url

def scrape_twitter_scams():
    """Scrape Twitter for scam-related posts."""
    if not SNSCRAPE_AVAILABLE:
        logger.warning("snscrape not available, skipping Twitter")
        return []

    logger.info("=" * 70)
    logger.info("Scraping Twitter for scam URLs...")
    logger.info("=" * 70)

    urls_found = []

    queries = [
        '"scam website" OR "scam site" OR "phishing link"',
        '"is this a scam" url',
        'suspicious link fraud',
        '"fake website" scam',
        '"got scammed" site'
    ]

    for query in queries:
        try:
            logger.info(f"\nSearching Twitter: {query}")

            # Create scraper with query
            since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            scraper_query = f"{query} since:{since_date} lang:en"

            scraper = sntwitter.TwitterSearchScraper(scraper_query)

            tweet_count = 0
            for tweet in scraper.get_items():
                if tweet_count >= 15:  # Limit per query
                    break

                try:
                    tweet_text = tweet.content if hasattr(tweet, 'content') else tweet.rawContent

                    # Extract URLs from tweet
                    found_urls = extract_urls_from_text(tweet_text)

                    for url in found_urls:
                        cleaned = clean_url(url)
                        if cleaned:
                            urls_found.append({
                                'url': cleaned,
                                'source': 'twitter',
                                'tweet_text': tweet_text[:200],
                                'tweet_url': tweet.url if hasattr(tweet, 'url') else '',
                                'username': tweet.user.username if hasattr(tweet, 'user') else 'unknown',
                                'date': tweet.date.isoformat() if hasattr(tweet, 'date') else datetime.now().isoformat(),
                                'likes': tweet.likeCount if hasattr(tweet, 'likeCount') else 0,
                                'retweets': tweet.retweetCount if hasattr(tweet, 'retweetCount') else 0
                            })
                            logger.info(f"  ✓ Found: {cleaned}")

                    tweet_count += 1

                except Exception as e:
                    logger.debug(f"Error processing tweet: {e}")
                    continue

            time.sleep(2)  # Rate limiting

        except Exception as e:
            logger.error(f"Error with query '{query}': {e}")
            continue

    logger.info(f"\n✅ Twitter: Found {len(urls_found)} URLs")
    return urls_found

def scrape_bbb_scam_tracker():
    """Scrape BBB Scam Tracker for real scam reports."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available, skipping BBB")
        return []

    logger.info("\n" + "=" * 70)
    logger.info("Scraping BBB Scam Tracker...")
    logger.info("=" * 70)

    urls_found = []

    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Navigate to BBB Scam Tracker
            bbb_url = "https://www.bbb.org/scamtracker/us/"
            logger.info(f"Loading {bbb_url}")

            page.goto(bbb_url, timeout=30000)

            # Wait for content to load
            try:
                page.wait_for_selector('article, .report-card, .scam-card', timeout=10000)
            except:
                logger.warning("Timeout waiting for BBB content, trying to parse anyway")

            time.sleep(3)  # Extra wait for dynamic content

            # Get page content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Find scam report cards
            reports = (
                soup.find_all('article', limit=20) or
                soup.find_all('div', class_='report-card', limit=20) or
                soup.find_all('div', class_='scam-card', limit=20)
            )

            logger.info(f"Found {len(reports)} report cards on BBB")

            for report in reports:
                try:
                    # Extract title
                    title_elem = report.find('h3') or report.find('h2') or report.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    # Extract description/details
                    desc_elem = report.find('p') or report.find('div', class_='description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''

                    # Combine text
                    full_text = f"{title} {description}"

                    # Extract scam type
                    category_elem = report.find(class_='category') or report.find(class_='scam-type')
                    scam_type = category_elem.get_text(strip=True) if category_elem else 'unknown'

                    # Extract URLs from text
                    found_urls = extract_urls_from_text(full_text)

                    # Try to get report link
                    report_link_elem = report.find('a', href=True)
                    report_url = ''
                    if report_link_elem:
                        href = report_link_elem['href']
                        report_url = href if href.startswith('http') else f"https://www.bbb.org{href}"

                    for url in found_urls:
                        cleaned = clean_url(url)
                        if cleaned:
                            urls_found.append({
                                'url': cleaned,
                                'source': 'bbb',
                                'title': title[:150],
                                'description': description[:300],
                                'scam_type': scam_type,
                                'report_url': report_url,
                                'date': datetime.now().isoformat()
                            })
                            logger.info(f"  ✓ Found: {cleaned}")
                            logger.info(f"     Type: {scam_type}")

                except Exception as e:
                    logger.debug(f"Error processing BBB report: {e}")
                    continue

            browser.close()

    except Exception as e:
        logger.error(f"Error scraping BBB: {e}", exc_info=True)

    logger.info(f"\n✅ BBB: Found {len(urls_found)} URLs")
    return urls_found

def main():
    """Main execution."""
    logger.info("\n" + "=" * 70)
    logger.info("REAL SCAM URL SCRAPER - Twitter & BBB")
    logger.info("=" * 70)
    logger.info("")

    all_urls = []

    # Scrape Twitter
    twitter_urls = scrape_twitter_scams()
    all_urls.extend(twitter_urls)

    # Scrape BBB
    bbb_urls = scrape_bbb_scam_tracker()
    all_urls.extend(bbb_urls)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("COLLECTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total URLs collected: {len(all_urls)}")
    logger.info(f"  Twitter: {len(twitter_urls)}")
    logger.info(f"  BBB: {len(bbb_urls)}")

    if all_urls:
        # Remove duplicates
        seen = set()
        unique_urls = []
        for url_data in all_urls:
            url_key = url_data['url'].lower()
            if url_key not in seen:
                seen.add(url_key)
                unique_urls.append(url_data)

        logger.info(f"Unique URLs: {len(unique_urls)}")

        # Display results
        logger.info("\n" + "=" * 70)
        logger.info("COLLECTED SCAM URLs:")
        logger.info("=" * 70)

        for i, url_data in enumerate(unique_urls, 1):
            logger.info(f"\n{i}. {url_data['url']}")
            logger.info(f"   Source: {url_data['source']}")

            if url_data['source'] == 'twitter':
                logger.info(f"   Tweet: {url_data['tweet_text'][:100]}...")
                logger.info(f"   By: @{url_data['username']}")
                logger.info(f"   Engagement: {url_data['likes']} likes, {url_data['retweets']} retweets")
            elif url_data['source'] == 'bbb':
                logger.info(f"   Title: {url_data['title'][:100]}")
                logger.info(f"   Type: {url_data['scam_type']}")
                logger.info(f"   Description: {url_data['description'][:100]}...")

        # Save to JSON
        os.makedirs('scam_url_collector/data', exist_ok=True)
        output_file = 'scam_url_collector/data/real_scam_urls.json'

        with open(output_file, 'w') as f:
            json.dump({
                'collection_date': datetime.now().isoformat(),
                'total_urls': len(unique_urls),
                'sources': {
                    'twitter': len(twitter_urls),
                    'bbb': len(bbb_urls)
                },
                'urls': unique_urls
            }, f, indent=2)

        logger.info(f"\n✅ Results saved to {output_file}")
    else:
        logger.warning("⚠️  No URLs collected")

if __name__ == '__main__':
    main()
