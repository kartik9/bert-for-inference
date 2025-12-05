"""
URL extraction, cleaning, and validation utilities.
"""
import re
import logging
import requests
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from requests.exceptions import RequestException, Timeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLExtractor:
    """Utility class for extracting, cleaning, and validating URLs."""

    # Comprehensive URL regex patterns
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )

    # Pattern for bare domains (without http/https)
    DOMAIN_PATTERN = re.compile(
        r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b',
        re.IGNORECASE
    )

    # Known URL shorteners
    URL_SHORTENERS = {
        'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
        'short.link', 'cutt.ly', 'bitly.com', 'rebrand.ly',
        'is.gd', 'buff.ly', 'adf.ly', 'bl.ink', 'lnkd.in'
    }

    # Tracking parameters to remove
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
        '_ga', '_gl', 'ref', 'source'
    }

    # Invalid/local domains to exclude
    EXCLUDED_DOMAINS = {
        'localhost', '127.0.0.1', '0.0.0.0', 'example.com',
        'test.com', 'reddit.com', 'twitter.com', 'x.com',
        'youtube.com', 'youtu.be', 'bbb.org', 'ftc.gov'
    }

    @classmethod
    def extract_urls(cls, text: str, include_bare_domains: bool = False) -> List[str]:
        """
        Extract all URLs from text.

        Args:
            text: Text to extract URLs from
            include_bare_domains: Whether to include bare domains without http://

        Returns:
            List of extracted URLs
        """
        if not text:
            return []

        urls = []

        # Extract URLs with http/https
        urls.extend(cls.URL_PATTERN.findall(text))

        # Optionally extract bare domains
        if include_bare_domains:
            potential_domains = cls.DOMAIN_PATTERN.findall(text)
            for domain in potential_domains:
                # Only include if it looks like a real domain (has valid TLD)
                if '.' in domain and not domain.startswith('.') and not domain.endswith('.'):
                    # Add http:// prefix
                    urls.append(f'http://{domain}')

        return list(set(urls))  # Remove duplicates

    @classmethod
    def clean_url(cls, url: str) -> str:
        """
        Clean and normalize a URL.

        Args:
            url: URL to clean

        Returns:
            Cleaned and normalized URL
        """
        if not url:
            return ''

        try:
            # Parse the URL
            parsed = urlparse(url)

            # Normalize scheme to https if http
            scheme = parsed.scheme.lower()
            if scheme not in ('http', 'https'):
                scheme = 'http'

            # Normalize domain to lowercase
            netloc = parsed.netloc.lower()

            # Remove tracking parameters
            if parsed.query:
                params = parse_qs(parsed.query)
                # Filter out tracking parameters
                clean_params = {
                    k: v for k, v in params.items()
                    if k.lower() not in cls.TRACKING_PARAMS
                }
                query = urlencode(clean_params, doseq=True)
            else:
                query = ''

            # Remove trailing slash from path
            path = parsed.path.rstrip('/')

            # Remove fragment
            fragment = ''

            # Reconstruct URL
            cleaned = urlunparse((
                scheme,
                netloc,
                path,
                parsed.params,
                query,
                fragment
            ))

            return cleaned

        except Exception as e:
            logger.warning(f"Error cleaning URL {url}: {e}")
            return url

    @classmethod
    def validate_url(cls, url: str, check_accessibility: bool = False) -> bool:
        """
        Validate if a URL is legitimate and not in excluded list.

        Args:
            url: URL to validate
            check_accessibility: Whether to check if URL is accessible (slower)

        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False

        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check if scheme is http or https
            if parsed.scheme not in ('http', 'https'):
                return False

            # Extract domain
            domain = parsed.netloc.lower()
            # Remove port if present
            domain = domain.split(':')[0]

            # Check against excluded domains
            for excluded in cls.EXCLUDED_DOMAINS:
                if domain == excluded or domain.endswith(f'.{excluded}'):
                    return False

            # Must have a valid TLD
            if '.' not in domain:
                return False

            # Optionally check accessibility
            if check_accessibility:
                try:
                    response = requests.head(
                        url,
                        timeout=5,
                        allow_redirects=True,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    return response.status_code < 500
                except RequestException:
                    return False

            return True

        except Exception as e:
            logger.warning(f"Error validating URL {url}: {e}")
            return False

    @classmethod
    def expand_shortened_url(cls, short_url: str, timeout: int = 5) -> Optional[str]:
        """
        Expand a shortened URL to its final destination.

        Args:
            short_url: Shortened URL to expand
            timeout: Request timeout in seconds

        Returns:
            Expanded URL or None if expansion fails
        """
        try:
            parsed = urlparse(short_url)
            domain = parsed.netloc.lower().replace('www.', '')

            # Check if it's a known URL shortener
            if domain not in cls.URL_SHORTENERS:
                return short_url

            # Follow redirects to get final URL
            response = requests.head(
                short_url,
                allow_redirects=True,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            return response.url

        except Timeout:
            logger.warning(f"Timeout expanding URL: {short_url}")
            return None
        except RequestException as e:
            logger.warning(f"Error expanding URL {short_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error expanding URL {short_url}: {e}")
            return None

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """
        Normalize URL for deduplication purposes.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL string
        """
        # Clean the URL
        cleaned = cls.clean_url(url)

        # Parse and extract key components
        parsed = urlparse(cleaned)

        # Create normalized version: lowercase domain + path
        normalized = f"{parsed.netloc.lower()}{parsed.path.lower()}"

        return normalized

    @classmethod
    def is_url_shortener(cls, url: str) -> bool:
        """
        Check if URL is from a known URL shortening service.

        Args:
            url: URL to check

        Returns:
            True if URL is from a shortener service
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            return domain in cls.URL_SHORTENERS
        except:
            return False

    @classmethod
    def extract_domain(cls, url: str) -> Optional[str]:
        """
        Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string or None
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            # Remove port
            domain = domain.split(':')[0]
            return domain
        except:
            return None
