"""
Scrape PhishTank for active phishing URLs.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import json
import time


class PhishTankScraper:
    """Scrape PhishTank web interface for active phishing URLs."""

    def __init__(self):
        self.search_url = "https://phishtank.org/phish_search.php?valid=y&active=y&Search=Search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Scrape active phishing URLs from PhishTank."""
        print(f"[PhishTank Scraper] Fetching {count} active phishing URLs...")
        print(f"[PhishTank Scraper] URL: {self.search_url}")

        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            print(f"[PhishTank Scraper] Response status: {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all phishing entries in the results table
            results = []

            # PhishTank results are typically in a table with class "data"
            # Look for tables that might contain phishing data
            tables = soup.find_all('table')

            print(f"[PhishTank Scraper] Found {len(tables)} tables")

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all('td')

                    # Look for rows with URL data
                    # PhishTank typically has: Phish ID, URL, Submitted, Verified, etc.
                    if len(cells) >= 2:
                        # Try to find URL in cells
                        for cell in cells:
                            links = cell.find_all('a', href=True)
                            for link in links:
                                href = link.get('href', '')
                                text = link.get_text(strip=True)

                                # Check if this looks like a phishing URL
                                # PhishTank links to phish details page
                                if 'phish_detail.php' in href:
                                    # Extract phish ID
                                    phish_id = href.split('phish_id=')[-1] if 'phish_id=' in href else None

                                    # Try to find the actual phishing URL in nearby cells
                                    for potential_url_cell in cells:
                                        url_links = potential_url_cell.find_all('a', href=True)
                                        for url_link in url_links:
                                            potential_url = url_link.get('href', '')
                                            # Skip PhishTank internal links
                                            if potential_url and not potential_url.startswith('/') and 'phishtank.org' not in potential_url:
                                                results.append({
                                                    "url": potential_url,
                                                    "phish_id": phish_id,
                                                    "source": "phishtank_scrape",
                                                    "verified": True,
                                                    "active": True,
                                                })

                                                if len(results) >= count:
                                                    break

                                        if len(results) >= count:
                                            break

                                if len(results) >= count:
                                    break

                            if len(results) >= count:
                                break

                    if len(results) >= count:
                        break

                if len(results) >= count:
                    break

            # If we didn't find URLs in tables, try alternative approach
            # Look for all external links that might be phishing URLs
            if len(results) == 0:
                print("[PhishTank Scraper] No URLs found in tables, trying alternative parsing...")

                all_links = soup.find_all('a', href=True)
                seen_urls = set()

                for link in all_links:
                    url = link.get('href', '')
                    # Skip internal PhishTank links
                    if url and not url.startswith('/') and 'phishtank.org' not in url and url not in seen_urls:
                        # This might be a phishing URL
                        if url.startswith('http'):
                            results.append({
                                "url": url,
                                "source": "phishtank_scrape",
                                "verified": True,
                                "active": True,
                            })
                            seen_urls.add(url)

                            if len(results) >= count:
                                break

            print(f"[PhishTank Scraper] Successfully scraped {len(results)} URLs")

            # Remove duplicates
            unique_results = []
            seen = set()
            for r in results:
                if r['url'] not in seen:
                    unique_results.append(r)
                    seen.add(r['url'])

            return unique_results[:count]

        except Exception as e:
            print(f"[PhishTank Scraper] Error: {e}")
            import traceback
            traceback.print_exc()
            return []


def main():
    """Test PhishTank scraper."""
    print("=" * 100)
    print("PhishTank Active Phishing URLs - Web Scraping")
    print("=" * 100)
    print()

    scraper = PhishTankScraper()
    phishing_urls = scraper.fetch(count=5)

    if phishing_urls:
        print("\n" + "=" * 100)
        print(f"Successfully scraped {len(phishing_urls)} phishing URLs:")
        print("=" * 100)

        for i, entry in enumerate(phishing_urls, 1):
            print(f"\n{i}. URL: {entry['url']}")
            if 'phish_id' in entry and entry['phish_id']:
                print(f"   Phish ID: {entry['phish_id']}")
            print(f"   Source: {entry['source']}")
            print(f"   Verified: {entry['verified']}")
            print(f"   Active: {entry['active']}")

        # Save to file
        output = {
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source": "phishtank_scrape",
            "count": len(phishing_urls),
            "urls": phishing_urls,
        }

        output_file = "phishtank_scraped_urls.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n\nResults saved to: {output_file}")
    else:
        print("\n[ERROR] No URLs were scraped. The page structure may have changed.")
        print("Attempting to save raw HTML for inspection...")

        try:
            response = requests.get(scraper.search_url, headers=scraper.headers, timeout=30)
            with open("phishtank_page.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Raw HTML saved to: phishtank_page.html")

            # Print first 2000 characters for debugging
            print("\n[DEBUG] First 2000 characters of page:")
            print(response.text[:2000])
        except Exception as e:
            print(f"Could not save HTML: {e}")


if __name__ == "__main__":
    main()
