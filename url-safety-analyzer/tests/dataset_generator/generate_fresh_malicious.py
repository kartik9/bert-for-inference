"""
Generate fresh malicious URL dataset from live sources only.
Fetch 50 URLs total from URLhaus and Phishing Army, then filter.
"""
import requests
import json
import re
from typing import List, Dict, Any
from collections import defaultdict


def calculate_numeric_percentage(url: str) -> float:
    """Calculate what percentage of URL characters are numeric."""
    url_without_protocol = re.sub(r'^[a-z]+://', '', url, flags=re.IGNORECASE)
    if not url_without_protocol:
        return 0.0
    numeric_count = sum(1 for char in url_without_protocol if char.isdigit())
    total_chars = len(url_without_protocol)
    return (numeric_count / total_chars) * 100


class URLhausFetcher:
    """Fetch malware distribution URLs from URLhaus."""

    def __init__(self):
        self.csv_url = "https://urlhaus.abuse.ch/downloads/csv_recent/"

    def fetch(self, count: int = 30) -> List[Dict[str, Any]]:
        """Fetch recent online malware URLs from CSV feed."""
        print(f"[URLhaus] Fetching {count} malware URLs from CSV feed...")

        try:
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            results = []

            for line in lines:
                # Skip comments and headers
                if line.startswith('#') or line.startswith('id,'):
                    continue

                # Parse CSV: id,dateadded,url,url_status,threat,tags,urlhaus_link,reporter
                parts = line.split(',', 7)
                if len(parts) >= 6:
                    url_id, dateadded, url_str, status, threat, tags = parts[:6]

                    # Only include online URLs
                    if status == '"online"':
                        results.append({
                            "url": url_str.strip('"'),
                            "urlhaus_id": url_id,
                            "threat": threat.strip('"'),
                            "tags": tags.strip('"'),
                            "dateadded": dateadded,
                            "url_status": status.strip('"'),
                            "source": "urlhaus",
                            "category": "malware",
                        })

                        if len(results) >= count:
                            break

            print(f"[URLhaus] Fetched {len(results)} online malware URLs")
            return results

        except Exception as e:
            print(f"[URLhaus] Error: {e}")
            import traceback
            traceback.print_exc()
            return []


class PhishingArmyFetcher:
    """Fetch phishing URLs from Phishing Army."""

    def __init__(self):
        self.feed_url = "https://phishing.army/download/phishing_army_blocklist.txt"

    def fetch(self, count: int = 30) -> List[Dict[str, Any]]:
        """Fetch phishing URLs from blocklist."""
        print(f"[Phishing Army] Fetching {count} phishing URLs...")

        try:
            response = requests.get(self.feed_url, timeout=30)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            results = []

            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue

                url_str = line.strip()
                if url_str:
                    # Ensure URL has protocol
                    if not url_str.startswith('http'):
                        url_str = f"http://{url_str}"

                    results.append({
                        "url": url_str,
                        "source": "phishing_army",
                        "category": "phishing",
                        "type": "phishing",
                    })

                    if len(results) >= count:
                        break

            print(f"[Phishing Army] Fetched {len(results)} phishing URLs")
            return results

        except Exception as e:
            print(f"[Phishing Army] Error: {e}")
            return []


def filter_urls(urls: List[Dict[str, Any]], threshold: float = 75.0) -> tuple:
    """Filter URLs by numeric percentage."""
    kept = []
    filtered = []

    for entry in urls:
        url = entry.get('url', '')
        numeric_pct = calculate_numeric_percentage(url)
        entry['numeric_percentage'] = numeric_pct

        if numeric_pct > threshold:
            entry['filter_reason'] = f"Too many numbers: {numeric_pct:.1f}% numeric"
            filtered.append(entry)
        else:
            kept.append(entry)

    return kept, filtered


