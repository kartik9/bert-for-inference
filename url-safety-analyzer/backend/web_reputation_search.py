"""
Web Reputation Search Module
Searches the web for reputation information, scam complaints, and reviews about URLs
"""

import os
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebReputationSearcher:
    """
    Searches the web for reputation information about URLs
    Supports multiple search backends
    """

    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Configure search backend
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.google_cse_key = os.getenv('GOOGLE_CSE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')

    def is_configured(self) -> bool:
        """Check if at least one search backend is configured"""
        return any([self.brave_api_key, self.serpapi_key,
                    (self.google_cse_key and self.google_cse_id)])

    async def search_reputation(
        self,
        url: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for reputation information about a URL/domain
        Uses context from preliminary analysis for intelligent query generation

        Args:
            url: Full URL to analyze
            domain: Extracted domain name
            context: Analysis context including url_structure, content_analysis, ssl_info

        Returns aggregated findings from multiple search queries
        """
        logger.info(f"Starting context-aware reputation search for: {domain}")

        results = {
            "search_performed": True,
            "queries_used": [],
            "scam_indicators": [],
            "reputation_findings": [],
            "user_complaints": [],
            "review_summary": {},
            "news_mentions": [],
            "search_backend": self._get_backend_name(),
            "total_results_analyzed": 0,
            "query_strategy": "dynamic" if context else "static"
        }

        # Generate search queries (dynamic based on context)
        queries = self._generate_search_queries(url, domain, context)
        results["queries_used"] = queries

        if context:
            logger.info(f"Generated {len(queries)} context-aware queries")

        # Execute searches
        for query in queries:
            try:
                search_results = await self._execute_search(query)
                if search_results:
                    parsed = self._parse_search_results(query, search_results, domain)
                    self._merge_findings(results, parsed)
                    results["total_results_analyzed"] += len(search_results)
            except Exception as e:
                logger.error(f"Search error for query '{query}': {str(e)}")
                continue

        # Analyze and score findings
        results["reputation_score"] = self._calculate_reputation_score(results)
        results["risk_level"] = self._assess_risk_level(results)

        return results

    def _generate_search_queries(
        self,
        url: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate dynamic, context-aware search queries

        Uses preliminary analysis to intelligently select and prioritize queries
        """
        if not context:
            # Fall back to static queries if no context
            return self._generate_static_queries(domain)

        queries = []
        query_scores = []  # Track priority scores for each query

        # Extract context data
        url_structure = context.get("url_structure", {})
        content_analysis = context.get("content_analysis", {})
        ssl_info = context.get("ssl_info", {})
        suspicious_patterns = url_structure.get("suspicious_patterns", [])

        # Detect threat type and brand impersonation
        threat_type = self._detect_threat_type(url_structure, content_analysis, ssl_info)
        detected_brands = self._detect_brand_keywords(url, url_structure, content_analysis)

        logger.info(f"Detected threat type: {threat_type}, brands: {detected_brands}")

        # === BRAND IMPERSONATION QUERIES (Highest Priority) ===
        if detected_brands:
            for brand in detected_brands:
                queries.append((f'"{domain}" {brand} phishing', 100))
                queries.append((f'"{domain}" {brand} fake', 95))
                queries.append((f'"{domain}" impersonating {brand}', 90))
                queries.append((f'{brand} phishing "{domain}"', 85))

        # === THREAT-SPECIFIC QUERIES (High Priority) ===
        if threat_type == "phishing":
            queries.append((f'"{domain}" phishing', 90))
            queries.append((f'"{domain}" credential theft', 85))
            queries.append((f'"{domain}" password stolen', 80))
            queries.append((f'"{domain}" fake login', 75))

        elif threat_type == "malware":
            queries.append((f'"{domain}" malware', 90))
            queries.append((f'"{domain}" virus', 85))
            queries.append((f'"{domain}" trojan', 80))
            queries.append((f'"{domain}" infected', 75))

        elif threat_type == "scam":
            queries.append((f'"{domain}" scam', 90))
            queries.append((f'"{domain}" fraud', 85))
            queries.append((f'"{domain}" "lost money"', 80))
            queries.append((f'"{domain}" "did not receive"', 75))

        elif threat_type == "ecommerce_scam":
            queries.append((f'"{domain}" scam', 85))
            queries.append((f'"{domain}" "never received"', 80))
            queries.append((f'"{domain}" "no refund"', 75))
            queries.append((f'"{domain}" "fake products"', 70))

        # === SUSPICIOUS PATTERN QUERIES (Medium-High Priority) ===
        if "suspicious_tld" in str(suspicious_patterns):
            queries.append((f'"{domain}" scam', 75))
            queries.append((f'"{domain}" fraud', 70))

        if "url_shortener" in str(suspicious_patterns):
            queries.append((f'"{domain}" redirect scam', 70))

        if url_structure.get("has_ip"):
            queries.append((f'"{domain}" phishing IP', 75))

        # === SECURITY ISSUE QUERIES (Medium Priority) ===
        if not ssl_info.get("has_ssl"):
            queries.append((f'"{domain}" no ssl unsafe', 60))
            queries.append((f'"{domain}" security risk', 55))

        # === GENERAL REPUTATION QUERIES (Standard Priority) ===
        # Always include some general queries
        queries.append((f'"{domain}" scam', 50))
        queries.append((f'"{domain}" fraud', 48))
        queries.append((f'"{domain}" complaint', 45))
        queries.append((f'"{domain}" review', 40))

        # === VICTIM REPORT QUERIES (Medium Priority) ===
        queries.append((f'"{domain}" "lost money"', 55))
        queries.append((f'"{domain}" "did not receive"', 50))

        # === REPUTATION SITE QUERIES (Lower Priority unless high risk) ===
        priority = 60 if threat_type in ["phishing", "scam"] else 35
        queries.append((f'site:reddit.com "{domain}"', priority))
        queries.append((f'site:trustpilot.com "{domain}"', priority - 5))
        queries.append((f'site:bbb.org "{domain}"', priority - 10))

        # === POSITIVE QUERIES (Only for low-risk URLs) ===
        if threat_type == "unknown" and len(suspicious_patterns) == 0:
            queries.append((f'"{domain}" legitimate', 30))
            queries.append((f'"{domain}" trustworthy', 25))
            queries.append((f'"{domain}" safe', 20))

        # Sort by priority (highest first) and deduplicate
        queries = sorted(set(queries), key=lambda x: x[1], reverse=True)

        # Determine query limit based on threat level
        if threat_type in ["phishing", "malware", "scam"] or detected_brands:
            query_limit = 15  # High-risk: more thorough search
        elif len(suspicious_patterns) > 0:
            query_limit = 12  # Medium-risk: standard search
        else:
            query_limit = 8  # Low-risk: basic search

        # Extract just the query strings (remove scores)
        final_queries = [q[0] for q in queries[:query_limit]]

        logger.info(f"Query strategy: {query_limit} queries for threat_type={threat_type}")

        return final_queries

    def _generate_static_queries(self, domain: str) -> List[str]:
        """Generate static queries when no context is available (fallback)"""
        return [
            f'"{domain}" scam',
            f'"{domain}" fraud',
            f'"{domain}" phishing',
            f'"{domain}" complaint',
            f'"{domain}" review',
            f'"{domain}" "lost money"',
            f'site:reddit.com "{domain}"',
            f'site:trustpilot.com "{domain}"',
        ][:8]  # Conservative limit without context

    def _detect_threat_type(
        self,
        url_structure: Dict[str, Any],
        content_analysis: Dict[str, Any],
        ssl_info: Dict[str, Any]
    ) -> str:
        """
        Detect likely threat type based on technical indicators

        Returns: "phishing", "malware", "scam", "ecommerce_scam", or "unknown"
        """
        suspicious_patterns = url_structure.get("suspicious_patterns", [])
        forms_count = content_analysis.get("forms_count", 0)
        iframes = content_analysis.get("iframes_count", 0)
        title = content_analysis.get("title", "").lower()

        # Check for phishing indicators
        phishing_score = 0
        if "suspicious_keywords" in str(suspicious_patterns):
            phishing_score += 2
        if forms_count > 0 and ("login" in title or "signin" in title or "verify" in title):
            phishing_score += 3
        if not ssl_info.get("has_ssl") and forms_count > 0:
            phishing_score += 2
        if "external_form_submission" in content_analysis.get("suspicious_content", []):
            phishing_score += 3

        if phishing_score >= 4:
            return "phishing"

        # Check for malware indicators
        if iframes > 2:
            return "malware"
        if content_analysis.get("external_scripts_count", 0) > 10:
            return "malware"

        # Check for e-commerce scam indicators
        ecommerce_keywords = ["shop", "store", "buy", "cheap", "deal", "sale"]
        if any(kw in title for kw in ecommerce_keywords):
            if "suspicious_tld" in str(suspicious_patterns):
                return "ecommerce_scam"

        # Check for general scam indicators
        if "suspicious_tld" in str(suspicious_patterns):
            return "scam"
        if len(suspicious_patterns) >= 3:
            return "scam"

        return "unknown"

    def _detect_brand_keywords(
        self,
        url: str,
        url_structure: Dict[str, Any],
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Detect brand names that might be impersonated

        Returns list of detected brand names
        """
        detected_brands = []
        url_lower = url.lower()
        title = content_analysis.get("title", "").lower()

        # Major brands to check for
        brand_list = {
            "paypal": ["paypal", "pypal", "paypai", "paypa1"],
            "amazon": ["amazon", "amaz0n", "amazom"],
            "apple": ["apple", "appl", "icloud"],
            "microsoft": ["microsoft", "windows", "outlook", "office365"],
            "google": ["google", "gmail", "googl"],
            "facebook": ["facebook", "fb", "meta"],
            "instagram": ["instagram", "insta"],
            "netflix": ["netflix", "netflx"],
            "bank": ["bank", "banking", "wellsfargo", "chase", "bofa", "citibank"],
            "ebay": ["ebay"],
            "usps": ["usps", "ups", "fedex", "dhl"],
            "irs": ["irs", "tax"],
        }

        for brand, variants in brand_list.items():
            for variant in variants:
                # Check URL
                if variant in url_lower:
                    # Check if it's the actual brand domain
                    domain = url_structure.get("domain", "").lower()
                    if domain != brand:  # Not the real brand
                        detected_brands.append(brand)
                        break

                # Check page title
                elif variant in title and brand not in title:
                    detected_brands.append(brand)
                    break

        return list(set(detected_brands))  # Deduplicate

    async def _execute_search(self, query: str) -> List[Dict[str, Any]]:
        """Execute search using configured backend"""

        # Try Brave Search API first (recommended - good free tier)
        if self.brave_api_key:
            return await self._search_brave(query)

        # Try SerpAPI
        elif self.serpapi_key:
            return await self._search_serpapi(query)

        # Try Google Custom Search
        elif self.google_cse_key and self.google_cse_id:
            return await self._search_google_cse(query)

        # Fallback: DuckDuckGo scraping (least reliable)
        else:
            logger.warning("No search API configured, using fallback method")
            return await self._search_duckduckgo_fallback(query)

    async def _search_brave(self, query: str) -> List[Dict[str, Any]]:
        """Search using Brave Search API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    'https://api.search.brave.com/res/v1/web/search',
                    headers={
                        'X-Subscription-Token': self.brave_api_key,
                        'Accept': 'application/json'
                    },
                    params={
                        'q': query,
                        'count': 10,
                        'text_decorations': False,
                        'safesearch': 'off'
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    for item in data.get('web', {}).get('results', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('description', ''),
                            'url': item.get('url', ''),
                            'source': 'brave'
                        })

                    return results
                else:
                    logger.error(f"Brave Search API error: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Brave Search error: {str(e)}")
            return []

    async def _search_serpapi(self, query: str) -> List[Dict[str, Any]]:
        """Search using SerpAPI"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    'https://serpapi.com/search',
                    params={
                        'q': query,
                        'api_key': self.serpapi_key,
                        'num': 10
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    for item in data.get('organic_results', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'source': 'serpapi'
                        })

                    return results
                else:
                    logger.error(f"SerpAPI error: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"SerpAPI error: {str(e)}")
            return []

    async def _search_google_cse(self, query: str) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    'https://www.googleapis.com/customsearch/v1',
                    params={
                        'key': self.google_cse_key,
                        'cx': self.google_cse_id,
                        'q': query,
                        'num': 10
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []

                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'source': 'google_cse'
                        })

                    return results
                else:
                    logger.error(f"Google CSE error: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Google CSE error: {str(e)}")
            return []

    async def _search_duckduckgo_fallback(self, query: str) -> List[Dict[str, Any]]:
        """
        Fallback search using DuckDuckGo HTML scraping
        Less reliable, use only when no API is configured
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    'https://html.duckduckgo.com/html/',
                    params={'q': query},
                    headers=self.headers,
                    follow_redirects=True
                )

                if response.status_code != 200:
                    return []

                soup = BeautifulSoup(response.text, 'lxml')
                results = []

                # Parse DDG results
                for result_div in soup.find_all('div', class_='result')[:10]:
                    title_elem = result_div.find('a', class_='result__a')
                    snippet_elem = result_div.find('a', class_='result__snippet')

                    if title_elem:
                        results.append({
                            'title': title_elem.get_text(strip=True),
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'url': title_elem.get('href', ''),
                            'source': 'duckduckgo_fallback'
                        })

                return results

        except Exception as e:
            logger.error(f"DuckDuckGo fallback error: {str(e)}")
            return []

    def _parse_search_results(
        self, query: str, search_results: List[Dict[str, Any]], domain: str
    ) -> Dict[str, Any]:
        """Parse search results to extract reputation signals"""

        parsed = {
            'query': query,
            'scam_indicators': [],
            'positive_signals': [],
            'negative_signals': [],
            'neutral_mentions': []
        }

        # Keywords indicating problems
        scam_keywords = [
            'scam', 'fraud', 'fake', 'phishing', 'malware', 'virus',
            'steal', 'stolen', 'hack', 'malicious', 'dangerous', 'warning',
            'avoid', 'beware', 'suspicious', 'reported', 'complaint'
        ]

        # Keywords indicating legitimacy
        positive_keywords = [
            'legitimate', 'trustworthy', 'safe', 'secure', 'reliable',
            'verified', 'authentic', 'official', 'reputable', 'trusted'
        ]

        # Loss/damage keywords
        victim_keywords = [
            'lost money', 'stolen', 'charged', 'unauthorized', 'fraud',
            'did not receive', 'never arrived', 'ripped off', 'scammed'
        ]

        for result in search_results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            text = f"{title} {snippet}"
            result_url = result.get('url', '')

            # Check for scam indicators
            found_scam_terms = [kw for kw in scam_keywords if kw in text]
            if found_scam_terms:
                parsed['scam_indicators'].append({
                    'source': result_url,
                    'title': result.get('title', ''),
                    'snippet': snippet[:200],
                    'keywords': found_scam_terms,
                    'severity': 'high' if any(kw in text for kw in ['scam', 'fraud', 'phishing']) else 'medium'
                })

            # Check for victim reports
            found_victim_terms = [kw for kw in victim_keywords if kw in text]
            if found_victim_terms:
                parsed['negative_signals'].append({
                    'type': 'victim_report',
                    'source': result_url,
                    'snippet': snippet[:200],
                    'indicators': found_victim_terms
                })

            # Check for positive signals
            found_positive = [kw for kw in positive_keywords if kw in text]
            if found_positive:
                parsed['positive_signals'].append({
                    'source': result_url,
                    'keywords': found_positive,
                    'snippet': snippet[:200]
                })

            # Check for review sites
            if any(site in result_url for site in ['trustpilot', 'bbb.org', 'sitejabber', 'reddit']):
                parsed['neutral_mentions'].append({
                    'type': 'review_site',
                    'source': result_url,
                    'title': result.get('title', ''),
                    'snippet': snippet[:200]
                })

        return parsed

    def _merge_findings(self, results: Dict[str, Any], parsed: Dict[str, Any]):
        """Merge parsed results into overall findings"""

        # Add scam indicators
        for indicator in parsed['scam_indicators']:
            # Avoid duplicates
            if not any(i['source'] == indicator['source'] for i in results['scam_indicators']):
                results['scam_indicators'].append(indicator)

        # Add complaints
        for signal in parsed['negative_signals']:
            if not any(c['source'] == signal['source'] for c in results['user_complaints']):
                results['user_complaints'].append(signal)

        # Track reputation findings
        if parsed['scam_indicators'] or parsed['negative_signals']:
            results['reputation_findings'].append({
                'query': parsed['query'],
                'finding_type': 'negative',
                'count': len(parsed['scam_indicators']) + len(parsed['negative_signals'])
            })
        elif parsed['positive_signals']:
            results['reputation_findings'].append({
                'query': parsed['query'],
                'finding_type': 'positive',
                'count': len(parsed['positive_signals'])
            })

    def _calculate_reputation_score(self, results: Dict[str, Any]) -> int:
        """
        Calculate reputation score (0-100, higher is better)
        0-30: Very poor reputation
        31-50: Poor reputation
        51-70: Mixed reputation
        71-85: Good reputation
        86-100: Excellent reputation
        """

        scam_count = len(results['scam_indicators'])
        complaint_count = len(results['user_complaints'])

        # Start with neutral score
        score = 70

        # Penalties for negative findings
        high_severity_scams = sum(1 for s in results['scam_indicators'] if s.get('severity') == 'high')

        # Heavy penalty for scam reports
        score -= (high_severity_scams * 15)
        score -= ((scam_count - high_severity_scams) * 10)

        # Penalty for user complaints
        score -= (complaint_count * 5)

        # Cap between 0 and 100
        score = max(0, min(100, score))

        return score

    def _assess_risk_level(self, results: Dict[str, Any]) -> str:
        """Assess overall risk level based on findings"""

        scam_count = len(results['scam_indicators'])
        complaint_count = len(results['user_complaints'])
        reputation_score = results['reputation_score']

        high_severity_scams = sum(1 for s in results['scam_indicators'] if s.get('severity') == 'high')

        if high_severity_scams >= 3 or scam_count >= 5:
            return "CRITICAL"
        elif high_severity_scams >= 1 or scam_count >= 3 or complaint_count >= 5:
            return "HIGH"
        elif scam_count >= 1 or complaint_count >= 2 or reputation_score < 50:
            return "MEDIUM"
        elif reputation_score >= 70:
            return "LOW"
        else:
            return "UNKNOWN"

    def _get_backend_name(self) -> str:
        """Get the name of the configured search backend"""
        if self.brave_api_key:
            return "Brave Search API"
        elif self.serpapi_key:
            return "SerpAPI"
        elif self.google_cse_key and self.google_cse_id:
            return "Google Custom Search"
        else:
            return "DuckDuckGo (Fallback)"
