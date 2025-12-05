"""
Validate all user-provided phishing URLs to find 10 live ones.
"""
import requests
import socket
import time
import re
import json
from typing import Dict, Any
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


def main():
    """Validate all user-provided URLs."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    # Load URLs from file
    with open('user_phishing_urls.txt', 'r') as f:
        all_urls = [line.strip() for line in f if line.strip()]

    print("=" * 100)
    print("VALIDATING USER-PROVIDED PHISHING URLs")
    print("=" * 100)
    print(f"\nTotal URLs to validate: {len(all_urls)}")
    print("Target: Find 10 live URLs with ≤20% numeric content")
    print("⚠️  WARNING: Validating potentially malicious URLs\n")

    live_urls = []
    checked_count = 0
    batch_size = 50
    max_workers = 30

    start_time = time.time()

    print("Validating in parallel batches...\n")

    for i in range(0, len(all_urls), batch_size):
        if len(live_urls) >= 10:
            print(f"\n✓ Found {len(live_urls)} live URLs - stopping validation")
            break

        batch = all_urls[i:i + batch_size]
        print(f"Validating batch {i//batch_size + 1} ({len(batch)} URLs)...", end=" ", flush=True)

        batch_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(validate_url, url): url for url in batch}

            for future in as_completed(futures):
                result = future.result()
                checked_count += 1

                if result.get("is_live", False) and not result.get("filtered", False):
                    live_urls.append(result)
                    print(f"\n  ✓ Found live URL #{len(live_urls)}: {result['url'][:70]}...")
                    print(f"    Batch {i//batch_size + 1} ", end="", flush=True)

                    if len(live_urls) >= 10:
                        break

        batch_elapsed = time.time() - batch_start
        print(f"Done in {batch_elapsed:.1f}s (Live total: {len(live_urls)})")

    elapsed = time.time() - start_time

    print("\n" + "=" * 100)
    print("VALIDATION COMPLETE")
    print("=" * 100)
    print(f"Total URLs checked: {checked_count}")
    print(f"Live URLs found: {len(live_urls)}")
    print(f"Time elapsed: {elapsed:.1f} seconds")
    if checked_count > 0:
        print(f"Success rate: {len(live_urls) / checked_count * 100:.1f}%")

    if len(live_urls) >= 10:
        print("\n" + "=" * 100)
        print("10 VERIFIED LIVE PHISHING URLs")
        print("=" * 100)

        for i, entry in enumerate(live_urls[:10], 1):
            print(f"\n{i}. {entry['url']}")
            print(f"   ✓ DNS Resolved: {entry.get('dns_ip', 'N/A')}")
            print(f"   ✓ HTTP Status: {entry.get('status_code', 'N/A')}")
            print(f"   ✓ Numeric content: {entry['numeric_percentage']:.1f}%")
            if entry.get('final_url') != entry.get('url'):
                final = entry.get('final_url', '')
                if len(final) > 70:
                    final = final[:67] + '...'
                print(f"   ↪ Redirected to: {final}")

        print("\n" + "=" * 100)
        print("⚠️  WARNING: These are ACTIVE PHISHING URLs - DO NOT VISIT")
        print("=" * 100)

        # Save results
        output_file = "live_user_provided_phishing.json"
        with open(output_file, 'w') as f:
            json.dump({
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "user_provided",
                "statistics": {
                    "total_urls_available": len(all_urls),
                    "total_checked": checked_count,
                    "live_found": len(live_urls),
                    "success_rate": len(live_urls) / checked_count * 100 if checked_count > 0 else 0,
                },
                "live_urls": live_urls[:10],
            }, f, indent=2)

        print(f"\nResults saved to: {output_file}")
    else:
        print(f"\n⚠️  Found {len(live_urls)} live URLs (target was 10)")
        if len(live_urls) > 0:
            print("\nPartial results:")
            for i, entry in enumerate(live_urls, 1):
                print(f"\n{i}. {entry['url']}")
                print(f"   ✓ DNS: {entry.get('dns_ip', 'N/A')}")
                print(f"   ✓ HTTP Status: {entry.get('status_code', 'N/A')}")
                print(f"   ✓ Numeric: {entry['numeric_percentage']:.1f}%")


if __name__ == "__main__":
    main()
