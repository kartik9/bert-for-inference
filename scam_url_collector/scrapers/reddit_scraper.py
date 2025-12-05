"""
Reddit scraper for collecting scam URLs from relevant subreddits.
"""
import praw
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from .base_scraper import BaseScraper
from ..utils.url_extractor import URLExtractor
from ..utils.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    """Scraper for Reddit using PRAW."""

    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        """
        Initialize Reddit scraper.

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        super().__init__(rate_limit_delay=Config.SLEEP_BETWEEN_REQUESTS)

        # Use provided credentials or fall back to config
        self.client_id = client_id or Config.REDDIT_CLIENT_ID
        self.client_secret = client_secret or Config.REDDIT_CLIENT_SECRET
        self.user_agent = user_agent or Config.REDDIT_USER_AGENT

        # Validate credentials
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials are required")

        # Initialize PRAW
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            # Test connection
            self.reddit.user.me()
            self.logger.info("Reddit API connection established")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit API: {e}")
            raise

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape URLs from all configured subreddits.

        Returns:
            List of URL records
        """
        all_results = []

        # Scrape each subreddit
        for subreddit_name in Config.SUBREDDITS:
            self.logger.info(f"Scraping r/{subreddit_name}")
            results = self.scrape_subreddit(
                subreddit_name,
                limit=Config.REDDIT_POST_LIMIT,
                days_back=Config.REDDIT_DAYS_BACK
            )
            all_results.extend(results)
            self.rate_limit()

        self.logger.info(f"Reddit scraping complete. Found {len(all_results)} URL records")
        return all_results

    def scrape_subreddit(
        self,
        subreddit_name: str,
        limit: int = 100,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Scrape a specific subreddit.

        Args:
            subreddit_name: Name of subreddit
            limit: Maximum number of posts to scrape
            days_back: How many days back to search

        Returns:
            List of URL records
        """
        results = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Get new and hot posts
            posts = []

            # Get hot posts
            try:
                posts.extend(list(subreddit.hot(limit=limit // 2)))
            except Exception as e:
                self.logger.warning(f"Error getting hot posts from r/{subreddit_name}: {e}")

            # Get new posts
            try:
                posts.extend(list(subreddit.new(limit=limit // 2)))
            except Exception as e:
                self.logger.warning(f"Error getting new posts from r/{subreddit_name}: {e}")

            # Also search with keywords
            for keyword in Config.REDDIT_KEYWORDS[:3]:  # Limit to avoid rate limiting
                try:
                    search_results = subreddit.search(
                        keyword,
                        sort='new',
                        time_filter='week',
                        limit=20
                    )
                    posts.extend(list(search_results))
                    self.rate_limit()
                except Exception as e:
                    self.logger.warning(f"Error searching r/{subreddit_name} for '{keyword}': {e}")

            # Remove duplicates based on post ID
            seen_ids = set()
            unique_posts = []
            for post in posts:
                if post.id not in seen_ids:
                    seen_ids.add(post.id)
                    unique_posts.append(post)

            # Process each post
            for submission in unique_posts:
                try:
                    # Check if post is recent enough
                    post_date = datetime.fromtimestamp(submission.created_utc)
                    if post_date < cutoff_date:
                        continue

                    # Extract URLs from submission
                    submission_results = self.extract_urls_from_post(submission, subreddit_name)
                    results.extend(submission_results)

                except Exception as e:
                    self.logger.warning(f"Error processing submission {submission.id}: {e}")
                    continue

            self.logger.info(f"Found {len(results)} URLs in r/{subreddit_name}")

        except Exception as e:
            self.logger.error(f"Error scraping r/{subreddit_name}: {e}", exc_info=True)

        return results

    def extract_urls_from_post(
        self,
        submission: praw.models.Submission,
        subreddit_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extract URLs from a Reddit submission and its comments.

        Args:
            submission: Reddit submission object
            subreddit_name: Name of subreddit

        Returns:
            List of URL records
        """
        results = []

        # Combine title and selftext for context
        post_text = f"{submission.title}\n{submission.selftext}"

        # Extract URLs from post
        urls = URLExtractor.extract_urls(post_text, include_bare_domains=True)

        for url in urls:
            # Clean and validate URL
            cleaned_url = URLExtractor.clean_url(url)

            if not URLExtractor.validate_url(cleaned_url):
                continue

            # Expand if shortened
            if URLExtractor.is_url_shortener(cleaned_url):
                expanded = URLExtractor.expand_shortened_url(cleaned_url)
                if expanded:
                    cleaned_url = expanded

            # Create record
            record = self.create_record(
                url=cleaned_url,
                source='reddit',
                source_id=submission.id,
                source_url=f"https://reddit.com{submission.permalink}",
                context=post_text[:500],
                scam_type=self._classify_scam_type(post_text),
                date_posted=datetime.fromtimestamp(submission.created_utc),
                metadata={
                    'subreddit': subreddit_name,
                    'title': submission.title,
                    'upvotes': submission.score,
                    'num_comments': submission.num_comments,
                    'author': str(submission.author) if submission.author else '[deleted]'
                }
            )

            results.append(record)

        # Extract URLs from comments (top-level only to avoid overwhelming)
        try:
            submission.comments.replace_more(limit=0)  # Don't expand "load more comments"

            for comment in submission.comments[:10]:  # Limit to top 10 comments
                try:
                    comment_text = comment.body

                    # Extract URLs from comment
                    comment_urls = URLExtractor.extract_urls(comment_text, include_bare_domains=True)

                    for url in comment_urls:
                        cleaned_url = URLExtractor.clean_url(url)

                        if not URLExtractor.validate_url(cleaned_url):
                            continue

                        # Expand if shortened
                        if URLExtractor.is_url_shortener(cleaned_url):
                            expanded = URLExtractor.expand_shortened_url(cleaned_url)
                            if expanded:
                                cleaned_url = expanded

                        # Create record
                        record = self.create_record(
                            url=cleaned_url,
                            source='reddit',
                            source_id=f"{submission.id}_{comment.id}",
                            source_url=f"https://reddit.com{submission.permalink}{comment.id}",
                            context=f"Comment: {comment_text[:400]}",
                            scam_type=self._classify_scam_type(comment_text),
                            date_posted=datetime.fromtimestamp(comment.created_utc),
                            metadata={
                                'subreddit': subreddit_name,
                                'post_title': submission.title,
                                'comment_score': comment.score,
                                'author': str(comment.author) if comment.author else '[deleted]',
                                'is_comment': True
                            }
                        )

                        results.append(record)

                except Exception as e:
                    self.logger.debug(f"Error processing comment: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Error processing comments for submission {submission.id}: {e}")

        return results

    def _classify_scam_type(self, text: str) -> str:
        """
        Attempt to classify scam type based on keywords in text.

        Args:
            text: Text to analyze

        Returns:
            Scam type or None
        """
        text_lower = text.lower()

        scam_keywords = {
            'phishing': ['phish', 'credential', 'login', 'password', 'account'],
            'financial': ['money', 'payment', 'bank', 'credit card', 'wire transfer', 'paypal', 'venmo'],
            'crypto': ['bitcoin', 'crypto', 'ethereum', 'wallet', 'nft', 'blockchain'],
            'identity_theft': ['ssn', 'social security', 'identity', 'personal info', 'id theft'],
            'tech_support': ['tech support', 'microsoft', 'apple', 'computer virus', 'refund'],
            'romance': ['dating', 'romance', 'lonely', 'relationship', 'love'],
            'job': ['job offer', 'employment', 'work from home', 'easy money', 'mlm'],
            'shopping': ['fake product', 'counterfeit', 'never received', 'fake store'],
            'malware': ['malware', 'virus', 'trojan', 'ransomware', 'infected']
        }

        for scam_type, keywords in scam_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return scam_type

        return 'unknown'

    def search_by_keyword(
        self,
        keyword: str,
        subreddit_name: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search Reddit for a specific keyword.

        Args:
            keyword: Keyword to search for
            subreddit_name: Specific subreddit to search (None for all)
            limit: Maximum results

        Returns:
            List of URL records
        """
        results = []

        try:
            if subreddit_name:
                subreddit = self.reddit.subreddit(subreddit_name)
            else:
                subreddit = self.reddit.subreddit('all')

            search_results = subreddit.search(
                keyword,
                sort='new',
                time_filter='month',
                limit=limit
            )

            for submission in search_results:
                submission_results = self.extract_urls_from_post(
                    submission,
                    subreddit_name or 'all'
                )
                results.extend(submission_results)
                self.rate_limit()

        except Exception as e:
            self.logger.error(f"Error searching for keyword '{keyword}': {e}", exc_info=True)

        return results
