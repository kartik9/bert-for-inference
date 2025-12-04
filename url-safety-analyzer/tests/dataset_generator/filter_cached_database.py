"""
Filter the full cached phishing database to remove overly obvious URLs.
"""
import json
import re
from typing import List, Dict, Any


def calculate_numeric_percentage(url: str) -> float:
    """Calculate what percentage of URL characters are numeric."""
    # Remove protocol (http://, https://, ftp://)
    url_without_protocol = re.sub(r'^[a-z]+://', '', url, flags=re.IGNORECASE)

    if not url_without_protocol:
        return 0.0

    # Count numeric characters
    numeric_count = sum(1 for char in url_without_protocol if char.isdigit())
    total_chars = len(url_without_protocol)

    return (numeric_count / total_chars) * 100


def main():
    """Filter the full cached phishing database."""
    print("="*100)
    print("Filtering Full Cached Phishing Database (100 URLs)")
    print("="*100)

    # Load the full database
    with open("/home/user/bert-for-inference/url-safety-analyzer/backend/real_phishing_urls.json", 'r') as f:
        data = json.load(f)

    urls = data.get('urls', [])
    print(f"\nTotal URLs in database: {len(urls)}")

    # Analyze numeric percentage distribution
    numeric_percentages = []
    filtered_count = 0
    filtered_examples = []

    for entry in urls:
        url = entry.get('url', '')
        numeric_pct = calculate_numeric_percentage(url)
        numeric_percentages.append(numeric_pct)

        if numeric_pct > 75.0:
            filtered_count += 1
            if len(filtered_examples) < 10:  # Save first 10 examples
                filtered_examples.append({
                    'url': url,
                    'numeric_pct': numeric_pct,
                    'brand': entry.get('metadata', {}).get('impersonated_brand', 'Unknown')
                })

    # Statistics
    print(f"\n{'='*100}")
    print("Numeric Percentage Analysis")
    print(f"{'='*100}")
    print(f"URLs with >75% numeric characters: {filtered_count} ({filtered_count/len(urls)*100:.1f}%)")
    print(f"URLs with ≤75% numeric characters: {len(urls) - filtered_count} ({(len(urls)-filtered_count)/len(urls)*100:.1f}%)")

    # Distribution
    ranges = [
        (0, 10),
        (10, 25),
        (25, 50),
        (50, 75),
        (75, 90),
        (90, 100)
    ]

    print(f"\nDistribution by numeric percentage:")
    for min_pct, max_pct in ranges:
        count = sum(1 for pct in numeric_percentages if min_pct <= pct < max_pct)
        print(f"  {min_pct:3d}% - {max_pct:3d}%: {count:3d} URLs ({count/len(urls)*100:5.1f}%)")

    # Show examples of filtered URLs
    if filtered_examples:
        print(f"\n{'='*100}")
        print(f"Examples of URLs with >75% Numeric Characters (Would be Filtered)")
        print(f"{'='*100}")

        for i, example in enumerate(filtered_examples, 1):
            print(f"\n{i}. {example['url']}")
            print(f"   Numeric: {example['numeric_pct']:.1f}%")
            print(f"   Target Brand: {example['brand']}")

    # Create filtered dataset
    kept_urls = []
    filtered_urls = []

    for entry in urls:
        url = entry.get('url', '')
        numeric_pct = calculate_numeric_percentage(url)

        if numeric_pct > 75.0:
            entry_copy = entry.copy()
            entry_copy['filter_reason'] = f"Too many numbers: {numeric_pct:.1f}% numeric"
            entry_copy['numeric_percentage'] = numeric_pct
            filtered_urls.append(entry_copy)
        else:
            entry_copy = entry.copy()
            entry_copy['numeric_percentage'] = numeric_pct
            kept_urls.append(entry_copy)

    # Save filtered dataset
    output = {
        "source": "Filtered Real Active Phishing URLs",
        "fetch_date": data.get('fetch_date'),
        "filter_date": "2024-12-04",
        "filter_criteria": {
            "numeric_threshold": 75.0,
            "description": "URLs with >75% numeric characters filtered as overly obvious"
        },
        "total_original": len(urls),
        "total_kept": len(kept_urls),
        "total_filtered": len(filtered_urls),
        "urls": kept_urls,
        "filtered_urls": filtered_urls[:20]  # Save first 20 filtered for reference
    }

    output_file = "real_phishing_urls_filtered.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\n{'='*100}")
    print(f"Filtered database saved to: {output_file}")
    print(f"{'='*100}")
    print(f"Original URLs: {len(urls)}")
    print(f"Kept URLs: {len(kept_urls)}")
    print(f"Filtered URLs: {len(filtered_urls)}")
    print(f"\nThe filtered database has {len(kept_urls)} quality phishing URLs")
    print(f"that aren't obviously suspicious based on numeric content alone.")


if __name__ == "__main__":
    main()
