"""
Display sample malicious URLs from various sources.
"""
import json
import requests
from typing import List, Dict, Any
from collections import defaultdict


def load_cached_phishing_urls(file_path: str, count: int = 5) -> List[Dict[str, Any]]:
    """Load phishing URLs from cached JSON file."""
    print(f"[Cached Phishing URLs] Loading from {file_path}...")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        urls = data.get("urls", [])

        # Group by impersonated brand to get diverse examples
        by_brand = defaultdict(list)
        for entry in urls:
            brand = entry.get("metadata", {}).get("impersonated_brand", "Unknown")
            by_brand[brand].append(entry)

        # Get diverse samples
        samples = []
        brands_seen = set()

        for entry in urls:
            brand = entry.get("metadata", {}).get("impersonated_brand", "Unknown")
            if brand not in brands_seen or len(samples) < count:
                samples.append(entry)
                brands_seen.add(brand)

            if len(samples) >= count:
                break

        print(f"[Cached Phishing URLs] Loaded {len(samples)} diverse samples")
        return samples

    except Exception as e:
        print(f"[Cached Phishing URLs] Error: {e}")
        return []


def fetch_urlhaus_csv(count: int = 5) -> List[Dict[str, Any]]:
    """Fetch from URLhaus CSV feed (no auth required)."""
    print(f"[URLhaus CSV] Fetching recent malware URLs...")

    try:
        # URLhaus provides a public CSV feed
        url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
        response = requests.get(url, timeout=30)
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
                        "status": status.strip('"'),
                    })

                    if len(results) >= count:
                        break

        print(f"[URLhaus CSV] Fetched {len(results)} malware URLs")
        return results

    except Exception as e:
        print(f"[URLhaus CSV] Error: {e}")
        return []


def fetch_phishing_army(count: int = 5) -> List[Dict[str, Any]]:
    """Fetch from Phishing Army (free feed)."""
    print(f"[Phishing Army] Fetching phishing URLs...")

    try:
        # Phishing Army provides a free blocklist
        url = "https://phishing.army/download/phishing_army_blocklist.txt"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        lines = response.text.strip().split('\n')

        results = []
        for line in lines:
            # Skip comments
            if line.startswith('#') or not line.strip():
                continue

            # URLs are listed one per line
            url_str = line.strip()
            if url_str:
                results.append({
                    "url": f"http://{url_str}" if not url_str.startswith('http') else url_str,
                    "source": "phishing_army",
                    "type": "phishing",
                })

                if len(results) >= count:
                    break

        print(f"[Phishing Army] Fetched {len(results)} phishing URLs")
        return results

    except Exception as e:
        print(f"[Phishing Army] Error: {e}")
        return []


def main():
    """Display malicious URL samples from all sources."""
    print("=" * 100)
    print("MALICIOUS URL SAMPLES - Live Fetch from Threat Intelligence Sources")
    print("=" * 100)
    print()

    all_results = {}

    # Source 1: Cached Phishing Database
    print("\n" + "=" * 100)
    print("SOURCE 1: Cached Phishing Database (Real Active Phishing URLs)")
    print("=" * 100)
    cached_phishing = load_cached_phishing_urls(
        "/home/user/bert-for-inference/url-safety-analyzer/backend/real_phishing_urls.json",
        count=5
    )
    all_results['cached_phishing'] = cached_phishing

    for i, entry in enumerate(cached_phishing, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Label: {entry['ground_truth_label']}")
        print(f"   Category: {entry['expected_category']}")
        print(f"   Target Brand: {entry['metadata']['impersonated_brand']}")
        print(f"   Phishing Type: {entry['metadata']['phishing_type']}")
        print(f"   Threat Indicators: {', '.join(entry['metadata']['threat_indicators'])}")

    # Source 2: URLhaus CSV
    print("\n\n" + "=" * 100)
    print("SOURCE 2: URLhaus (Malware Distribution URLs)")
    print("=" * 100)
    urlhaus_urls = fetch_urlhaus_csv(count=5)
    all_results['urlhaus'] = urlhaus_urls

    for i, entry in enumerate(urlhaus_urls, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   URLhaus ID: {entry['urlhaus_id']}")
        print(f"   Threat: {entry['threat']}")
        print(f"   Tags: {entry['tags']}")
        print(f"   Status: {entry['status']}")
        print(f"   Date Added: {entry['dateadded']}")

    # Source 3: Phishing Army
    print("\n\n" + "=" * 100)
    print("SOURCE 3: Phishing Army (Community Phishing Blocklist)")
    print("=" * 100)
    phishing_army = fetch_phishing_army(count=5)
    all_results['phishing_army'] = phishing_army

    for i, entry in enumerate(phishing_army, 1):
        print(f"\n{i}. URL: {entry['url']}")
        print(f"   Source: {entry['source']}")
        print(f"   Type: {entry['type']}")

    # Summary
    print("\n\n" + "=" * 100)
    print("SUMMARY OF MALICIOUS URL SOURCES")
    print("=" * 100)
    print(f"Cached Phishing Database: {len(cached_phishing)} URLs")
    print(f"URLhaus Malware URLs: {len(urlhaus_urls)} URLs")
    print(f"Phishing Army URLs: {len(phishing_army)} URLs")
    print(f"Total Malicious URLs: {len(cached_phishing) + len(urlhaus_urls) + len(phishing_army)}")

    # Save results
    output = {
        "fetched_at": "2024-12-04",
        "sources": all_results,
        "summary": {
            "cached_phishing_count": len(cached_phishing),
            "urlhaus_count": len(urlhaus_urls),
            "phishing_army_count": len(phishing_army),
            "total_count": len(cached_phishing) + len(urlhaus_urls) + len(phishing_army),
        }
    }

    output_file = "malicious_url_samples.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Analysis
    print("\n\n" + "=" * 100)
    print("ANALYSIS & CATEGORIZATION")
    print("=" * 100)

    print("\n📊 Phishing Targets (from cached database):")
    brands = defaultdict(int)
    for entry in cached_phishing:
        brand = entry['metadata']['impersonated_brand']
        brands[brand] += 1

    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {brand}: {count} URL(s)")

    print("\n📊 Malware Threats (from URLhaus):")
    threats = defaultdict(int)
    for entry in urlhaus_urls:
        threat = entry.get('threat', 'unknown')
        threats[threat] += 1

    for threat, count in sorted(threats.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {threat}: {count} URL(s)")


if __name__ == "__main__":
    main()
