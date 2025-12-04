"""
Live URL validator for URLhaus malware URLs.
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
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_dns(self, url: str) -> Dict[str, Any]:
        """Check if URL resolves via DNS."""
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc or parsed.path.split('/')[0]

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
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False
            )

            return {
                "responding": True,
                "status_code": response.status_code,
                "final_url": response.url,
                "redirected": response.url != url,
            }
        except requests.exceptions.Timeout:
            return {"responding": False, "error": "Connection timeout"}
        except requests.exceptions.ConnectionError:
            return {"responding": False, "error": "Connection failed"}
        except requests.exceptions.TooManyRedirects:
            return {"responding": False, "error": "Too many redirects"}
        except Exception as e:
            return {"responding": False, "error": str(e)}

    def validate_url(self, url: str) -> Dict[str, Any]:
        """Perform complete validation of a URL."""
        result = {"url": url, "timestamp": time.time()}

        dns_result = self.check_dns(url)
        result["dns"] = dns_result

        if dns_result.get("resolved", False):
            http_result = self.check_http(url)
            result["http"] = http_result
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
    """Validate URLhaus malware URLs from the dataset."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    print("=" * 100)
    print("LIVE URL VALIDATOR - URLhaus Malware URLs")
    print("=" * 100)
    print("\n⚠️  WARNING: Connecting to potentially malicious URLs for validation\n")

    with open('fresh_malicious_urls.json', 'r') as f:
        data = json.load(f)

    urlhaus_urls = [u for u in data['urls'] if u['source'] == 'urlhaus']

    print(f"Total URLhaus URLs to validate: {len(urlhaus_urls)}")
    print(f"Starting validation with 5s timeout per URL...")
    print()

    urls_to_check = [entry['url'] for entry in urlhaus_urls]

    validator = LiveURLValidator(timeout=5, max_workers=20)

    print("Validating URLs in parallel...")
    start_time = time.time()

    validation_results = validator.validate_batch(urls_to_check)

    elapsed = time.time() - start_time
    print(f"\nValidation completed in {elapsed:.1f} seconds")

    url_to_validation = {r['url']: r for r in validation_results}

    validated_urls = []
    for entry in urlhaus_urls:
        url = entry['url']
        validation = url_to_validation.get(url, {})

        validated_urls.append({
            **entry,
            "validation": validation,
            "is_live": validation.get("is_live", False),
        })

    live_urls = [u for u in validated_urls if u.get("is_live", False)]
    dead_urls = [u for u in validated_urls if not u.get("is_live", False)]

    print("\n" + "=" * 100)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 100)
    print(f"Total URLs checked: {len(validated_urls)}")
    print(f"Live URLs (responding): {len(live_urls)}")
    print(f"Dead URLs (not responding): {len(dead_urls)}")
    print(f"Success rate: {len(live_urls) / len(validated_urls) * 100:.1f}%")

    print("\n" + "=" * 100)
    print(f"{min(10, len(live_urls))} VERIFIED LIVE MALWARE URLs (URLhaus)")
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
        print(f"   Threat: {entry.get('threat', 'N/A')}")
        print(f"   URLhaus ID: {entry.get('urlhaus_id', 'N/A')}")
        print(f"   Numeric: {entry['numeric_percentage']:.1f}%")

    if len(live_urls) > 0:
        output_file = "validated_urlhaus_live.json"
        with open(output_file, 'w') as f:
            json.dump({
                "validated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "statistics": {
                    "total_checked": len(validated_urls),
                    "live_urls": len(live_urls),
                    "success_rate": len(live_urls) / len(validated_urls) * 100,
                },
                "live_urls": live_urls,
            }, f, indent=2)

        print("\n" + "=" * 100)
        print(f"Validated live URLs saved to: {output_file}")
        print(f"Live URLs available: {len(live_urls)}")
        print("\n⚠️  WARNING: These are ACTIVE MALWARE DISTRIBUTION URLs - DO NOT VISIT")
        print("=" * 100)


if __name__ == "__main__":
    main()
