"""
Ad Platform Transparency Checker
Checks if URLs/domains are being advertised on Google Ads and Meta Ad Library
Provides advertiser information and ad content for trust & safety analysis
"""

import os
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import json
import re

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class AdPlatformChecker:
    """
    Checks ad platform transparency centers for domain advertising activity
    """

    def __init__(self):
        self.timeout = httpx.Timeout(15.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Initialize OpenAI for content extraction
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not configured - AI extraction disabled")

    async def check_ad_platforms(
        self,
        url: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Check if domain/URL is advertised on Google Ads and Meta platforms

        Args:
            url: Full URL being investigated
            domain: Extracted domain name

        Returns: Dictionary with ad platform findings
        """
        logger.info(f"Checking ad platforms for: {domain}")

        results = {
            "checked": True,
            "domain": domain,
            "google_ads": await self._check_google_ads_transparency(domain),
            "meta_ads": await self._check_meta_ad_library(domain)
        }

        # Summarize findings
        results["summary"] = self._summarize_ad_findings(results)

        return results

    async def _check_google_ads_transparency(self, domain: str) -> Dict[str, Any]:
        """
        Check Google Ads Transparency Center for domain
        """
        logger.info(f"Checking Google Ads Transparency Center for: {domain}")

        result = {
            "checked": True,
            "found_ads": False,
            "search_performed": True,
            "advertisers": [],
            "ad_count": 0,
            "source": "Google Ads Transparency Center"
        }

        try:
            # Google Ads Transparency Center URL
            # Note: This uses web search approach since direct API may require auth
            search_url = f"https://adstransparency.google.com/"

            # Use web search to find if domain is advertised
            search_query = f"site:adstransparency.google.com {domain}"

            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # Try to search for the domain in Google Ads Transparency
                # This is a simplified approach - in production you'd use the actual API
                search_response = await client.get(
                    f"https://www.google.com/search?q={search_query}",
                    follow_redirects=True
                )

                if search_response.status_code == 200:
                    # Check if results mention the domain
                    content = search_response.text.lower()
                    if domain.lower() in content and "advertiser" in content:
                        result["found_ads"] = True
                        result["detection_method"] = "search_detection"

                        # Extract basic info if available
                        if self.openai_client:
                            extracted = await self._extract_google_ads_info(
                                search_response.text,
                                domain
                            )
                            result.update(extracted)

        except Exception as e:
            logger.error(f"Error checking Google Ads Transparency: {str(e)}")
            result["error"] = str(e)
            result["search_performed"] = False

        return result

    async def _check_meta_ad_library(self, domain: str) -> Dict[str, Any]:
        """
        Check Meta Ad Library for domain
        """
        logger.info(f"Checking Meta Ad Library for: {domain}")

        result = {
            "checked": True,
            "found_ads": False,
            "search_performed": True,
            "advertisers": [],
            "ad_count": 0,
            "source": "Meta Ad Library"
        }

        try:
            # Meta Ad Library URL (publicly accessible)
            # Search for domain in ad library
            search_query = f"site:facebook.com/ads/library {domain}"

            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # Search approach to find domain in Meta Ad Library
                search_response = await client.get(
                    f"https://www.google.com/search?q={search_query}",
                    follow_redirects=True
                )

                if search_response.status_code == 200:
                    content = search_response.text.lower()
                    if domain.lower() in content and ("ad" in content or "advertiser" in content):
                        result["found_ads"] = True
                        result["detection_method"] = "search_detection"

                        # Extract info if available
                        if self.openai_client:
                            extracted = await self._extract_meta_ads_info(
                                search_response.text,
                                domain
                            )
                            result.update(extracted)

        except Exception as e:
            logger.error(f"Error checking Meta Ad Library: {str(e)}")
            result["error"] = str(e)
            result["search_performed"] = False

        return result

    async def _extract_google_ads_info(
        self,
        page_content: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Use AI to extract Google Ads information from search results
        """
        try:
            # Clean HTML
            soup = BeautifulSoup(page_content, 'lxml')
            text = soup.get_text(separator=' ', strip=True)[:5000]

            prompt = f"""Extract Google Ads information about domain: {domain}

Page content from Google Ads Transparency search:
{text}

Extract any information about ads for this domain. Return ONLY JSON:
{{
  "advertisers": ["List of advertiser names found"],
  "ad_count": estimated_number_or_0,
  "ad_examples": ["Examples of ad text if found"],
  "advertiser_info": "Any info about who is advertising",
  "regions": ["Regions/countries if mentioned"],
  "platforms": ["Platforms where ads shown if mentioned"]
}}"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract ad platform information from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error extracting Google Ads info: {str(e)}")
            return {}

    async def _extract_meta_ads_info(
        self,
        page_content: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Use AI to extract Meta Ad Library information
        """
        try:
            soup = BeautifulSoup(page_content, 'lxml')
            text = soup.get_text(separator=' ', strip=True)[:5000]

            prompt = f"""Extract Meta/Facebook Ad Library information about domain: {domain}

Page content from Meta Ad Library search:
{text}

Extract any information about ads for this domain. Return ONLY JSON:
{{
  "advertisers": ["List of advertiser/page names found"],
  "ad_count": estimated_number_or_0,
  "ad_examples": ["Examples of ad text if found"],
  "advertiser_info": "Any info about who is advertising",
  "regions": ["Regions/countries if mentioned"],
  "platforms": ["Facebook/Instagram/etc if mentioned"]
}}"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract ad platform information from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error extracting Meta ads info: {str(e)}")
            return {}

    def _summarize_ad_findings(self, results: Dict[str, Any]) -> str:
        """
        Create human-readable summary of ad platform findings
        """
        summary_parts = []

        google = results.get("google_ads", {})
        meta = results.get("meta_ads", {})

        if google.get("found_ads"):
            advertiser_count = len(google.get("advertisers", []))
            summary_parts.append(
                f"Found on Google Ads ({advertiser_count} advertiser(s))"
            )

        if meta.get("found_ads"):
            advertiser_count = len(meta.get("advertisers", []))
            summary_parts.append(
                f"Found on Meta Ad Library ({advertiser_count} advertiser(s))"
            )

        if not summary_parts:
            return "No active advertising detected on major platforms"

        return " | ".join(summary_parts)
