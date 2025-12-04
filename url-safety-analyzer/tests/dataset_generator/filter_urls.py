"""
Filter URLs to remove obviously suspicious patterns.
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


def filter_numeric_urls(urls: List[Dict[str, Any]], threshold: float = 75.0) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out URLs with >75% numeric characters.

    Returns:
        tuple: (kept_urls, filtered_urls)
    """
    kept = []
    filtered = []

    for entry in urls:
        url = entry.get('url', '')
        numeric_pct = calculate_numeric_percentage(url)

        if numeric_pct > threshold:
            entry['filter_reason'] = f"Too many numbers: {numeric_pct:.1f}% numeric characters"
            entry['numeric_percentage'] = numeric_pct
            filtered.append(entry)
        else:
            entry['numeric_percentage'] = numeric_pct
            kept.append(entry)

    return kept, filtered


def load_and_filter_malicious_urls(file_path: str) -> Dict[str, Any]:
    """Load malicious URLs and filter out obvious ones."""
    print(f"\n{'='*100}")
    print(f"Filtering Malicious URLs from: {file_path}")
    print(f"{'='*100}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    results = {}
    total_original = 0
    total_kept = 0
    total_filtered = 0

    for source_name, urls in data.get('sources', {}).items():
        print(f"\n[{source_name.upper()}]")
        print(f"Original count: {len(urls)}")

        kept, filtered = filter_numeric_urls(urls, threshold=75.0)

        print(f"Kept: {len(kept)}")
        print(f"Filtered out: {len(filtered)}")

        if filtered:
            print(f"\nFiltered URLs:")
            for entry in filtered:
                print(f"  ❌ {entry['url'][:80]}...")
                print(f"     Reason: {entry['filter_reason']}")

        results[source_name] = {
            'kept': kept,
            'filtered': filtered,
            'stats': {
                'original': len(urls),
                'kept': len(kept),
                'filtered': len(filtered),
                'filter_rate': (len(filtered) / len(urls) * 100) if urls else 0
            }
        }

        total_original += len(urls)
        total_kept += len(kept)
        total_filtered += len(filtered)

    print(f"\n{'='*100}")
    print(f"MALICIOUS URLs - Overall Statistics")
    print(f"{'='*100}")
    print(f"Total original: {total_original}")
    print(f"Total kept: {total_kept}")
    print(f"Total filtered: {total_filtered}")
    print(f"Filter rate: {(total_filtered / total_original * 100):.1f}%")

    return results


def load_and_filter_safe_urls(file_path: str) -> Dict[str, Any]:
    """Load safe URLs and filter out obvious ones (should be very few)."""
    print(f"\n\n{'='*100}")
    print(f"Filtering Safe URLs from: {file_path}")
    print(f"{'='*100}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    results = {}
    total_original = 0
    total_kept = 0
    total_filtered = 0

    for source_name, urls in data.get('sources', {}).items():
        print(f"\n[{source_name.upper()}]")
        print(f"Original count: {len(urls)}")

        kept, filtered = filter_numeric_urls(urls, threshold=75.0)

        print(f"Kept: {len(kept)}")
        print(f"Filtered out: {len(filtered)}")

        if filtered:
            print(f"\nFiltered URLs (unexpected for safe URLs!):")
            for entry in filtered:
                print(f"  ❌ {entry['url'][:80]}...")
                print(f"     Reason: {entry['filter_reason']}")

        results[source_name] = {
            'kept': kept,
            'filtered': filtered,
            'stats': {
                'original': len(urls),
                'kept': len(kept),
                'filtered': len(filtered),
                'filter_rate': (len(filtered) / len(urls) * 100) if urls else 0
            }
        }

        total_original += len(urls)
        total_kept += len(kept)
        total_filtered += len(filtered)

    print(f"\n{'='*100}")
    print(f"SAFE URLs - Overall Statistics")
    print(f"{'='*100}")
    print(f"Total original: {total_original}")
    print(f"Total kept: {total_kept}")
    print(f"Total filtered: {total_filtered}")
    print(f"Filter rate: {(total_filtered / total_original * 100):.1f}%")

    return results


def main():
    """Filter both malicious and safe URLs."""
    print("="*100)
    print("URL FILTERING - Remove URLs with >75% Numeric Characters")
    print("="*100)

    # Filter malicious URLs
    malicious_results = load_and_filter_malicious_urls("malicious_url_samples.json")

    # Filter safe URLs
    safe_results = load_and_filter_safe_urls("safe_url_samples.json")

    # Save filtered datasets
    print(f"\n\n{'='*100}")
    print("Saving Filtered Datasets")
    print(f"{'='*100}")

    # Save filtered malicious URLs
    malicious_output = {
        "filtered_at": "2024-12-04",
        "filter_criteria": {
            "numeric_threshold": 75.0,
            "description": "URLs with >75% numeric characters are filtered as obviously suspicious"
        },
        "sources": {}
    }

    for source_name, data in malicious_results.items():
        malicious_output['sources'][source_name] = {
            'urls': data['kept'],
            'stats': data['stats'],
            'filtered_urls': data['filtered']
        }

    with open("malicious_urls_filtered.json", 'w') as f:
        json.dump(malicious_output, f, indent=2)
    print("✓ Saved: malicious_urls_filtered.json")

    # Save filtered safe URLs
    safe_output = {
        "filtered_at": "2024-12-04",
        "filter_criteria": {
            "numeric_threshold": 75.0,
            "description": "URLs with >75% numeric characters are filtered"
        },
        "sources": {}
    }

    for source_name, data in safe_results.items():
        safe_output['sources'][source_name] = {
            'urls': data['kept'],
            'stats': data['stats'],
            'filtered_urls': data['filtered']
        }

    with open("safe_urls_filtered.json", 'w') as f:
        json.dump(safe_output, f, indent=2)
    print("✓ Saved: safe_urls_filtered.json")

    # Final summary
    total_malicious_kept = sum(d['stats']['kept'] for d in malicious_results.values())
    total_safe_kept = sum(d['stats']['kept'] for d in safe_results.values())

    print(f"\n\n{'='*100}")
    print("FINAL DATASET COMPOSITION")
    print(f"{'='*100}")
    print(f"Malicious URLs (after filtering): {total_malicious_kept}")
    print(f"Safe URLs (after filtering): {total_safe_kept}")
    print(f"Total URLs: {total_malicious_kept + total_safe_kept}")

    # Show examples of filtered URLs
    print(f"\n\n{'='*100}")
    print("Examples of Filtered (Overly Obvious) URLs")
    print(f"{'='*100}")

    for source_name, data in malicious_results.items():
        if data['filtered']:
            print(f"\n{source_name.upper()}:")
            for entry in data['filtered'][:3]:  # Show first 3
                print(f"  {entry['url']}")
                print(f"  └─ {entry['numeric_percentage']:.1f}% numeric")


if __name__ == "__main__":
    main()
