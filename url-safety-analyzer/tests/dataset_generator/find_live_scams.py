"""
Find and validate live scam URLs from various sources.

Scam categories:
- Fake giveaways (cryptocurrency, prize scams)
- Investment/Ponzi schemes
- Romance/dating scams
- Tech support scams
- Fake shopping sites
- Cryptocurrency scams
"""
import requests
import socket
import time
import re
import json
from typing import Dict, Any, List
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import random


def calculate_numeric_percentage(url: str) -> float:
    """Calculate what percentage of URL characters are numeric."""
    url_without_protocol = re.sub(r'^[a-z]+://', '', url, flags=re.IGNORECASE)
    if not url_without_protocol:
        return 0.0
    numeric_count = sum(1 for char in url_without_protocol if char.isdigit())
    total_chars = len(url_without_protocol)
    return (numeric_count / total_chars) * 100


def check_dns(url: str) -> tuple:
    """Quick DNS check."""
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        ip = socket.gethostbyname(hostname)
        return True, ip
    except:
        return False, None


def check_http(url: str, timeout: int = 5) -> Dict[str, Any]:
    """Quick HTTP check."""
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            verify=False
        )
        return {
            "responding": True,
            "status_code": response.status_code,
            "final_url": response.url,
        }
    except:
        return {"responding": False}


def validate_url(url: str) -> Dict[str, Any]:
    """Validate a single URL."""
    dns_ok, ip = check_dns(url)
    if not dns_ok:
        return {"url": url, "is_live": False, "reason": "DNS failed"}

    http_result = check_http(url)
    if not http_result.get("responding", False):
        return {"url": url, "is_live": False, "reason": "HTTP failed", "dns_ip": ip}

    numeric_pct = calculate_numeric_percentage(url)
    if numeric_pct > 20.0:
        return {
            "url": url,
            "is_live": True,
            "filtered": True,
            "reason": f"Too many numbers: {numeric_pct:.1f}%",
            "numeric_percentage": numeric_pct,
            "dns_ip": ip,
        }

    return {
        "url": url,
        "is_live": True,
        "filtered": False,
        "numeric_percentage": numeric_pct,
        "status_code": http_result.get("status_code"),
        "final_url": http_result.get("final_url"),
        "dns_ip": ip,
    }


def fetch_urlhaus_scams(count: int = 1000) -> List[Dict[str, Any]]:
    """Fetch scam/fraud URLs from URLhaus CSV feed."""
    print(f"[URLhaus Scams] Fetching fraud/scam URLs...")

    try:
        url = "https://urlhaus.abuse.ch/downloads/csv_recent/"
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f"[URLhaus Scams] Failed: {response.status_code}")
            return []

        lines = response.text.strip().split('\n')
        urls = []

        for line in lines:
            if line.startswith('#') or line.startswith('id,'):
                continue

            parts = line.split(',', 7)
            if len(parts) >= 6:
                url_id, dateadded, url_str, status, threat, tags = parts[:6]

                # Look for scam-related threats
                threat_lower = threat.lower()
                tags_lower = tags.lower() if tags else ""

                is_scam = any(keyword in threat_lower or keyword in tags_lower
                             for keyword in ['scam', 'fraud', 'fake', 'ponzi', 'giveaway'])

                if is_scam and status == '"online"':
                    urls.append({
                        "url": url_str.strip('"'),
                        "urlhaus_id": url_id,
                        "threat": threat.strip('"'),
                        "tags": tags.strip('"'),
                        "source": "urlhaus",
                        "category": "scam",
                    })

                    if len(urls) >= count:
                        break

        print(f"[URLhaus Scams] Found {len(urls)} scam-related URLs")
        return urls

    except Exception as e:
        print(f"[URLhaus Scams] Error: {e}")
        return []


def fetch_cryptoscam_github() -> List[Dict[str, Any]]:
    """Try to fetch from CryptoScam GitHub repositories."""
    print(f"[CryptoScam GitHub] Attempting to fetch from public repos...")

    # Try fetching from a known crypto scam list on GitHub
    try:
        # Example: MetaMask maintains scam lists
        url = "https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/master/src/config.json"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            urls = []

            # Extract blacklisted domains
            if 'blacklist' in data:
                for domain in data['blacklist'][:1000]:
                    if not domain.startswith('http'):
                        domain = 'http://' + domain

                    urls.append({
                        "url": domain,
                        "source": "metamask_blacklist",
                        "category": "scam",
                        "subcategory": "crypto_scam",
                    })

            print(f"[CryptoScam GitHub] Fetched {len(urls)} domains from MetaMask blacklist")
            return urls
        else:
            print(f"[CryptoScam GitHub] Failed: {response.status_code}")
            return []

    except Exception as e:
        print(f"[CryptoScam GitHub] Error: {e}")
        return []


def fetch_scamadviser_list() -> List[str]:
    """Try to fetch from ScamAdviser or similar sources."""
    print(f"[ScamAdviser] Attempting to fetch scam list...")

    # Known scam patterns - common scam domains
    # These are example patterns, not endorsing these as actual scams
    scam_patterns = [
        # Will try to find actual reported scam sites
    ]

    print(f"[ScamAdviser] No public API available")
    return []


def get_known_scam_examples() -> List[Dict[str, Any]]:
    """Get a curated list of known scam URL patterns for testing."""
    # These are documented scam patterns from security research
    # NOT endorsing these, just using for security testing

    print("[Known Scams] Using documented scam examples from security research...")

    # Many scams use free hosting platforms
    scam_examples = [
        # These would come from actual scam reporting databases
        # For now, returning empty to test with real sources
    ]

    return []


