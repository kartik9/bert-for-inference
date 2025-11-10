#!/usr/bin/env python3
"""
Fetch real active phishing URLs from public threat intelligence sources.
"""

import requests
import json
from typing import List, Dict
from datetime import datetime


class RealPhishingFetcher:
    """Fetcher for real active phishing URLs from multiple sources."""

    def __init__(self):
        self.phishing_urls = []

    def fetch_from_phishing_database(self, limit=100) -> List[Dict]:
        """Fetch from Phishing-Database GitHub repository (actively maintained)."""
        print("Fetching real phishing URLs from Phishing-Database...")

        url = "https://raw.githubusercontent.com/Phishing-Database/Phishing.Database/master/phishing-links-ACTIVE.txt"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                phishing_urls = []

                for line in lines[:limit]:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Determine the target brand from URL patterns
                        brand, category = self._detect_target_brand(line)

                        phishing_urls.append({
                            "url": line,
                            "ground_truth_label": "MALICIOUS",
                            "expected_category": "phishing",
                            "description": f"Active phishing site targeting {brand}",
                            "metadata": {
                                "source": "Phishing-Database",
                                "impersonated_brand": brand,
                                "phishing_type": category,
                                "difficulty": "medium",
                                "test_purpose": "real_phishing_detection",
                                "threat_indicators": ["phishing", "brand_impersonation", "credential_theft"],
                                "verified_active": True,
                                "fetch_date": datetime.utcnow().isoformat()
                            }
                        })

                print(f"✓ Fetched {len(phishing_urls)} real active phishing URLs")
                return phishing_urls
            else:
                print(f"✗ Failed to fetch: HTTP {response.status_code}")
                return []

        except Exception as e:
            print(f"✗ Error fetching from Phishing-Database: {e}")
            return []

    def _detect_target_brand(self, url: str) -> tuple:
        """Detect target brand and phishing category from URL patterns."""
        url_lower = url.lower()

        # Banking/Financial
        if any(x in url_lower for x in ['paypal', 'pp-', 'ppal']):
            return ("PayPal", "payment_processor")
        elif any(x in url_lower for x in ['chase', 'jpmchase', 'jpm']):
            return ("Chase Bank", "banking")
        elif any(x in url_lower for x in ['wellsfargo', 'wf-', 'wells']):
            return ("Wells Fargo", "banking")
        elif any(x in url_lower for x in ['bankofamerica', 'bofa', 'boa-']):
            return ("Bank of America", "banking")
        elif any(x in url_lower for x in ['cibc', 'rbc', 'td-', 'tangerine', 'scotiabank', 'desjardins', 'simplii']):
            return ("Canadian Bank", "banking")
        elif any(x in url_lower for x in ['bank', 'banking', 'citibank', 'citi-']):
            return ("Generic Bank", "banking")

        # Tech Companies
        elif any(x in url_lower for x in ['microsoft', 'ms-', 'msn', 'outlook', 'office365', 'o365', 'azure']):
            return ("Microsoft", "tech_company")
        elif any(x in url_lower for x in ['google', 'gmail', 'goog-', 'drive']):
            return ("Google", "tech_company")
        elif any(x in url_lower for x in ['apple', 'icloud', 'itunes', 'appstore']):
            return ("Apple", "tech_company")
        elif any(x in url_lower for x in ['facebook', 'fb-', 'meta']):
            return ("Facebook/Meta", "social_media")
        elif any(x in url_lower for x in ['instagram', 'ig-', 'insta']):
            return ("Instagram", "social_media")
        elif any(x in url_lower for x in ['linkedin', 'lnkd']):
            return ("LinkedIn", "social_media")
        elif any(x in url_lower for x in ['twitter', 'x.com']):
            return ("Twitter/X", "social_media")
        elif any(x in url_lower for x in ['whatsapp', 'wa-']):
            return ("WhatsApp", "messaging")
        elif any(x in url_lower for x in ['yahoo', 'ymail']):
            return ("Yahoo", "email_provider")
        elif any(x in url_lower for x in ['aol', 'aim']):
            return ("AOL", "email_provider")

        # E-commerce
        elif any(x in url_lower for x in ['amazon', 'amzn', 'aws']):
            return ("Amazon", "ecommerce")
        elif any(x in url_lower for x in ['ebay', 'e-bay']):
            return ("eBay", "ecommerce")
        elif any(x in url_lower for x in ['aliexpress', 'alibaba']):
            return ("Alibaba/AliExpress", "ecommerce")

        # Shipping/Delivery
        elif any(x in url_lower for x in ['usps', 'postal', 'uspis']):
            return ("USPS", "shipping")
        elif any(x in url_lower for x in ['fedex', 'fed-ex']):
            return ("FedEx", "shipping")
        elif any(x in url_lower for x in ['dhl', 'dhlexpress']):
            return ("DHL", "shipping")
        elif any(x in url_lower for x in ['ups', 'united-parcel']):
            return ("UPS", "shipping")

        # Cryptocurrency
        elif any(x in url_lower for x in ['coinbase', 'coin-base']):
            return ("Coinbase", "cryptocurrency")
        elif any(x in url_lower for x in ['binance', 'bnb']):
            return ("Binance", "cryptocurrency")
        elif any(x in url_lower for x in ['metamask', 'meta-mask']):
            return ("MetaMask", "crypto_wallet")
        elif any(x in url_lower for x in ['blockchain', 'crypto', 'bitcoin', 'btc', 'eth', 'wallet']):
            return ("Cryptocurrency Service", "cryptocurrency")

        # Other services
        elif any(x in url_lower for x in ['netflix', 'netflx']):
            return ("Netflix", "streaming")
        elif any(x in url_lower for x in ['adobe', 'acrobat']):
            return ("Adobe", "software")
        elif any(x in url_lower for x in ['dropbox', 'drop-box']):
            return ("Dropbox", "cloud_storage")

        # Generic/Unknown
        elif any(x in url_lower for x in ['login', 'signin', 'auth', 'verify', 'confirm', 'update', 'secure']):
            return ("Generic Service", "credential_harvesting")
        else:
            return ("Unknown Target", "generic_phishing")

    def save_phishing_urls(self, output_path: str):
        """Save fetched phishing URLs to JSON file."""
        data = {
            "source": "Real Active Phishing URLs",
            "fetch_date": datetime.utcnow().isoformat(),
            "total_urls": len(self.phishing_urls),
            "urls": self.phishing_urls
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Saved {len(self.phishing_urls)} phishing URLs to: {output_path}")


if __name__ == "__main__":
    fetcher = RealPhishingFetcher()

    # Fetch from Phishing-Database
    phishing_urls = fetcher.fetch_from_phishing_database(limit=100)
    fetcher.phishing_urls = phishing_urls

    # Save to file
    output_path = "real_phishing_urls.json"
    fetcher.save_phishing_urls(output_path)

    # Show sample
    print(f"\n{'='*70}")
    print("Sample Real Phishing URLs:")
    print(f"{'='*70}\n")

    for i, url_data in enumerate(phishing_urls[:10], 1):
        print(f"{i}. {url_data['url']}")
        print(f"   Target: {url_data['metadata']['impersonated_brand']}")
        print(f"   Category: {url_data['metadata']['phishing_type']}")
        print()
