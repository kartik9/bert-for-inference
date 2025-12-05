"""
Configuration management for scam URL collector.
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration settings for the scam URL collector."""

    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', '')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'ScamURLCollector/1.0')

    # Twitter API Configuration (optional)
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET', '')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')

    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'scam_url_collector/data/scam_urls.db')

    # Target Subreddits
    SUBREDDITS: List[str] = [
        'Scams',
        'scambait',
        'phishing',
        'cybersecurity',
        'antiMLM',
        'personalfinance',
        'scambusters',
        'CyberSecurity',
        'netsec',
        'privacy'
    ]

    # Reddit Search Keywords
    REDDIT_KEYWORDS: List[str] = [
        'is this legit',
        'suspicious link',
        'got this url',
        'phishing site',
        'scam website',
        'fake website',
        'is this a scam',
        'sketchy website',
        'fraudulent site',
        'malicious link'
    ]

    # Twitter Search Queries
    TWITTER_QUERIES: List[str] = [
        '(scam OR phishing) url',
        'suspicious link',
        'phishing website',
        'scam website',
        'malicious site',
        'fraud url',
        'fake website scam'
    ]

    # Twitter accounts to monitor (security researchers, scam alerts)
    TWITTER_SECURITY_ACCOUNTS: List[str] = [
        'phishingalert',
        'ScamAdviser',
        'CyberScamAlert',
        'FraudWatch',
        'PhishLabs'
    ]

    # Rate Limiting Configuration
    REQUESTS_PER_MINUTE = int(os.getenv('REQUESTS_PER_MINUTE', '30'))
    SLEEP_BETWEEN_REQUESTS = float(os.getenv('SLEEP_BETWEEN_REQUESTS', '2.0'))

    # URL Validation Configuration
    TIMEOUT_SECONDS = int(os.getenv('TIMEOUT_SECONDS', '5'))
    MAX_REDIRECTS = int(os.getenv('MAX_REDIRECTS', '3'))
    CHECK_URL_ACCESSIBILITY = os.getenv('CHECK_URL_ACCESSIBILITY', 'false').lower() == 'true'

    # Scraping Configuration
    REDDIT_POST_LIMIT = int(os.getenv('REDDIT_POST_LIMIT', '100'))
    REDDIT_DAYS_BACK = int(os.getenv('REDDIT_DAYS_BACK', '7'))

    TWITTER_TWEET_LIMIT = int(os.getenv('TWITTER_TWEET_LIMIT', '100'))
    TWITTER_DAYS_BACK = int(os.getenv('TWITTER_DAYS_BACK', '7'))

    BBB_PAGES_TO_SCRAPE = int(os.getenv('BBB_PAGES_TO_SCRAPE', '10'))

    FTC_DAYS_BACK = int(os.getenv('FTC_DAYS_BACK', '30'))

    # Browser Configuration (for BBB scraping)
    HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'true').lower() == 'true'
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chromium')  # chromium, firefox, webkit

    # Scheduling Configuration
    COLLECTION_INTERVAL_HOURS = int(os.getenv('COLLECTION_INTERVAL_HOURS', '6'))

    # Export Configuration
    EXPORT_LIMIT = int(os.getenv('EXPORT_LIMIT', '500'))
    EXPORT_PATH = os.getenv('EXPORT_PATH', 'scam_url_collector/data/urls_to_investigate.json')

    @classmethod
    def validate(cls) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid
        """
        errors = []

        # Reddit API is required
        if not cls.REDDIT_CLIENT_ID or not cls.REDDIT_CLIENT_SECRET:
            errors.append("Reddit API credentials are required (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)")

        # Twitter API is optional, but if one is set, warn about others
        twitter_creds = [
            cls.TWITTER_API_KEY,
            cls.TWITTER_API_SECRET,
            cls.TWITTER_ACCESS_TOKEN,
            cls.TWITTER_ACCESS_SECRET
        ]

        if any(twitter_creds) and not all(twitter_creds):
            errors.append("If using Twitter API, all credentials must be set (API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)")

        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    @classmethod
    def print_config(cls):
        """Print current configuration (masking sensitive data)."""
        def mask_secret(value: str) -> str:
            """Mask sensitive values."""
            if not value:
                return '<not set>'
            if len(value) <= 8:
                return '*' * len(value)
            return value[:4] + '*' * (len(value) - 8) + value[-4:]

        print("\n=== Configuration ===")
        print(f"Reddit Client ID: {mask_secret(cls.REDDIT_CLIENT_ID)}")
        print(f"Reddit Client Secret: {mask_secret(cls.REDDIT_CLIENT_SECRET)}")
        print(f"Reddit User Agent: {cls.REDDIT_USER_AGENT}")
        print(f"\nTwitter API Key: {mask_secret(cls.TWITTER_API_KEY)}")
        print(f"Twitter Bearer Token: {mask_secret(cls.TWITTER_BEARER_TOKEN)}")
        print(f"\nDatabase Path: {cls.DATABASE_PATH}")
        print(f"Target Subreddits: {len(cls.SUBREDDITS)}")
        print(f"Reddit Keywords: {len(cls.REDDIT_KEYWORDS)}")
        print(f"Twitter Queries: {len(cls.TWITTER_QUERIES)}")
        print(f"\nRate Limiting: {cls.REQUESTS_PER_MINUTE} req/min, {cls.SLEEP_BETWEEN_REQUESTS}s delay")
        print(f"Reddit Post Limit: {cls.REDDIT_POST_LIMIT}")
        print(f"Twitter Tweet Limit: {cls.TWITTER_TWEET_LIMIT}")
        print(f"Collection Interval: {cls.COLLECTION_INTERVAL_HOURS} hours")
        print(f"Headless Browser: {cls.HEADLESS_BROWSER}")
        print("====================\n")
