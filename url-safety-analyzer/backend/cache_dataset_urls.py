#!/usr/bin/env python3
"""
Cache all URLs from the dataset for offline evaluation.
Verifies URLs are accessible and caches their content.
"""

import json
import asyncio
from url_cache import URLCache
from pathlib import Path
import sys


async def cache_dataset_urls(dataset_path: str, cache_dir: str = "./url_cache"):
    """Cache all URLs from the dataset."""

    # Load dataset
    print(f"Loading dataset from: {dataset_path}")
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    test_cases = dataset.get('test_cases', [])
    total_urls = len(test_cases)

    print(f"Total URLs to cache: {total_urls}")
    print(f"{'='*70}\n")

    # Initialize cache
    cache = URLCache(cache_dir=cache_dir)

    # Statistics
    stats = {
        'success': 0,
        'failed': 0,
        'already_cached': 0,
        'by_label': {}
    }

    # Cache each URL
    for i, test_case in enumerate(test_cases, 1):
        url = test_case['url']
        label = test_case['ground_truth_label']

        # Track by label
        if label not in stats['by_label']:
            stats['by_label'][label] = {'success': 0, 'failed': 0, 'cached': 0}

        # Check if already cached
        if cache.has_cached(url):
            print(f"[{i}/{total_urls}] ✓ CACHED: {url[:80]}")
            stats['already_cached'] += 1
            stats['by_label'][label]['cached'] += 1
            continue

        # Try to fetch and cache
        try:
            print(f"[{i}/{total_urls}] Fetching: {url[:80]}...")
            cached_data = await cache.get_or_fetch(url, timeout=15)

            if cached_data:
                stats['success'] += 1
                stats['by_label'][label]['success'] += 1
                print(f"  ✓ SUCCESS - Status: {cached_data.get('status_code', 'N/A')}, "
                      f"Size: {len(cached_data.get('html', ''))} bytes")
            else:
                stats['failed'] += 1
                stats['by_label'][label]['failed'] += 1
                print(f"  ✗ FAILED - Unable to fetch")

        except Exception as e:
            stats['failed'] += 1
            stats['by_label'][label]['failed'] += 1
            print(f"  ✗ ERROR - {str(e)[:100]}")

        # Small delay to avoid overwhelming servers
        if i % 10 == 0:
            await asyncio.sleep(1)

    # Print summary
    print(f"\n{'='*70}")
    print("CACHING COMPLETE")
    print(f"{'='*70}\n")

    print(f"Total URLs: {total_urls}")
    print(f"Already Cached: {stats['already_cached']}")
    print(f"Successfully Fetched: {stats['success']}")
    print(f"Failed to Fetch: {stats['failed']}")
    print(f"Cache Success Rate: {((stats['success'] + stats['already_cached']) / total_urls) * 100:.1f}%")

    print(f"\nBy Label:")
    for label, label_stats in sorted(stats['by_label'].items()):
        total = label_stats['success'] + label_stats['failed'] + label_stats['cached']
        success_rate = ((label_stats['success'] + label_stats['cached']) / total) * 100 if total > 0 else 0
        print(f"  {label}:")
        print(f"    Total: {total}")
        print(f"    Cached: {label_stats['cached']}")
        print(f"    Success: {label_stats['success']}")
        print(f"    Failed: {label_stats['failed']}")
        print(f"    Success Rate: {success_rate:.1f}%")

    # Show cache statistics
    print(f"\n{'='*70}")
    print(f"Cache Directory: {cache_dir}")
    cache_path = Path(cache_dir)
    if cache_path.exists():
        # Count cached entries
        entries_dir = cache_path / "entries"
        if entries_dir.exists():
            cached_count = len(list(entries_dir.iterdir()))
            print(f"Total Cached Entries: {cached_count}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dataset_path = "../test_datasets/real_world_test_dataset_500.json"
    else:
        dataset_path = sys.argv[1]

    cache_dir = "./url_cache"

    print(f"{'='*70}")
    print("URL Dataset Caching Tool")
    print(f"{'='*70}\n")

    asyncio.run(cache_dataset_urls(dataset_path, cache_dir))
