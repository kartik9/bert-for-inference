"""
Find live Phishing Army URLs by fetching large batches and validating in real-time.

Fetches URLs, validates they're live, and filters by 20% numeric threshold.
Stops when 10 live URLs are found.
"""
import requests
import socket
import time
import re
from typing import Dict, Any, List
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


def calculate_numeric_percentage(url: str) -> float:
    """Calculate what percentage of URL characters are numeric."""
    url_without_protocol = re.sub(r'^[a-z]+://', '', url, flags=re.IGNORECASE)
    if not url_without_protocol:
        return 0.0
    numeric_count = sum(1 for char in url_without_protocol if char.isdigit())
    total_chars = len(url_without_protocol)
    return (numeric_count / total_chars) * 100


def check_dns(url: str) -> bool:
    """Quick DNS check."""
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        socket.gethostbyname(hostname)
        return True
    except:
        return False


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
    # First quick DNS check
    if not check_dns(url):
        return {"url": url, "is_live": False, "reason": "DNS failed"}

    # Then HTTP check
    http_result = check_http(url)
    if not http_result.get("responding", False):
        return {"url": url, "is_live": False, "reason": "HTTP failed"}

    # Check numeric percentage
    numeric_pct = calculate_numeric_percentage(url)
    if numeric_pct > 20.0:
        return {
            "url": url,
            "is_live": True,
            "filtered": True,
            "reason": f"Too many numbers: {numeric_pct:.1f}%",
            "numeric_percentage": numeric_pct,
        }

    return {
        "url": url,
        "is_live": True,
        "filtered": False,
        "numeric_percentage": numeric_pct,
        "status_code": http_result.get("status_code"),
        "final_url": http_result.get("final_url"),
    }


def fetch_phishing_army_urls(count: int = 1000) -> List[str]:
    """Fetch Phishing Army URLs."""
    print(f"[Phishing Army] Fetching up to {count} URLs...")

    url = "https://phishing.army/download/phishing_army_blocklist_extended.txt"
    response = requests.get(url, timeout=30)

    lines = response.text.strip().split('\n')
    urls = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if not line.startswith('http'):
                line = 'http://' + line
            urls.append(line)

            if len(urls) >= count:
                break

    print(f"[Phishing Army] Fetched {len(urls)} URLs")
    return urls


def main():
    """Find 10 live Phishing Army URLs."""
    import warnings
    import random
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    print("=" * 100)
    print("FINDING LIVE PHISHING ARMY URLs")
    print("=" * 100)
    print("\nTarget: 10 live URLs with ≤20% numeric content")
    print("Strategy: Fetch large list, randomly sample for validation")
    print("⚠️  WARNING: Validating potentially malicious URLs\n")

    # Fetch HUGE batch (all available URLs)
    all_urls = fetch_phishing_army_urls(count=100000)

    print(f"\nTotal URLs available: {len(all_urls)}")
    print(f"Randomly sampling URLs for validation...")
    print("Validating in parallel batches...\n")

    live_urls = []
    checked_count = 0
    batch_size = 100
    max_workers = 30

    # Create a shuffled copy for random sampling
    shuffled_urls = all_urls.copy()
    random.shuffle(shuffled_urls)

    start_time = time.time()

    for i in range(0, len(shuffled_urls), batch_size):
        if len(live_urls) >= 10:
            break

        batch = shuffled_urls[i:i + batch_size]
        print(f"Validating random batch {i//batch_size + 1} ({len(batch)} URLs)...", end=" ")

        batch_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(validate_url, url): url for url in batch}

            for future in as_completed(futures):
                result = future.result()
                checked_count += 1

                if result.get("is_live", False) and not result.get("filtered", False):
                    live_urls.append(result)
                    print(f"\n  ✓ Found live URL #{len(live_urls)}: {result['url'][:60]}...")

                    if len(live_urls) >= 10:
                        break

        batch_elapsed = time.time() - batch_start
        print(f"Done in {batch_elapsed:.1f}s (Live: {len(live_urls)})")

    elapsed = time.time() - start_time

    print("\n" + "=" * 100)
    print("VALIDATION COMPLETE")
    print("=" * 100)
    print(f"Total URLs checked: {checked_count}")
    print(f"Live URLs found: {len(live_urls)}")
    print(f"Time elapsed: {elapsed:.1f} seconds")
    print(f"Success rate: {len(live_urls) / checked_count * 100:.1f}%")

    if len(live_urls) >= 10:
        print("\n" + "=" * 100)
        print("10 VERIFIED LIVE PHISHING URLs")
        print("=" * 100)

        for i, entry in enumerate(live_urls[:10], 1):
            print(f"\n{i}. {entry['url']}")
            print(f"   ✓ HTTP Status: {entry.get('status_code', 'N/A')}")
            print(f"   ✓ Numeric content: {entry['numeric_percentage']:.1f}%")
            if entry.get('final_url') != entry.get('url'):
                print(f"   ↪ Redirected to: {entry.get('final_url', 'N/A')[:60]}...")

        print("\n" + "=" * 100)
        print("⚠️  WARNING: These are ACTIVE PHISHING URLs - DO NOT VISIT")
        print("=" * 100)

        # Save results
        import json
        output_file = "live_phishing_validated.json"
        with open(output_file, 'w') as f:
            json.dump({
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "statistics": {
                    "total_checked": checked_count,
                    "live_found": len(live_urls),
                    "success_rate": len(live_urls) / checked_count * 100,
                },
                "live_urls": live_urls[:10],
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")
    else:
        print(f"\n⚠️  Only found {len(live_urls)} live URLs out of {checked_count} checked")
        print("Phishing Army blocklist may contain mostly dead URLs")


if __name__ == "__main__":
    main()