def main():
    """Generate fresh malicious URL dataset."""
    print("=" * 100)
    print("FRESH MALICIOUS URL DATASET GENERATION")
    print("=" * 100)
    print("\nFetching from LIVE sources only (no cached URLs):")
    print("  - URLhaus: Malware distribution URLs")
    print("  - Phishing Army: Phishing blocklist")
    print(f"\nTarget: 50 malicious URLs after filtration")
    print("=" * 100)

    # Fetch from both sources
    urlhaus_fetcher = URLhausFetcher()
    phishing_army_fetcher = PhishingArmyFetcher()

    # Fetch more than we need to account for filtering
    print("\n--- FETCHING PHASE ---\n")
    urlhaus_urls = urlhaus_fetcher.fetch(count=30)
    phishing_army_urls = phishing_army_fetcher.fetch(count=30)

    all_urls = urlhaus_urls + phishing_army_urls

    print(f"\n--- FETCH SUMMARY ---")
    print(f"URLhaus: {len(urlhaus_urls)} URLs")
    print(f"Phishing Army: {len(phishing_army_urls)} URLs")
    print(f"Total fetched: {len(all_urls)} URLs")

    # Filter URLs
    print(f"\n\n{'=' * 100}")
    print("FILTERING PHASE (>75% numeric characters)")
    print(f"{'=' * 100}\n")

    kept_urls, filtered_urls = filter_urls(all_urls, threshold=75.0)

    print(f"✓ Kept: {len(kept_urls)} URLs")
    print(f"✗ Filtered: {len(filtered_urls)} URLs")

    if filtered_urls:
        print(f"\n--- FILTERED URLS (Too Obvious) ---")
        for i, entry in enumerate(filtered_urls[:10], 1):
            print(f"\n{i}. {entry['url'][:80]}...")
            print(f"   Numeric: {entry['numeric_percentage']:.1f}%")
            print(f"   Source: {entry['source']}")

    # Show numeric distribution
    print(f"\n\n{'=' * 100}")
    print("NUMERIC PERCENTAGE DISTRIBUTION")
    print(f"{'=' * 100}")

    ranges = [(0, 10), (10, 25), (25, 50), (50, 75), (75, 90), (90, 100)]
    for min_pct, max_pct in ranges:
        count = sum(1 for u in kept_urls if min_pct <= u['numeric_percentage'] < max_pct)
        print(f"{min_pct:3d}% - {max_pct:3d}%: {count:3d} URLs")

    # Show examples from kept URLs
    print(f"\n\n{'=' * 100}")
    print(f"FINAL DATASET - {len(kept_urls)} MALICIOUS URLs (After Filtration)")
    print(f"{'=' * 100}\n")

    # Group by source
    by_source = defaultdict(list)
    for url in kept_urls:
        by_source[url['source']].append(url)

    for source, urls in by_source.items():
        print(f"\n--- {source.upper()} ({len(urls)} URLs) ---\n")
        for i, entry in enumerate(urls[:10], 1):  # Show first 10
            print(f"{i}. {entry['url'][:80]}...")
            print(f"   Numeric: {entry['numeric_percentage']:.1f}%")
            if 'threat' in entry:
                print(f"   Threat: {entry['threat']}")
            if 'category' in entry:
                print(f"   Category: {entry['category']}")
            print()

        if len(urls) > 10:
            print(f"   ... and {len(urls) - 10} more URLs\n")

    # Save to file
    output = {
        "generated_at": "2024-12-04",
        "description": "Fresh malicious URLs from live sources only",
        "sources": ["urlhaus", "phishing_army"],
        "filter_criteria": {
            "numeric_threshold": 75.0,
            "description": "URLs with >75% numeric characters filtered"
        },
        "statistics": {
            "total_fetched": len(all_urls),
            "total_kept": len(kept_urls),
            "total_filtered": len(filtered_urls),
            "filter_rate": (len(filtered_urls) / len(all_urls) * 100) if all_urls else 0,
            "urlhaus_count": len([u for u in kept_urls if u['source'] == 'urlhaus']),
            "phishing_army_count": len([u for u in kept_urls if u['source'] == 'phishing_army']),
        },
        "urls": kept_urls,
        "filtered_urls": filtered_urls,
    }

    output_file = "fresh_malicious_urls.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 100}")
    print("GENERATION COMPLETE")
    print(f"{'=' * 100}")
    print(f"\nDataset saved to: {output_file}")
    print(f"\nFinal Statistics:")
    print(f"  Total Fetched: {len(all_urls)}")
    print(f"  After Filtration: {len(kept_urls)}")
    print(f"  Filter Rate: {(len(filtered_urls) / len(all_urls) * 100):.1f}%")
    print(f"\nBy Source:")
    print(f"  URLhaus: {len([u for u in kept_urls if u['source'] == 'urlhaus'])} URLs")
    print(f"  Phishing Army: {len([u for u in kept_urls if u['source'] == 'phishing_army'])} URLs")

    if len(kept_urls) >= 50:
        print(f"\n✓ TARGET ACHIEVED: {len(kept_urls)} malicious URLs (target was 50)")
    else:
        print(f"\n⚠ Need {50 - len(kept_urls)} more URLs to reach target of 50")


if __name__ == "__main__":
    main()
