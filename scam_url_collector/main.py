"""
Main orchestrator for scam URL collection.
Coordinates all scrapers and manages the collection process.
"""
import logging
import argparse
import schedule
import time
from datetime import datetime
from typing import List, Dict, Any

from scrapers.reddit_scraper import RedditScraper
from scrapers.twitter_scraper import TwitterScraper
from scrapers.bbb_scraper import BBBScraper
from scrapers.ftc_scraper import FTCScraper
from utils.database import ScamURLDatabase
from utils.url_extractor import URLExtractor
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scam_url_collector/data/collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScamURLCollector:
    """Main collector orchestrating all scrapers."""

    def __init__(self, use_twitter_api: bool = False, skip_bbb: bool = False):
        """
        Initialize the collector.

        Args:
            use_twitter_api: Whether to use Twitter API (vs snscrape)
            skip_bbb: Skip BBB scraping (requires browser automation)
        """
        self.db = ScamURLDatabase(Config.DATABASE_PATH)
        self.skip_bbb = skip_bbb

        logger.info("Initializing scrapers...")

        # Initialize Reddit scraper (required)
        try:
            self.reddit = RedditScraper()
            logger.info("✓ Reddit scraper initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Reddit scraper: {e}")
            self.reddit = None

        # Initialize Twitter scraper (optional)
        try:
            self.twitter = TwitterScraper(use_api=use_twitter_api)
            logger.info(f"✓ Twitter scraper initialized (API: {use_twitter_api})")
        except Exception as e:
            logger.warning(f"✗ Twitter scraper not available: {e}")
            self.twitter = None

        # Initialize BBB scraper (optional, requires browser)
        if not skip_bbb:
            try:
                self.bbb = BBBScraper()
                logger.info("✓ BBB scraper initialized")
            except Exception as e:
                logger.warning(f"✗ BBB scraper not available: {e}")
                self.bbb = None
        else:
            self.bbb = None
            logger.info("BBB scraper skipped (--skip-bbb)")

        # Initialize FTC scraper (optional)
        try:
            self.ftc = FTCScraper()
            logger.info("✓ FTC scraper initialized")
        except Exception as e:
            logger.warning(f"✗ FTC scraper not available: {e}")
            self.ftc = None

        logger.info("Collector initialized\n")

    def run_collection_cycle(self):
        """Run a complete collection cycle across all sources."""
        logger.info("=" * 60)
        logger.info("Starting collection cycle...")
        logger.info("=" * 60)

        start_time = datetime.now()
        total_urls_collected = 0

        # Collect from Reddit
        if self.reddit:
            logger.info("\n--- Reddit Collection ---")
            try:
                reddit_urls = self.reddit.safe_scrape()
                count = self.process_urls(reddit_urls, 'reddit')
                total_urls_collected += count
                logger.info(f"Reddit: Processed {count} URL records")
            except Exception as e:
                logger.error(f"Error during Reddit collection: {e}", exc_info=True)

        # Collect from Twitter
        if self.twitter:
            logger.info("\n--- Twitter Collection ---")
            try:
                twitter_urls = self.twitter.safe_scrape()
                count = self.process_urls(twitter_urls, 'twitter')
                total_urls_collected += count
                logger.info(f"Twitter: Processed {count} URL records")
            except Exception as e:
                logger.error(f"Error during Twitter collection: {e}", exc_info=True)

        # Collect from BBB
        if self.bbb:
            logger.info("\n--- BBB Collection ---")
            try:
                bbb_urls = self.bbb.safe_scrape()
                count = self.process_urls(bbb_urls, 'bbb')
                total_urls_collected += count
                logger.info(f"BBB: Processed {count} URL records")
            except Exception as e:
                logger.error(f"Error during BBB collection: {e}", exc_info=True)

        # Collect from FTC
        if self.ftc:
            logger.info("\n--- FTC Collection ---")
            try:
                ftc_urls = self.ftc.safe_scrape()
                count = self.process_urls(ftc_urls, 'ftc')
                total_urls_collected += count
                logger.info(f"FTC: Processed {count} URL records")
            except Exception as e:
                logger.error(f"Error during FTC collection: {e}", exc_info=True)

        # Update priority scores
        logger.info("\n--- Updating Priority Scores ---")
        self.db.update_priority_scores()

        # Generate statistics
        stats = self.db.get_statistics()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("Collection Cycle Complete")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"URLs collected this cycle: {total_urls_collected}")
        logger.info(f"Total URLs in database: {stats.get('total_urls', 0)}")
        logger.info(f"Pending investigation: {stats.get('pending_urls', 0)}")
        logger.info(f"Added in last 24h: {stats.get('added_last_24h', 0)}")
        logger.info(f"\nURLs by source:")
        for source, count in stats.get('by_source', {}).items():
            logger.info(f"  {source}: {count}")
        logger.info("=" * 60 + "\n")

    def process_urls(self, url_records: List[Dict[str, Any]], source: str) -> int:
        """
        Process and store URL records in the database.

        Args:
            url_records: List of URL record dictionaries
            source: Source name

        Returns:
            Number of new URLs added
        """
        if not url_records:
            logger.info(f"No URLs to process from {source}")
            return 0

        new_count = 0

        for record in url_records:
            try:
                # Normalize URL for deduplication
                url = record.get('url')
                if not url:
                    continue

                url_normalized = URLExtractor.normalize_url(url)

                # Calculate priority score
                priority_score = self.db.calculate_priority_score(record)

                # Prepare record for database
                db_record = {
                    'url': url,
                    'url_normalized': url_normalized,
                    'source': record.get('source', source),
                    'source_id': record.get('source_id'),
                    'source_url': record.get('source_url'),
                    'context': record.get('context'),
                    'scam_type': record.get('scam_type'),
                    'date_posted': record.get('date_posted'),
                    'metadata': record.get('metadata', {}),
                    'priority_score': priority_score
                }

                # Insert into database
                if self.db.insert_url(db_record):
                    new_count += 1

            except Exception as e:
                logger.warning(f"Error processing URL record: {e}")
                continue

        logger.info(f"Added {new_count} new URLs from {source}")
        return new_count

    def export_for_investigation(self, output_file: str = None, limit: int = None):
        """
        Export URLs for investigation.

        Args:
            output_file: Output JSON file path
            limit: Maximum number of URLs to export
        """
        output_file = output_file or Config.EXPORT_PATH
        limit = limit or Config.EXPORT_LIMIT

        logger.info(f"Exporting top {limit} URLs to {output_file}")

        try:
            self.db.export_to_json(output_file, limit=limit)
            logger.info(f"✓ Export complete: {output_file}")
        except Exception as e:
            logger.error(f"✗ Export failed: {e}", exc_info=True)

    def print_statistics(self):
        """Print database statistics."""
        stats = self.db.get_statistics()

        print("\n" + "=" * 60)
        print("Database Statistics")
        print("=" * 60)
        print(f"Total URLs: {stats.get('total_urls', 0)}")
        print(f"Pending investigation: {stats.get('pending_urls', 0)}")
        print(f"Added in last 24h: {stats.get('added_last_24h', 0)}")
        print(f"\nURLs by source:")
        for source, count in stats.get('by_source', {}).items():
            print(f"  {source}: {count}")
        print("=" * 60 + "\n")

    def run_scheduled(self, interval_hours: int = None):
        """
        Run collector on a schedule.

        Args:
            interval_hours: Hours between collection cycles
        """
        interval_hours = interval_hours or Config.COLLECTION_INTERVAL_HOURS

        logger.info(f"Starting scheduled collection every {interval_hours} hours")
        logger.info("Press Ctrl+C to stop\n")

        # Run immediately on start
        self.run_collection_cycle()

        # Schedule subsequent runs
        schedule.every(interval_hours).hours.do(self.run_collection_cycle)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\nScheduled collection stopped by user")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scam URL Collector - Multi-source scraper for scam URLs'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run collection once and exit (default: run on schedule)'
    )

    parser.add_argument(
        '--export',
        action='store_true',
        help='Export URLs for investigation after collection'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print statistics and exit'
    )

    parser.add_argument(
        '--twitter-api',
        action='store_true',
        help='Use Twitter API instead of snscrape'
    )

    parser.add_argument(
        '--skip-bbb',
        action='store_true',
        help='Skip BBB scraping (avoids browser automation)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=None,
        help=f'Hours between collection cycles (default: {Config.COLLECTION_INTERVAL_HOURS})'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help=f'Output file for export (default: {Config.EXPORT_PATH})'
    )

    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration and exit'
    )

    args = parser.parse_args()

    # Print configuration
    Config.print_config()

    # Validate configuration
    if args.validate_config or not Config.validate():
        if args.validate_config:
            logger.info("Configuration validation complete")
        return

    # Initialize collector
    collector = ScamURLCollector(
        use_twitter_api=args.twitter_api,
        skip_bbb=args.skip_bbb
    )

    # Handle different modes
    if args.stats:
        # Just print statistics
        collector.print_statistics()

    elif args.once:
        # Run once and exit
        collector.run_collection_cycle()

        if args.export:
            collector.export_for_investigation(output_file=args.output)

        collector.print_statistics()

    else:
        # Run on schedule
        try:
            collector.run_scheduled(interval_hours=args.interval)
        finally:
            # Export on exit
            if args.export:
                collector.export_for_investigation(output_file=args.output)


if __name__ == '__main__':
    main()
