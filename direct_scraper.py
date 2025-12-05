"""
Direct scraper using Playwright for BBB and requests for Reddit public pages.
"""
import json
import os
import re
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_urls_from_text(text):
    """Extract URLs from text."""
    url_pattern = re.compile(r'http[s]?://[^\s<>"{}|\\^`\[\]]+')
    urls = url_pattern.findall(text)

    # Also find bare domains
    domain_pattern = re.compile(r'\b([a-z0-9][a-z0-9-]{0,61}[a-z0-9]?\.[a-z]{2,}\b(?:/\S*)?)', re.IGNORECASE)
    domains = domain_pattern.findall(text)

    for domain in domains:
        if not any(domain.lower() in u.lower() for u in urls):
            urls.append(f'http://{domain}')

    return urls

def is_valid_scam_url(url):
    """Check if URL is valid and not from common sites."""
    url_lower = url.lower()
    exclude = ['reddit.com', 'twitter.com', 'x.com', 'youtube.com', 'facebook.com',
               'bbb.org', 'ftc.gov', 't.co', 'bit.ly', 'imgur.com', 'giphy.com']

    for excluded in exclude:
        if excluded in url_lower:
            return False

    # Must have a domain
    if '.' not in url:
        return False

    return True

def scrape_reddit_scams():
    """Scrape r/Scams subreddit."""
    logger.info("=" * 70)
    logger.info("Scraping r/Scams from Reddit...")
    logger.info("=" * 70)

    urls_found = []

    try:
        # Use old.reddit.com for easier scraping
        reddit_url = "https://old.reddit.com/r/Scams/new/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(reddit_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all posts
        posts = soup.find_all('div', class_='thing', limit=25)
        logger.info(f"Found {len(posts)} posts on r/Scams")

        for post in posts:
            try:
                # Get title
                title_elem = post.find('a', class_='title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                post_url = title_elem['href']
                if not post_url.startswith('http'):
                    post_url = f"https://old.reddit.com{post_url}"

                # Get post body if available
                expando = post.find('div', class_='expando')
                body_text = expando.get_text(strip=True) if expando else ''

                full_text = f"{title} {body_text}"

                # Extract URLs
                found_urls = extract_urls_from_text(full_text)

                for url in found_urls:
                    if is_valid_scam_url(url):
                        urls_found.append({
                            'url': url,
                            'source': 'reddit',
                            'subreddit': 'r/Scams',
                            'post_title': title[:150],
                            'post_url': post_url,
                            'context': full_text[:300],
                            'date': datetime.now().isoformat()
                        })
                        logger.info(f"  ✓ Found: {url}")
                        logger.info(f"     From: {title[:60]}...")

            except Exception as e:
                logger.debug(f"Error processing post: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping Reddit: {e}")

    logger.info(f"✅ Reddit: Found {len(urls_found)} URLs")
    return urls_found

def scrape_bbb_with_playwright():
    """Scrape BBB Scam Tracker using Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright not available")
        return []

    logger.info("\n" + "=" * 70)
    logger.info("Scraping BBB Scam Tracker with Playwright...")
    logger.info("=" * 70)

    urls_found = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            bbb_url = "https://www.bbb.org/scamtracker/us/"
            logger.info(f"Loading {bbb_url}")

            page.goto(bbb_url, wait_until='networkidle', timeout=60000)
            time.sleep(5)  # Wait for JS to load

            # Get all text content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Try to find scam reports
            # Look for any divs that might contain reports
            all_text_elements = soup.find_all(['p', 'div', 'span'])

            logger.info(f"Analyzing {len(all_text_elements)} elements...")

            scam_keywords = ['scam', 'fraud', 'phishing', 'fake', 'suspicious']

            for elem in all_text_elements:
                text = elem.get_text(strip=True)

                # Check if text mentions scams
                if any(keyword in text.lower() for keyword in scam_keywords) and len(text) > 50:
                    # Extract URLs
                    found_urls = extract_urls_from_text(text)

                    for url in found_urls:
                        if is_valid_scam_url(url):
                            urls_found.append({
                                'url': url,
                                'source': 'bbb',
                                'context': text[:250],
                                'date': datetime.now().isoformat()
                            })
                            logger.info(f"  ✓ Found: {url}")

            browser.close()

    except Exception as e:
        logger.error(f"Error scraping BBB: {e}", exc_info=True)

    logger.info(f"✅ BBB: Found {len(urls_found)} URLs")
    return urls_found

def scrape_r_phishing():
    """Scrape r/phishing subreddit."""
    logger.info("\n" + "=" * 70)
    logger.info("Scraping r/phishing from Reddit...")
    logger.info("=" * 70)

    urls_found = []

    try:
        reddit_url = "https://old.reddit.com/r/phishing/new/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(reddit_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        posts = soup.find_all('div', class_='thing', limit=25)
        logger.info(f"Found {len(posts)} posts on r/phishing")

        for post in posts:
            try:
                title_elem = post.find('a', class_='title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                post_url = title_elem['href']
                if not post_url.startswith('http'):
                    post_url = f"https://old.reddit.com{post_url}"

                expando = post.find('div', class_='expando')
                body_text = expando.get_text(strip=True) if expando else ''

                full_text = f"{title} {body_text}"

                found_urls = extract_urls_from_text(full_text)

                for url in found_urls:
                    if is_valid_scam_url(url):
                        urls_found.append({
                            'url': url,
                            'source': 'reddit',
                            'subreddit': 'r/phishing',
                            'post_title': title[:150],
                            'post_url': post_url,
                            'context': full_text[:300],
                            'date': datetime.now().isoformat()
                        })
                        logger.info(f"  ✓ Found: {url}")

            except Exception as e:
                logger.debug(f"Error processing post: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping r/phishing: {e}")

    logger.info(f"✅ r/phishing: Found {len(urls_found)} URLs")
    return urls_found

def main():
    logger.info("\n" + "=" * 70)
    logger.info("DIRECT REAL SCAM URL SCRAPER")
    logger.info("=" * 70)

    all_urls = []

    # Scrape Reddit r/Scams
    scams_urls = scrape_reddit_scams()
    all_urls.extend(scams_urls)
    time.sleep(2)

    # Scrape Reddit r/phishing
    phishing_urls = scrape_r_phishing()
    all_urls.extend(phishing_urls)
    time.sleep(2)

    # Scrape BBB
    bbb_urls = scrape_bbb_with_playwright()
    all_urls.extend(bbb_urls)

    # Remove duplicates
    seen = set()
    unique_urls = []
    for url_data in all_urls:
        url_key = url_data['url'].lower()
        if url_key not in seen:
            seen.add(url_key)
            unique_urls.append(url_data)

    logger.info("\n" + "=" * 70)
    logger.info("COLLECTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total unique URLs: {len(unique_urls)}")
    logger.info(f"  Reddit r/Scams: {len(scams_urls)}")
    logger.info(f"  Reddit r/phishing: {len(phishing_urls)}")
    logger.info(f"  BBB: {len(bbb_urls)}")

    if unique_urls:
        logger.info("\n" + "=" * 70)
        logger.info("COLLECTED SCAM URLs:")
        logger.info("=" * 70)

        for i, url_data in enumerate(unique_urls, 1):
            logger.info(f"\n{i}. {url_data['url']}")
            logger.info(f"   Source: {url_data['source']}")
            if 'subreddit' in url_data:
                logger.info(f"   Subreddit: {url_data['subreddit']}")
                logger.info(f"   Post: {url_data['post_title'][:80]}")
            logger.info(f"   Context: {url_data['context'][:100]}...")

        # Save results
        os.makedirs('scam_url_collector/data', exist_ok=True)
        output_file = 'scam_url_collector/data/real_scam_urls.json'

        with open(output_file, 'w') as f:
            json.dump({
                'collection_date': datetime.now().isoformat(),
                'total_urls': len(unique_urls),
                'sources': {
                    'reddit_scams': len(scams_urls),
                    'reddit_phishing': len(phishing_urls),
                    'bbb': len(bbb_urls)
                },
                'urls': unique_urls
            }, f, indent=2)

        logger.info(f"\n✅ Results saved to {output_file}")
    else:
        logger.warning("⚠️  No URLs collected")

if __name__ == '__main__':
    main()
