"""
Improved PhishTank scraper that extracts actual phishing URLs.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
import time
import re


class ImprovedPhishTankScraper:
    """Scrape PhishTank for actual phishing target URLs."""

    def __init__(self):
        self.search_url = "https://phishtank.org/phish_search.php?valid=y&active=y&Search=Search"
        self.base_url = "https://phishtank.org/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_phish_detail(self, phish_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific phish."""
        detail_url = f"{self.base_url}phish_detail.php?phish_id={phish_id}"

        try:
            response = requests.get(detail_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for the phishing URL in the detail page
            # PhishTank typically displays the URL prominently
            url = None
            target = None
            submitted_date = None

            # Method 1: Look for URL in table cells or divs with specific labels
            for element in soup.find_all(['td', 'div', 'span']):
                text = element.get_text(strip=True)

                # Look for "Phish URL:" or similar labels
                if 'URL' in text or 'url' in text.lower():
                    # Check siblings or next elements for the actual URL
                    next_elem = element.find_next()
                    if next_elem:
                        potential_url = next_elem.get_text(strip=True)
                        if potential_url.startswith('http'):
                            url = potential_url
                            break

            # Method 2: Look for links that might be the phishing URL
            if not url:
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    # Skip PhishTank internal links
                    if href.startswith('http') and 'phishtank.org' not in href:
                        url = href
                        break

            # Method 3: Look in the page source for URL patterns
            if not url:
                page_text = soup.get_text()
                # Find URLs in the text
                url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
                urls_found = re.findall(url_pattern, page_text)
                for found_url in urls_found:
                    if 'phishtank.org' not in found_url:
                        url = found_url if found_url.startswith('http') else f"http://{found_url}"
                        break

            return {
                "url": url,
                "phish_id": phish_id,
                "target": target,
                "submitted_date": submitted_date,
            }

        except Exception as e:
            print(f"   Error fetching phish {phish_id}: {e}")
            return {"url": None, "phish_id": phish_id}

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Scrape active phishing URLs from PhishTank."""
        print(f"[PhishTank Scraper] Fetching {count} active phishing URLs...")
        print(f"[PhishTank Scraper] Step 1: Getting list of recent phish IDs...")

        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract phish IDs from the search results
            phish_ids = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'phish_detail.php?phish_id=' in href:
                    phish_id = href.split('phish_id=')[-1]
                    if phish_id not in phish_ids:
                        phish_ids.append(phish_id)

            print(f"[PhishTank Scraper] Found {len(phish_ids)} phish IDs")

            if len(phish_ids) == 0:
                print("[PhishTank Scraper] No phish IDs found. Saving HTML for debugging...")
                with open("phishtank_debug.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("HTML saved to phishtank_debug.html")
                return []

            print(f"[PhishTank Scraper] Step 2: Fetching details for {min(count, len(phish_ids))} phishing URLs...")

            results = []
            for i, phish_id in enumerate(phish_ids[:count * 2], 1):  # Fetch more in case some fail
                print(f"   Fetching {i}/{min(count * 2, len(phish_ids))}: phish_id={phish_id}")

                detail = self.get_phish_detail(phish_id)

                if detail['url']:
                    results.append({
                        "url": detail['url'],
                        "phish_id": phish_id,
                        "source": "phishtank_scrape",
                        "verified": True,
                        "active": True,
                        "target": detail.get('target'),
                        "submitted_date": detail.get('submitted_date'),
                    })

                    print(f"   ✓ Got URL: {detail['url'][:80]}...")

                    if len(results) >= count:
                        break

                # Be nice to the server
                time.sleep(1)

            print(f"\n[PhishTank Scraper] Successfully scraped {len(results)} phishing URLs")
            return results

        except Exception as e:
            print(f"[PhishTank Scraper] Error: {e}")
            import traceback
            traceback.print_exc()
            return []


def main():
    """Test improved PhishTank scraper."""
    print("=" * 100)
    print("PhishTank Active Phishing URLs - Improved Web Scraping")
    print("=" * 100)
    print()

    scraper = ImprovedPhishTankScraper()
    phishing_urls = scraper.fetch(count=5)

    if phishing_urls:
        print("\n\n" + "=" * 100)
        print(f"Successfully scraped {len(phishing_urls)} phishing URLs:")
        print("=" * 100)

        for i, entry in enumerate(phishing_urls, 1):
            print(f"\n{i}. URL: {entry['url']}")
            print(f"   Phish ID: {entry['phish_id']}")
            print(f"   Source: {entry['source']}")
            print(f"   Verified: {entry['verified']}")
            print(f"   Active: {entry['active']}")
            if entry.get('target'):
                print(f"   Target: {entry['target']}")

        # Save to file
        output = {
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source": "phishtank_scrape_improved",
            "count": len(phishing_urls),
            "urls": phishing_urls,
        }

        output_file = "phishtank_scraped_urls.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n\nResults saved to: {output_file}")
    else:
        print("\n[ERROR] No URLs were scraped.")


if __name__ == "__main__":
    main()
