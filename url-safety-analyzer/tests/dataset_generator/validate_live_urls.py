"""
Live URL validator - checks if URLs are actually active and responding.

Performs:
- DNS resolution checks
- HTTP/HTTPS connectivity tests
- Response code validation
- Timeout handling

WARNING: This script connects to potentially malicious URLs for validation.
Only use in isolated/sandboxed environments for security research.
"""
import requests
import json
import socket
from typing import Dict, Any, List
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class LiveURLValidator:
    """Validates URLs are actually live and responding."""

    def __init__(self, timeout: int = 5, max_workers: int = 10):
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        # Use a generic user agent to avoid blocks
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_dns(self, url: str) -> Dict[str, Any]:
        """Check if URL resolves via DNS."""
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc or parsed.path.split('/')[0]

            # Remove port if present
            if ':' in hostname:
                hostname = hostname.split(':')[0]

            ip_address = socket.gethostbyname(hostname)
            return {
                "resolved": True,
                "ip_address": ip_address,
                "hostname": hostname,
            }
        except socket.gaierror:
            return {
                "resolved": False,
                "error": "DNS resolution failed",
                "hostname": hostname if 'hostname' in locals() else None,
            }
        except Exception as e:
            return {
                "resolved": False,
                "error": str(e),
            }

    def check_http(self, url: str) -> Dict[str, Any]:
        """Check if URL responds to HTTP/HTTPS requests."""
        try:
            # Use HEAD request to avoid downloading content
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False  # Don't verify SSL for malicious sites
            )

            return {
                "responding": True,
                "status_code": response.status_code,
                "final_url": response.url,
                "redirected": response.url != url,
                "headers": dict(response.headers),
            }
        except requests.exceptions.Timeout:
            return {
                "responding": False,
                "error": "Connection timeout",
            }
        except requests.exceptions.ConnectionError:
            return {
                "responding": False,
                "error": "Connection failed",
            }
        except requests.exceptions.TooManyRedirects:
            return {
                "responding": False,
                "error": "Too many redirects",
            }
        except Exception as e:
            return {
                "responding": False,
                "error": str(e),
            }

    def validate_url(self, url: str) -> Dict[str, Any]:
        """Perform complete validation of a URL."""
        result = {
            "url": url,
            "timestamp": time.time(),
        }

        # Check DNS
        dns_result = self.check_dns(url)
        result["dns"] = dns_result

        # Only check HTTP if DNS resolved
        if dns_result.get("resolved", False):
            http_result = self.check_http(url)
            result["http"] = http_result

            # Consider URL live if it resolves AND responds (even with error codes)
            result["is_live"] = http_result.get("responding", False)
        else:
            result["is_live"] = False
            result["http"] = {"responding": False, "error": "DNS failed"}

        return result

    def validate_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Validate multiple URLs in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.validate_url, url): url
                for url in urls
            }

            for future in as_completed(future_to_url):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    url = future_to_url[future]
                    results.append({
                        "url": url,
                        "is_live": False,
                        "error": str(e),
                    })

        return results


def main():
    """Validate Phishing Army URLs from the dataset."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    print("=" * 100)
    print("LIVE URL VALIDATOR - Phishing Army URLs")
    print("=" * 100)
    print("\n⚠️  WARNING: Connecting to potentially malicious URLs for validation")
    print("Only running in isolated environment for security research\n")

    # Load the dataset
    with open('fresh_malicious_urls.json', 'r') as f:
        data = json.load(f)

    # Filter Phishing Army URLs
    phishing_urls = [u for u in data['urls'] if u['source'] == 'phishing_army']

    print(f"Total Phishing Army URLs to validate: {len(phishing_urls)}")
    print(f"Starting validation with {5}s timeout per URL...")
    print()

    # Extract just the URLs
    urls_to_check = [entry['url'] for entry in phishing_urls]

    # Validate
    validator = LiveURLValidator(timeout=5, max_workers=20)

    print("Validating URLs in parallel (this may take a few minutes)...")
    start_time = time.time()

    validation_results = validator.validate_batch(urls_to_check)

    elapsed = time.time() - start_time
    print(f"\nValidation completed in {elapsed:.1f} seconds")

    # Combine original data with validation results
    url_to_validation = {r['url']: r for r in validation_results}

    validated_urls = []
    for entry in phishing_urls:
        url = entry['url']
        validation = url_to_validation.get(url, {})

        validated_urls.append({
            **entry,
            "validation": validation,
            "is_live": validation.get("is_live", False),
        })

    # Separate live and dead URLs
    live_urls = [u for u in validated_urls if u.get("is_live", False)]
    dead_urls = [u for u in validated_urls if not u.get("is_live", False)]

    # Print summary
    print("\n" + "=" * 100)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 100)
    print(f"Total URLs checked: {len(validated_urls)}")
    print(f"Live URLs (responding): {len(live_urls)}")
    print(f"Dead URLs (not responding): {len(dead_urls)}")
    print(f"Success rate: {len(live_urls) / len(validated_urls) * 100:.1f}%")

    # Show 10 live URLs
    print("\n" + "=" * 100)
    print("10 VERIFIED LIVE PHISHING URLs")
    print("=" * 100)

    for i, entry in enumerate(live_urls[:10], 1):
        validation = entry.get('validation', {})
        dns = validation.get('dns', {})
        http = validation.get('http', {})

        print(f"\n{i}. {entry['url']}")
        print(f"   ✓ DNS Resolved: {dns.get('ip_address', 'N/A')}")
        print(f"   ✓ HTTP Status: {http.get('status_code', 'N/A')}")
        if http.get('redirected', False):
            print(f"   ↪ Redirected to: {http.get('final_url', 'N/A')[:60]}...")
        print(f"   Numeric content: {entry['numeric_percentage']:.1f}%")

    # Show sample of dead URLs for debugging
    print("\n" + "=" * 100)
    print("Sample of DEAD URLs (for reference)")
    print("=" * 100)

    for i, entry in enumerate(dead_urls[:5], 1):
        validation = entry.get('validation', {})
        dns = validation.get('dns', {})
        http = validation.get('http', {})

        print(f"\n{i}. {entry['url']}")
        if not dns.get('resolved', False):
            print(f"   ✗ DNS Failed: {dns.get('error', 'Unknown error')}")
        else:
            print(f"   ✓ DNS OK: {dns.get('ip_address', 'N/A')}")
            print(f"   ✗ HTTP Failed: {http.get('error', 'Unknown error')}")

    # Save validated dataset
    output = {
        "generated_at": data.get("generated_at"),
        "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "statistics": {
            "total_checked": len(validated_urls),
            "live_urls": len(live_urls),
            "dead_urls": len(dead_urls),
            "success_rate": len(live_urls) / len(validated_urls) * 100 if validated_urls else 0,
        },
        "live_urls": live_urls,
        "dead_urls": dead_urls,
    }

    output_file = "validated_phishing_urls.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 100)
    print(f"Validated dataset saved to: {output_file}")
    print(f"\nLive URLs available: {len(live_urls)}")
    print("=" * 100)


if __name__ == "__main__":
    main()
