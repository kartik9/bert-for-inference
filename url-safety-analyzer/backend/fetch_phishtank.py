#!/usr/bin/env python3
"""
Fetch real active phishing URLs from PhishTank and add to dataset.
Run this script in an environment with PhishTank access.
"""

import requests
import json
from datetime import datetime
from typing import List, Dict


def fetch_phishtank_urls(limit=100) -> List[Dict]:
    """Fetch verified active phishing URLs from PhishTank."""
    print("Fetching from PhishTank...")

    url = "http://data.phishtank.com/data/online-valid.json"

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data)} phishing URLs from PhishTank")

            phishing_urls = []

            for entry in data[:limit]:
                phish_url = entry.get('url', '')
                target = entry.get('target', 'Unknown')
                verified = entry.get('verified', 'no')
                submission_time = entry.get('submission_time', '')

                # Only include verified phishing
                if verified == 'yes' and phish_url:
                    phishing_urls.append({
                        "url": phish_url,
                        "ground_truth_label": "MALICIOUS",
                        "expected_category": "phishing",
                        "description": f"Active phishing site targeting {target}",
                        "metadata": {
                            "source": "PhishTank",
                            "impersonated_brand": target,
                            "phishing_type": "credential_harvesting",
                            "difficulty": "medium",
                            "test_purpose": "real_phishing_detection",
                            "threat_indicators": ["phishing", "brand_impersonation", "credential_theft"],
                            "verified_active": True,
                            "verified": verified,
                            "submission_time": submission_time,
                            "fetch_date": datetime.utcnow().isoformat()
                        }
                    })

            print(f"✓ Filtered to {len(phishing_urls)} verified phishing URLs")

            # Show target distribution
            targets = {}
            for item in phishing_urls:
                target = item['metadata']['impersonated_brand']
                targets[target] = targets.get(target, 0) + 1

            print(f"\nTop 10 Targeted Brands:")
            for target, count in sorted(targets.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {target}: {count}")

            return phishing_urls

        else:
            print(f"✗ Failed: HTTP {response.status_code}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def merge_with_existing_dataset(phishtank_urls: List[Dict],
                                 dataset_path: str = "../test_datasets/real_world_test_dataset_500.json"):
    """Merge PhishTank URLs with existing dataset."""
    print(f"\nMerging with existing dataset...")

    try:
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)

        # Get existing URLs to avoid duplicates
        existing_urls = {tc['url'] for tc in dataset['test_cases']}

        # Add new unique URLs
        new_urls = [url for url in phishtank_urls if url['url'] not in existing_urls]

        print(f"  Existing dataset: {len(dataset['test_cases'])} URLs")
        print(f"  PhishTank URLs: {len(phishtank_urls)}")
        print(f"  Duplicates removed: {len(phishtank_urls) - len(new_urls)}")
        print(f"  New URLs to add: {len(new_urls)}")

        # Add new URLs
        dataset['test_cases'].extend(new_urls)
        dataset['total_urls'] = len(dataset['test_cases'])

        # Update statistics
        stats = dataset.get('statistics', {})
        stats['total'] = len(dataset['test_cases'])

        # Update by_label
        by_label = {}
        for tc in dataset['test_cases']:
            label = tc['ground_truth_label']
            by_label[label] = by_label.get(label, 0) + 1
        stats['by_label'] = by_label

        # Update by_source
        by_source = {}
        for tc in dataset['test_cases']:
            source = tc['metadata'].get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1
        stats['by_source'] = by_source

        dataset['statistics'] = stats

        # Save updated dataset
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        print(f"\n✓ Updated dataset saved: {len(dataset['test_cases'])} total URLs")
        print(f"\nDistribution by Label:")
        for label, count in sorted(stats['by_label'].items()):
            pct = (count / stats['total']) * 100
            print(f"  {label}: {count} ({pct:.1f}%)")

        print(f"\nDistribution by Source:")
        for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")

        return dataset

    except Exception as e:
        print(f"✗ Error merging dataset: {e}")
        return None


if __name__ == "__main__":
    print("="*70)
    print("PhishTank URL Fetcher")
    print("="*70 + "\n")

    # Fetch PhishTank URLs
    phishtank_urls = fetch_phishtank_urls(limit=100)

    if phishtank_urls:
        # Save standalone file
        output = {
            "source": "PhishTank",
            "fetch_date": datetime.utcnow().isoformat(),
            "total_urls": len(phishtank_urls),
            "urls": phishtank_urls
        }

        with open("phishtank_urls.json", 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✓ Saved to: phishtank_urls.json")

        # Merge with existing dataset
        print("\n" + "="*70)
        merge_with_existing_dataset(phishtank_urls)

    else:
        print("\n✗ No PhishTank URLs fetched")
        print("\nNote: You may need to:")
        print("  1. Check your network connection")
        print("  2. Verify PhishTank is accessible from your location")
        print("  3. Use a VPN if PhishTank is geo-blocked")
