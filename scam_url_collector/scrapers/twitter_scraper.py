"""
Twitter/X scraper for collecting scam URLs from tweets.
Supports both snscrape (no API required) and tweepy (with API credentials).
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import snscrape.modules.twitter as sntwitter
    SNSCRAPE_AVAILABLE = True
except ImportError:
    SNSCRAPE_AVAILABLE = False

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

from .base_scraper import BaseScraper
from ..utils.url_extractor import URLExtractor
from ..utils.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X using snscrape or tweepy."""

    def __init__(
        self,
        use_api: bool = False,
        api_key: str = None,
        api_secret: str = None,
        access_token: str = None,
        access_secret: str = None,
        bearer_token: str = None
    ):
        """
        Initialize Twitter scraper.

        Args:
            use_api: Whether to use Twitter API (via tweepy)
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_secret: Twitter access token secret
            bearer_token: Twitter bearer token (for API v2)
        """
        super().__init__(rate_limit_delay=Config.SLEEP_BETWEEN_REQUESTS)

        self.use_api = use_api
        self.api = None
        self.client = None

        if use_api:
            if not TWEEPY_AVAILABLE:
                raise ImportError("tweepy is not installed. Install with: pip install tweepy")

            # Use provided credentials or fall back to config
            self.api_key = api_key or Config.TWITTER_API_KEY
            self.api_secret = api_secret or Config.TWITTER_API_SECRET
            self.access_token = access_token or Config.TWITTER_ACCESS_TOKEN
            self.access_secret = access_secret or Config.TWITTER_ACCESS_SECRET
            self.bearer_token = bearer_token or Config.TWITTER_BEARER_TOKEN

            try:
                # Initialize Twitter API v2 client
                if self.bearer_token:
                    self.client = tweepy.Client(bearer_token=self.bearer_token)
                    self.logger.info("Twitter API v2 client initialized")
                else:
                    # Fall back to v1.1 API
                    auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
                    auth.set_access_token(self.access_token, self.access_secret)
                    self.api = tweepy.API(auth, wait_on_rate_limit=True)
                    self.logger.info("Twitter API v1.1 initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Twitter API: {e}")
                raise
        else:
            if not SNSCRAPE_AVAILABLE:
                self.logger.warning("snscrape is not installed. Twitter scraping may not work.")
                self.logger.warning("Install with: pip install snscrape")
            else:
                self.logger.info("Using snscrape for Twitter scraping (no API required)")

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape URLs from Twitter using configured queries.

        Returns:
            List of URL records
        """
        all_results = []

        # Scrape each query
        for query in Config.TWITTER_QUERIES:
            self.logger.info(f"Scraping Twitter for: {query}")
            results = self.scrape_tweets(
                query=query,
                max_results=Config.TWITTER_TWEET_LIMIT,
                days_back=Config.TWITTER_DAYS_BACK
            )
            all_results.extend(results)
            self.rate_limit()

        # Also scrape from security researcher accounts
        for account in Config.TWITTER_SECURITY_ACCOUNTS[:3]:  # Limit to avoid rate limiting
            self.logger.info(f"Scraping tweets from @{account}")
            results = self.scrape_user_timeline(
                username=account,
                max_results=50,
                days_back=Config.TWITTER_DAYS_BACK
            )
            all_results.extend(results)
            self.rate_limit()

        self.logger.info(f"Twitter scraping complete. Found {len(all_results)} URL records")
        return all_results

    def scrape_tweets(
        self,
        query: str,
        max_results: int = 100,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Scrape tweets matching a search query.

        Args:
            query: Search query
            max_results: Maximum number of tweets
            days_back: How many days back to search

        Returns:
            List of URL records
        """
        if self.use_api and self.client:
            return self._scrape_with_api_v2(query, max_results, days_back)
        elif self.use_api and self.api:
            return self._scrape_with_api_v1(query, max_results, days_back)
        else:
            return self._scrape_with_snscrape(query, max_results, days_back)

    def _scrape_with_snscrape(
        self,
        query: str,
        max_results: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Scrape using snscrape (no API required)."""
        if not SNSCRAPE_AVAILABLE:
            self.logger.warning("snscrape not available, skipping")
            return []

        results = []
        since_date = datetime.now() - timedelta(days=days_back)

        try:
            # Build snscrape query
            scraper_query = f"{query} since:{since_date.strftime('%Y-%m-%d')} filter:links"

            scraper = sntwitter.TwitterSearchScraper(scraper_query)
            tweet_count = 0

            for tweet in scraper.get_items():
                if tweet_count >= max_results:
                    break

                # Extract URLs from tweet
                tweet_results = self._extract_urls_from_tweet({
                    'id': tweet.id,
                    'text': tweet.content or tweet.rawContent,
                    'created_at': tweet.date,
                    'user': tweet.user.username,
                    'retweet_count': tweet.retweetCount or 0,
                    'like_count': tweet.likeCount or 0,
                    'url': tweet.url
                })

                results.extend(tweet_results)
                tweet_count += 1

        except Exception as e:
            self.logger.error(f"Error scraping with snscrape: {e}", exc_info=True)

        return results

    def _scrape_with_api_v2(
        self,
        query: str,
        max_results: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Scrape using Twitter API v2."""
        results = []
        since_date = datetime.now() - timedelta(days=days_back)

        try:
            # Search recent tweets
            tweets = self.client.search_recent_tweets(
                query=f"{query} -is:retweet has:links",
                max_results=min(max_results, 100),  # API limit
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                start_time=since_date.isoformat() + 'Z'
            )

            if not tweets.data:
                return results

            for tweet in tweets.data:
                tweet_results = self._extract_urls_from_tweet({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'user': f"user_{tweet.author_id}",
                    'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                    'like_count': tweet.public_metrics.get('like_count', 0),
                    'url': f"https://twitter.com/i/web/status/{tweet.id}"
                })

                results.extend(tweet_results)

        except tweepy.TweepyException as e:
            self.logger.error(f"Twitter API error: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error scraping with API v2: {e}", exc_info=True)

        return results

    def _scrape_with_api_v1(
        self,
        query: str,
        max_results: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Scrape using Twitter API v1.1."""
        results = []
        since_date = datetime.now() - timedelta(days=days_back)

        try:
            # Search tweets
            tweets = tweepy.Cursor(
                self.api.search_tweets,
                q=f"{query} filter:links -filter:retweets",
                lang="en",
                result_type="recent",
                tweet_mode="extended"
            ).items(max_results)

            for tweet in tweets:
                # Check date
                if tweet.created_at < since_date:
                    continue

                tweet_results = self._extract_urls_from_tweet({
                    'id': tweet.id,
                    'text': tweet.full_text,
                    'created_at': tweet.created_at,
                    'user': tweet.user.screen_name,
                    'retweet_count': tweet.retweet_count,
                    'like_count': tweet.favorite_count,
                    'url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                })

                results.extend(tweet_results)

        except tweepy.TweepyException as e:
            self.logger.error(f"Twitter API error: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error scraping with API v1: {e}", exc_info=True)

        return results

    def scrape_user_timeline(
        self,
        username: str,
        max_results: int = 50,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Scrape tweets from a specific user's timeline.

        Args:
            username: Twitter username (without @)
            max_results: Maximum number of tweets
            days_back: How many days back

        Returns:
            List of URL records
        """
        if self.use_api:
            return self._scrape_user_with_api(username, max_results, days_back)
        else:
            return self._scrape_user_with_snscrape(username, max_results, days_back)

    def _scrape_user_with_snscrape(
        self,
        username: str,
        max_results: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Scrape user timeline with snscrape."""
        if not SNSCRAPE_AVAILABLE:
            return []

        results = []
        since_date = datetime.now() - timedelta(days=days_back)

        try:
            scraper = sntwitter.TwitterUserScraper(username)
            tweet_count = 0

            for tweet in scraper.get_items():
                if tweet_count >= max_results:
                    break

                if tweet.date < since_date:
                    break

                tweet_results = self._extract_urls_from_tweet({
                    'id': tweet.id,
                    'text': tweet.content or tweet.rawContent,
                    'created_at': tweet.date,
                    'user': username,
                    'retweet_count': tweet.retweetCount or 0,
                    'like_count': tweet.likeCount or 0,
                    'url': tweet.url
                })

                results.extend(tweet_results)
                tweet_count += 1

        except Exception as e:
            self.logger.error(f"Error scraping user @{username}: {e}", exc_info=True)

        return results

    def _scrape_user_with_api(
        self,
        username: str,
        max_results: int,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Scrape user timeline with Twitter API."""
        # Implementation similar to _scrape_with_api_v1/v2 but for user timeline
        # Simplified for brevity
        self.logger.warning("User timeline scraping with API not fully implemented")
        return []

    def _extract_urls_from_tweet(self, tweet_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract URLs from a tweet.

        Args:
            tweet_data: Dictionary containing tweet information

        Returns:
            List of URL records
        """
        results = []
        tweet_text = tweet_data.get('text', '')

        # Extract URLs
        urls = URLExtractor.extract_urls(tweet_text, include_bare_domains=True)

        for url in urls:
            # Clean and validate
            cleaned_url = URLExtractor.clean_url(url)

            if not URLExtractor.validate_url(cleaned_url):
                continue

            # Expand if shortened (especially t.co)
            if URLExtractor.is_url_shortener(cleaned_url):
                expanded = URLExtractor.expand_shortened_url(cleaned_url)
                if expanded:
                    cleaned_url = expanded

            # Create record
            record = self.create_record(
                url=cleaned_url,
                source='twitter',
                source_id=str(tweet_data.get('id')),
                source_url=tweet_data.get('url', f"https://twitter.com/i/web/status/{tweet_data.get('id')}"),
                context=tweet_text[:500],
                scam_type=self._classify_scam_type(tweet_text),
                date_posted=tweet_data.get('created_at'),
                metadata={
                    'username': tweet_data.get('user'),
                    'retweets': tweet_data.get('retweet_count', 0),
                    'likes': tweet_data.get('like_count', 0),
                    'engagement': tweet_data.get('retweet_count', 0) + tweet_data.get('like_count', 0)
                }
            )

            results.append(record)

        return results

    def _classify_scam_type(self, text: str) -> str:
        """Classify scam type based on keywords."""
        text_lower = text.lower()

        scam_keywords = {
            'phishing': ['phish', 'credential', 'login', 'password'],
            'crypto': ['bitcoin', 'crypto', 'wallet', 'nft'],
            'financial': ['money', 'payment', 'bank', 'wire'],
            'malware': ['malware', 'virus', 'trojan', 'infected']
        }

        for scam_type, keywords in scam_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return scam_type

        return 'unknown'