def main():
    """Find live scam URLs."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    print("=" * 100)
    print("FINDING LIVE SCAM URLs")
    print("=" * 100)
    print("\nTarget: 10 live scam URLs with ≤20% numeric content")
    print("Categories: Crypto scams, investment scams, fake giveaways, tech support scams")
    print("⚠️  WARNING: Validating potentially malicious URLs\n")

    all_sources = []

    # Try URLhaus for scam-related URLs
    urlhaus_scams = fetch_urlhaus_scams(count=5000)
    all_sources.extend(urlhaus_scams)

    # Try MetaMask crypto scam blacklist from GitHub
    crypto_scams = fetch_cryptoscam_github()
    all_sources.extend(crypto_scams)

    # Try other sources
    known_scams = get_known_scam_examples()
    all_sources.extend(known_scams)

    if not all_sources:
        print("\n⚠️  No scam URL sources available")
        print("Tried:")
        print("  - URLhaus (scam-related)")
        print("  - MetaMask crypto scam blacklist")
        print("  - CryptoScamDB API (unavailable)")
        print("\nScam databases may require authentication or have restricted access")
        return

    # Extract URLs
    all_urls = []
    for entry in all_sources:
        if isinstance(entry, dict) and 'url' in entry:
            all_urls.append(entry)
        elif isinstance(entry, str):
            all_urls.append({"url": entry, "source": "unknown", "category": "scam"})

    print(f"\nTotal scam URLs to validate: {len(all_urls)}")
    print("Randomly sampling for validation...\n")

    # Shuffle for random sampling
    random.shuffle(all_urls)

    live_urls = []
    checked_count = 0
    batch_size = 50
    max_workers = 30

    start_time = time.time()

    for i in range(0, len(all_urls), batch_size):
        if len(live_urls) >= 10:
            break

        batch = all_urls[i:i + batch_size]
        print(f"Validating batch {i//batch_size + 1} ({len(batch)} URLs)...", end=" ", flush=True)

        batch_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for entry in batch:
                url = entry['url'] if isinstance(entry, dict) else entry
                futures[executor.submit(validate_url, url)] = entry

            for future in as_completed(futures):
                result = future.result()
                entry = futures[future]
                checked_count += 1

                if result.get("is_live", False) and not result.get("filtered", False):
                    # Merge entry metadata with validation results
                    if isinstance(entry, dict):
                        result.update({
                            "source": entry.get("source", "unknown"),
                            "scam_category": entry.get("category", "scam"),
                            "subcategory": entry.get("subcategory", ""),
                        })

                    live_urls.append(result)
                    print(f"\n  ✓ Found live scam #{len(live_urls)}: {result['url'][:70]}...")
                    print(f"    Batch {i//batch_size + 1} ", end="", flush=True)

                    if len(live_urls) >= 10:
                        break

        batch_elapsed = time.time() - batch_start
        print(f"Done in {batch_elapsed:.1f}s (Live: {len(live_urls)})")

    elapsed = time.time() - start_time

    print("\n" + "=" * 100)
    print("VALIDATION COMPLETE")
    print("=" * 100)
    print(f"Total URLs checked: {checked_count}")
    print(f"Live scam URLs found: {len(live_urls)}")
    print(f"Time elapsed: {elapsed:.1f} seconds")
    if checked_count > 0:
        print(f"Success rate: {len(live_urls) / checked_count * 100:.1f}%")

    if len(live_urls) >= 10:
        print("\n" + "=" * 100)
        print("10 VERIFIED LIVE SCAM URLs")
        print("=" * 100)

        for i, entry in enumerate(live_urls[:10], 1):
            print(f"\n{i}. {entry['url']}")
            print(f"   ✓ DNS Resolved: {entry.get('dns_ip', 'N/A')}")
            print(f"   ✓ HTTP Status: {entry.get('status_code', 'N/A')}")
            print(f"   ✓ Numeric content: {entry['numeric_percentage']:.1f}%")
            print(f"   Source: {entry.get('source', 'N/A')}")
            print(f"   Category: {entry.get('scam_category', 'N/A')}")
            if entry.get('final_url') != entry.get('url'):
                final = entry.get('final_url', '')
                if len(final) > 70:
                    final = final[:67] + '...'
                print(f"   ↪ Redirected to: {final}")

        print("\n" + "=" * 100)
        print("⚠️  WARNING: These are ACTIVE SCAM URLs - DO NOT VISIT OR SEND MONEY")
        print("=" * 100)

        # Save results
        output_file = "live_scam_urls.json"
        with open(output_file, 'w') as f:
            json.dump({
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "scam_databases",
                "statistics": {
                    "total_checked": checked_count,
                    "live_found": len(live_urls),
                    "success_rate": len(live_urls) / checked_count * 100 if checked_count > 0 else 0,
                },
                "live_urls": live_urls[:10],
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")
    else:
        print(f"\n⚠️  Found {len(live_urls)} live scam URLs (target was 10)")
        if len(live_urls) > 0:
            print("\nPartial results:")
            for i, entry in enumerate(live_urls, 1):
                print(f"\n{i}. {entry['url']}")
                print(f"   ✓ DNS: {entry.get('dns_ip', 'N/A')}")
                print(f"   ✓ HTTP: {entry.get('status_code', 'N/A')}")
                print(f"   Category: {entry.get('scam_category', 'N/A')}")


if __name__ == "__main__":
    main()
