"""
Test script to run FTC scraper without requiring Reddit API credentials.
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.ftc_scraper import FTCScraper
from utils.database import ScamURLDatabase
from utils.url_extractor import URLExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Run FTC scraper test."""
    logger.info("=" * 60)
    logger.info("Testing FTC Scraper (No API credentials required)")
    logger.info("=" * 60)

    # Initialize database
    db = ScamURLDatabase('data/scam_urls.db')

    # Initialize FTC scraper
    logger.info("\nInitializing FTC scraper...")
    ftc = FTCScraper()

    # Scrape FTC
    logger.info("\nScraping FTC consumer alerts and news...")
    ftc_results = ftc.safe_scrape()

    logger.info(f"\nFound {len(ftc_results)} URL records from FTC")

    # Process and store URLs
    new_count = 0
    for record in ftc_results:
        try:
            url = record.get('url')
            if not url:
                continue

            url_normalized = URLExtractor.normalize_url(url)
            priority_score = db.calculate_priority_score(record)

            db_record = {
                'url': url,
                'url_normalized': url_normalized,
                'source': record.get('source', 'ftc'),
                'source_id': record.get('source_id'),
                'source_url': record.get('source_url'),
                'context': record.get('context'),
                'scam_type': record.get('scam_type'),
                'date_posted': record.get('date_posted'),
                'metadata': record.get('metadata', {}),
                'priority_score': priority_score
            }

            if db.insert_url(db_record):
                new_count += 1
                logger.info(f"  ✓ {url} (priority: {priority_score:.1f})")

        except Exception as e:
            logger.warning(f"Error processing URL: {e}")
            continue

    logger.info(f"\n✓ Added {new_count} new URLs to database")

    # Show statistics
    stats = db.get_statistics()
    logger.info("\n" + "=" * 60)
    logger.info("Database Statistics")
    logger.info("=" * 60)
    logger.info(f"Total URLs: {stats.get('total_urls', 0)}")
    logger.info(f"Pending investigation: {stats.get('pending_urls', 0)}")

    # Export top URLs
    if stats.get('total_urls', 0) > 0:
        logger.info("\nExporting URLs to JSON...")
        db.export_to_json('data/test_urls.json', limit=50)
        logger.info("✓ Exported to data/test_urls.json")

    # Show top 20 URLs
    logger.info("\n" + "=" * 60)
    logger.info("Top 20 URLs by Priority Score")
    logger.info("=" * 60)

    top_urls = db.get_pending_urls(limit=20)
    for i, url_rec in enumerate(top_urls, 1):
        logger.info(f"\n{i}. {url_rec['url']}")
        logger.info(f"   Priority: {url_rec['priority_score']:.1f}")
        logger.info(f"   Type: {url_rec['scam_type']}")
        logger.info(f"   Source: {url_rec['source_url']}")
        logger.info(f"   Context: {url_rec['context'][:100]}...")

    logger.info("\n" + "=" * 60)
    logger.info(f"✓ Test complete! Collected {new_count} URLs")
    logger.info("=" * 60)

if __name__ == '__main__':
    main()
