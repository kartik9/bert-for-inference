"""
Validate user-provided phishing URLs to find live ones.
"""
import requests
import socket
import time
import re
import json
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


def check_dns(url: str) -> tuple[bool, str]:
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


# User-provided URLs to validate
USER_URLS = """https://roblox.com.ge/games/94641939467366/Fun-combat-game?privateServerLinkCode=91006313887146611551343620283535
http://piyushsingh24.github.io/spotify-clone
https://71pms7116aa5mketapp.peou.de/71PMs/Aa5MKEtAPp/6MUwbNfsyIzYe2bbfMTJ4D9qgen/71PMs/Aa5MKEtAPp/Finance/7116/anaheim.net/6MUwbNfsyIzYe2bbfMTJ
https://rbx-url.com/cH6-h99q
https://www.apprewards.xyz/
https://chatpgt.wpenginepowered.com/CH/swisspas_2k25/swisspas_2k25/login.php
https://chatpgt.wpenginepowered.com/CH/swisspas_2k25/swisspas_2k25/
https://www.website-e8dce2af.pop.owl.temporary.site/
https://teegardenvodka.avromic.com/canaccordgenuity/cgf.html
http://skyhighcraft.com/ji/
https://roblox.com.py/games/920587237/Adopt-Me?privateServerLinkCode=46901839668685421802122542343015
https://uhggf.buzz/h5/
https://uhggf.buzz/
https://bdomobile.onlinebanking-bdo-87a.workers.dev/bdo-form/zL8WWK6J47Gt2zKMjoKL2nFKeS10NauNldfUgD0BnA/
http://cy945266.tw1.ru/Wetransfer/fr
https://scaling-waffle-sigma.vercel.app/
http://www.scaling-waffle-sigma.vercel.app/
https://coinzbas-eprolgenvx.godaddysites.com/
https://roblox.com.ge/users/9018258961/profile
http://www.n4kpoby8alj.mycompanyportal.xyz/
http://www.7azd7pm9h.mycompanyportal.xyz/""".strip().split('\n')


def main():
    """Validate user-provided URLs."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    print("=" * 100)
    print("VALIDATING USER-PROVIDED PHISHING URLs")
    print("=" * 100)
    print(f"\nTotal URLs to validate: {len(USER_URLS)}")
    print("Target: Find 10 live URLs with ≤20% numeric content")
    print("⚠️  WARNING: Validating potentially malicious URLs\n")

    live_urls = []
    checked_count = 0
    batch_size = 20
    max_workers = 20

    start_time = time.time()

    print("Validating in parallel batches...\n")

    for i in range(0, len(USER_URLS), batch_size):
        batch = USER_URLS[i:i + batch_size]
        print(f"Validating batch {i//batch_size + 1} ({len(batch)} URLs)...", end=" ")

        batch_start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(validate_url, url.strip()): url for url in batch if url.strip()}

            for future in as_completed(futures):
                result = future.result()
                checked_count += 1

                if result.get("is_live", False) and not result.get("filtered", False):
                    live_urls.append(result)
                    print(f"\n  ✓ Found live URL #{len(live_urls)}: {result['url'][:60]}...")

        batch_elapsed = time.time() - batch_start
        print(f"Done in {batch_elapsed:.1f}s (Live so far: {len(live_urls)})")

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
                print(f"   ↪ Redirected to: {entry.get('final_url', 'N/A')[:60]}...")

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
