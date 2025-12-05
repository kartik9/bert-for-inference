"""
Scrape URLs from public threat intelligence sources.
"""
import requests
import json
import logging
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def scrape_urlhaus():
    """Scrape recent malicious URLs from URLhaus (abuse.ch)."""
    logger.info("Scraping URLhaus for recent malicious URLs...")

    urls_found = []

    try:
        # URLhaus recent URLs endpoint
        api_url = "https://urlhaus-api.abuse.ch/v1/urls/recent/"

        response = requests.post(api_url, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data.get('query_status') == 'ok':
            urls_data = data.get('urls', [])
            logger.info(f"Found {len(urls_data)} recent URLs from URLhaus")

            for url_info in urls_data[:30]:  # Limit to 30
                try:
                    url = url_info.get('url', '')
                    if not url:
                        continue

                    urls_found.append({
                        'url': url,
                        'source': 'urlhaus',
                        'threat': url_info.get('threat', 'unknown'),
                        'tags': url_info.get('tags', []),
                        'date_added': url_info.get('date_added', ''),
                        'url_status': url_info.get('url_status', ''),
                        'reporter': url_info.get('reporter', ''),
                        'source_url': f"https://urlhaus.abuse.ch/url/{url_info.get('id', '')}"
                    })

                    logger.info(f"  ✓ {url[:80]} ({url_info.get('threat', 'unknown')})")

                except Exception as e:
                    logger.warning(f"Error processing URL: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error scraping URLhaus: {e}", exc_info=True)

    return urls_found

def scrape_openphish():
    """Scrape from OpenPhish feed."""
    logger.info("\nScraping OpenPhish for phishing URLs...")

    urls_found = []

    try:
        # OpenPhish feed
        feed_url = "https://openphish.com/feed.txt"

        response = requests.get(feed_url, timeout=30)
        response.raise_for_status()

        urls = response.text.strip().split('\n')
        logger.info(f"Found {len(urls)} URLs from OpenPhish feed")

        for url in urls[:25]:  # Limit to 25
            url = url.strip()
            if url and url.startswith('http'):
                urls_found.append({
                    'url': url,
                    'source': 'openphish',
                    'threat': 'phishing',
                    'date_added': datetime.now().isoformat(),
                    'source_url': 'https://openphish.com/'
                })

                logger.info(f"  ✓ {url[:80]}")

    except Exception as e:
        logger.error(f"Error scraping OpenPhish: {e}", exc_info=True)

    return urls_found

def scrape_phishtank_api():
    """Scrape from PhishTank API."""
    logger.info("\nAttempting to scrape PhishTank...")

    urls_found = []

    try:
        # PhishTank requires API key, but we can try the public data
        # Note: This endpoint may require authentication
        api_url = "http://data.phishtank.com/data/online-valid.json"

        logger.info("Fetching PhishTank data (this may take a moment)...")
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Found {len(data)} phishing URLs from PhishTank")

        for item in data[:20]:  # Limit to 20
            try:
                url = item.get('url', '')
                if url:
                    urls_found.append({
                        'url': url,
                        'source': 'phishtank',
                        'threat': 'phishing',
                        'phish_id': item.get('phish_id', ''),
                        'date_added': item.get('submission_time', ''),
                        'verified': item.get('verified', False),
                        'source_url': item.get('phish_detail_url', '')
                    })

                    logger.info(f"  ✓ {url[:80]}")

            except Exception as e:
                logger.warning(f"Error processing PhishTank entry: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scraping PhishTank: {e}")

    return urls_found

def main():
    """Main function."""
    logger.info("=" * 70)
    logger.info("Public Threat Intelligence URL Scraper")
    logger.info("=" * 70)
    logger.info("")

    all_urls = []

    # Scrape URLhaus
    try:
        urlhaus_urls = scrape_urlhaus()
        all_urls.extend(urlhaus_urls)
        time.sleep(2)
    except Exception as e:
        logger.error(f"URLhaus failed: {e}")

    # Scrape OpenPhish
    try:
        openphish_urls = scrape_openphish()
        all_urls.extend(openphish_urls)
        time.sleep(2)
    except Exception as e:
        logger.error(f"OpenPhish failed: {e}")

    # Try PhishTank
    try:
        phishtank_urls = scrape_phishtank_api()
        all_urls.extend(phishtank_urls)
    except Exception as e:
        logger.error(f"PhishTank failed: {e}")

    logger.info("\n" + "=" * 70)
    logger.info(f"Collection Complete - Found {len(all_urls)} URLs")
    logger.info("=" * 70)

    if all_urls:
        logger.info("\n📊 Summary by Source:")
        sources = {}
        for url_data in all_urls:
            source = url_data.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        for source, count in sources.items():
            logger.info(f"  {source}: {count} URLs")

        logger.info("\n" + "=" * 70)
        logger.info(f"First 20 URLs:\n")
        logger.info("=" * 70)

        for i, url_data in enumerate(all_urls[:20], 1):
            logger.info(f"\n{i}. {url_data['url']}")
            logger.info(f"   Source: {url_data['source']}")
            logger.info(f"   Threat: {url_data.get('threat', 'unknown')}")
            if url_data.get('tags'):
                logger.info(f"   Tags: {', '.join(url_data['tags'])}")

        # Save to file
        import os
        os.makedirs('scam_url_collector/data', exist_ok=True)

        output_file = 'scam_url_collector/data/threat_intel_urls.json'
        with open(output_file, 'w') as f:
            json.dump({
                'collection_date': datetime.now().isoformat(),
                'total_urls': len(all_urls),
                'sources': sources,
                'urls': all_urls
            }, f, indent=2)

        logger.info(f"\n✅ Results saved to {output_file}")
        logger.info(f"✅ Total URLs collected: {len(all_urls)}")

    else:
        logger.warning("⚠️  No URLs collected")

if __name__ == '__main__':
    main()
