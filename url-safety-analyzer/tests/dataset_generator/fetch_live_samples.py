"""
Live fetcher for malicious URLs from various threat intelligence sources.

This script fetches real malicious URLs to demonstrate the data sources.
"""
import requests
import json
from typing import List, Dict, Any
from datetime import datetime


class PhishTankFetcher:
    """Fetch active phishing URLs from PhishTank."""

    def __init__(self):
        self.api_url = "http://data.phishtank.com/data/online-valid.json"

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent verified phishing URLs."""
        print(f"[PhishTank] Fetching from {self.api_url}...")

        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()

            data = response.json()

            results = []
            for i, entry in enumerate(data[:count]):
                results.append({
                    "url": entry.get("url"),
                    "phish_id": entry.get("phish_id"),
                    "target": entry.get("target", "Unknown"),
                    "verified": entry.get("verified") == "yes",
                    "submission_time": entry.get("submission_time"),
                    "verification_time": entry.get("verification_time"),
                })

            print(f"[PhishTank] Successfully fetched {len(results)} URLs")
            return results

        except Exception as e:
            print(f"[PhishTank] Error: {e}")
            return []


class URLhausFetcher:
    """Fetch malware distribution URLs from URLhaus."""

    def __init__(self):
        self.api_url = "https://urlhaus-api.abuse.ch/v1/urls/recent/"

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent malware URLs."""
        print(f"[URLhaus] Fetching from {self.api_url}...")

        try:
            response = requests.post(self.api_url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("query_status") != "ok":
                print(f"[URLhaus] API returned status: {data.get('query_status')}")
                return []

            results = []
            urls = data.get("urls", [])

            for entry in urls[:count]:
                # Only include online URLs
                if entry.get("url_status") == "online":
                    results.append({
                        "url": entry.get("url"),
                        "urlhaus_id": entry.get("id"),
                        "threat": entry.get("threat"),
                        "tags": entry.get("tags", []),
                        "dateadded": entry.get("dateadded"),
                        "url_status": entry.get("url_status"),
                    })

                    if len(results) >= count:
                        break

            print(f"[URLhaus] Successfully fetched {len(results)} URLs")
            return results

        except Exception as e:
            print(f"[URLhaus] Error: {e}")
            return []


class OpenPhishFetcher:
    """Fetch phishing URLs from OpenPhish feed."""

    def __init__(self):
        self.feed_url = "https://openphish.com/feed.txt"

    def fetch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent phishing URLs."""
        print(f"[OpenPhish] Fetching from {self.feed_url}...")

        try:
            response = requests.get(self.feed_url, timeout=30)
            response.raise_for_status()

            urls = response.text.strip().split('\n')

            results = []
            for url in urls[:count]:
                url = url.strip()
                if url:
                    results.append({
                        "url": url,
                        "source": "openphish",
                        "fetched_at": datetime.utcnow().isoformat() + "Z",
                    })

            print(f"[OpenPhish] Successfully fetched {len(results)} URLs")
            return results

        except Exception as e:
            print(f"[OpenPhish] Error: {e}")
            return []


def main():
    """Fetch examples from all sources."""
    print("=" * 80)
    print("Fetching Live Malicious URLs from Threat Intelligence Sources")
    print("=" * 80)
    print()

    # Fetch from PhishTank
    print("\n--- PhishTank (Active Phishing) ---")
    phishtank = PhishTankFetcher()
    phishtank_urls = phishtank.fetch(5)

    for i, entry in enumerate(phishtank_urls, 1):
        print(f"\n{i}. {entry['url']}")
        print(f"   Phish ID: {entry['phish_id']}")
        print(f"   Target: {entry['target']}")
        print(f"   Verified: {entry['verified']}")
        print(f"   Submitted: {entry['submission_time']}")

    # Fetch from URLhaus
    print("\n\n--- URLhaus (Malware Distribution) ---")
    urlhaus = URLhausFetcher()
    urlhaus_urls = urlhaus.fetch(5)

    for i, entry in enumerate(urlhaus_urls, 1):
        print(f"\n{i}. {entry['url']}")
        print(f"   ID: {entry['urlhaus_id']}")
        print(f"   Threat: {entry['threat']}")
        print(f"   Tags: {', '.join(entry['tags']) if entry['tags'] else 'None'}")
        print(f"   Status: {entry['url_status']}")
        print(f"   Added: {entry['dateadded']}")

    # Fetch from OpenPhish
    print("\n\n--- OpenPhish (Phishing Feed) ---")
    openphish = OpenPhishFetcher()
    openphish_urls = openphish.fetch(5)

    for i, entry in enumerate(openphish_urls, 1):
        print(f"\n{i}. {entry['url']}")
        print(f"   Fetched: {entry['fetched_at']}")

    # Summary
    print("\n\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"PhishTank URLs fetched: {len(phishtank_urls)}")
    print(f"URLhaus URLs fetched: {len(urlhaus_urls)}")
    print(f"OpenPhish URLs fetched: {len(openphish_urls)}")
    print(f"Total malicious URLs: {len(phishtank_urls) + len(urlhaus_urls) + len(openphish_urls)}")

    # Save to JSON
    output = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "phishtank": phishtank_urls,
            "urlhaus": urlhaus_urls,
            "openphish": openphish_urls,
        },
        "summary": {
            "phishtank_count": len(phishtank_urls),
            "urlhaus_count": len(urlhaus_urls),
            "openphish_count": len(openphish_urls),
            "total_count": len(phishtank_urls) + len(urlhaus_urls) + len(openphish_urls),
        }
    }

    output_file = "live_malicious_urls_sample.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
