"""
Web Reputation Search Module
AI-driven search for reputation information, scam complaints, and reviews about URLs
Uses GPT-4o for intelligent query planning and GPT-4o-mini for result analysis
"""

import os
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import re
import json

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class WebReputationSearcher:
    """
    AI-powered web reputation searcher
    Uses GPT-4o for query planning and GPT-4o-mini for result analysis
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

        # Initialize OpenAI client for AI-driven analysis
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not configured - AI query planning disabled")

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
        AI-driven search for reputation information about a URL/domain
        Uses GPT-4o to plan queries and GPT-4o-mini to analyze results

        Args:
            url: Full URL to analyze
            domain: Extracted domain name
            context: Analysis context including url_structure, content_analysis, ssl_info

        Returns aggregated findings from AI analysis of search results
        """
        logger.info(f"Starting AI-driven reputation search for: {domain}")

        results = {
            "search_performed": True,
            "queries_used": [],
            "scam_indicators": [],
            "reputation_findings": [],
            "user_complaints": [],
            "ai_analysis": {},
            "search_backend": self._get_backend_name(),
            "total_results_analyzed": 0,
            "query_strategy": "ai_driven" if self.openai_client else "fallback"
        }

        # Use AI to generate search queries based on context
        if self.openai_client and context:
            queries = await self._ai_generate_queries(url, domain, context)
            logger.info(f"GPT-4o generated {len(queries)} intelligent queries")
        else:
            # Fallback to basic queries if no AI
            queries = await self._fallback_queries(domain)
            logger.info(f"Using {len(queries)} fallback queries (no AI configured)")

        results["queries_used"] = queries

        # Execute searches and collect all results
        all_search_results = []
        for query in queries:
            try:
                search_results = await self._execute_search(query)
                if search_results:
                    all_search_results.append({
                        "query": query,
                        "results": search_results
                    })
                    results["total_results_analyzed"] += len(search_results)
            except Exception as e:
                logger.error(f"Search error for query '{query}': {str(e)}")
                continue

        # Enrich search results by fetching actual page content
        enriched_content = []
        if self.openai_client and all_search_results:
            logger.info("Enriching search results by fetching page content from top results...")
            enriched_content = await self._enrich_search_results_with_content(
                url,
                all_search_results,
                max_pages=5  # Fetch up to 5 pages for deeper analysis
            )
            results["pages_fetched"] = len(enriched_content)
            logger.info(f"Fetched and analyzed {len(enriched_content)} pages for deeper insight")

        # Use AI to analyze all search results (snippets + enriched content)
        if self.openai_client and all_search_results:
            logger.info(f"Using GPT-4o-mini to analyze {len(all_search_results)} query results + {len(enriched_content)} full pages")
            ai_analysis = await self._ai_analyze_search_results(
                url, domain, all_search_results, context, enriched_content
            )
            results["ai_analysis"] = ai_analysis
            results["scam_indicators"] = ai_analysis.get("scam_indicators", [])
            results["user_complaints"] = ai_analysis.get("user_complaints", [])
            results["reputation_score"] = ai_analysis.get("reputation_score", 70)
            results["risk_level"] = ai_analysis.get("risk_level", "UNKNOWN")
            results["enriched_content_used"] = len(enriched_content) > 0
        else:
            # Fallback to basic analysis
            logger.info("Using fallback analysis (no AI configured)")
            results.update(self._fallback_analysis(all_search_results))

        return results

    async def execute_targeted_searches(
        self,
        url: str,
        search_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Execute specific targeted web searches and analyze results
        Used for follow-up investigations when AI needs more specific information

        Args:
            url: The URL being investigated
            search_queries: List of specific search queries to execute

        Returns: Analyzed search results with findings
        """
        logger.info(f"Executing {len(search_queries)} targeted searches for follow-up investigation")

        results = {
            "queries_executed": search_queries,
            "findings": [],
            "total_results": 0,
            "backend": self._get_backend_name()
        }

        # Execute each targeted search query
        all_search_results = []
        for query in search_queries[:5]:  # Limit to 5 queries
            try:
                search_results = await self._execute_search(query)
                if search_results:
                    all_search_results.append({
                        "query": query,
                        "results": search_results
                    })
                    results["total_results"] += len(search_results)
                    logger.info(f"Targeted search '{query}' returned {len(search_results)} results")
            except Exception as e:
                logger.error(f"Error executing targeted search '{query}': {str(e)}")
                continue

        # Enrich targeted search results with page content
        enriched_content = []
        if self.openai_client and all_search_results:
            logger.info("Enriching targeted search results by fetching page content...")
            enriched_content = await self._enrich_search_results_with_content(
                url,
                all_search_results,
                max_pages=3  # Fetch up to 3 pages for follow-up searches
            )
            results["pages_fetched"] = len(enriched_content)
            logger.info(f"Fetched and analyzed {len(enriched_content)} pages for follow-up investigation")

        # Use GPT-4o-mini to analyze the targeted search results + enriched content
        if self.openai_client and all_search_results:
            try:
                # Prepare enriched content summary
                enriched_summary = ""
                if enriched_content:
                    enriched_summary = "\n\nENRICHED CONTENT FROM FETCHED PAGES:\n"
                    for item in enriched_content:
                        extracted = item.get("extracted_content", {})
                        enriched_summary += f"\n- {item.get('url')}\n  Summary: {extracted.get('summary', 'N/A')}\n  Info: {extracted.get('extracted_info', 'N/A')[:300]}\n"

                analysis_prompt = f"""Analyze these targeted web search results for URL: {url}

These searches were conducted as follow-up investigation to address specific evidence gaps.

Search queries executed: {json.dumps(search_queries)}

Search Results ({results['total_results']} snippet results):
{json.dumps(all_search_results[:15], indent=2)}
{enriched_summary}

Analyze what new evidence these results provide. The enriched content (actual page fetches) is MORE RELIABLE than snippets.

Return ONLY a JSON object:
{{
  "new_findings": ["List of specific new findings from these searches"],
  "evidence_type": "reputation|scam_reports|user_reviews|technical_info",
  "severity": "low|medium|high|critical",
  "summary": "Brief summary of what was discovered",
  "supports_concern": true/false,
  "key_quotes": ["Direct quotes from enriched content if available"]
}}"""

                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are analyzing targeted web search results for trust and safety investigation."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=800,
                    response_format={"type": "json_object"}
                )

                analysis = json.loads(response.choices[0].message.content)
                results["ai_analysis"] = analysis
                results["findings"] = analysis.get("new_findings", [])
                results["enriched_content_used"] = len(enriched_content) > 0

            except Exception as e:
                logger.error(f"Error analyzing targeted search results: {str(e)}")
                results["findings"] = [f"Found {len(all_search_results)} results but analysis failed"]

        return results

    async def _ai_generate_queries(
        self,
        url: str,
        domain: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Use GPT-4o to intelligently generate search queries based on technical analysis
        """
        try:
            prompt = f"""You are a trust & safety expert analyzing a URL for potential threats.

URL: {url}
Domain: {domain}

TECHNICAL ANALYSIS CONTEXT:
{json.dumps(context, indent=2)}

Based on this technical analysis, generate 8-15 highly targeted web search queries to investigate this URL's reputation.

Consider:
1. What specific threats are indicated by the technical data?
2. Are there brand impersonation indicators?
3. What type of scam/fraud patterns are present?
4. What would real victims search for or complain about?
5. Which reputation sites would have relevant information?

Generate queries that will find:
- Scam reports and warnings
- User complaints and victim testimonials
- Brand impersonation mentions
- Security warnings
- Review site discussions (Reddit, Trustpilot, BBB)

Return ONLY a JSON array of search query strings. Each query should be specific and targeted.

Example response:
["domain.com paypal phishing", "domain.com credential theft", "site:reddit.com domain.com scam"]

Your response (JSON array only):"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for intelligent planning
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust & safety expert who generates targeted web search queries. Respond with JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content.strip()
            queries_data = json.loads(response_text)

            # Handle different possible JSON structures
            if isinstance(queries_data, list):
                queries = queries_data
            elif isinstance(queries_data, dict):
                queries = queries_data.get("queries", queries_data.get("search_queries", []))
            else:
                queries = []

            logger.info(f"GPT-4o generated {len(queries)} queries")
            return queries[:15]  # Limit to 15

        except Exception as e:
            logger.error(f"AI query generation error: {str(e)}")
            return await self._fallback_queries(domain)

    async def _ai_analyze_search_results(
        self,
        url: str,
        domain: str,
        search_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        enriched_content: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Use GPT-4o-mini to analyze search results and extract threat intelligence
        Now includes enriched content from actual page fetches
        """
        try:
            # Prepare search results summary for AI
            results_summary = []
            for item in search_results:
                query = item["query"]
                for result in item["results"][:5]:  # Top 5 results per query
                    results_summary.append({
                        "query": query,
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", "")[:300],
                        "url": result.get("url", "")
                    })

            # Add enriched content section if available
            enriched_section = ""
            if enriched_content and len(enriched_content) > 0:
                enriched_section = f"""

ENRICHED CONTENT FROM ACTUAL PAGES ({len(enriched_content)} pages fetched and analyzed):
"""
                for idx, item in enumerate(enriched_content, 1):
                    extracted = item.get("extracted_content", {})
                    enriched_section += f"""
Page {idx}: {item.get('url', 'Unknown')}
- Relevance: {extracted.get('relevance_type', 'unknown')}
- Severity: {extracted.get('severity', 'unknown')}
- Summary: {extracted.get('summary', 'No summary')}
- Key Quotes: {json.dumps(extracted.get('key_quotes', []))}
- Extracted Info: {extracted.get('extracted_info', 'None')[:500]}
"""

            prompt = f"""You are a trust & safety analyst examining web search results about a URL.

TARGET URL: {url}
DOMAIN: {domain}

TECHNICAL CONTEXT:
{json.dumps(context, indent=2) if context else "No technical context"}

SEARCH RESULTS ({len(results_summary)} snippet results across multiple queries):
{json.dumps(results_summary, indent=2)}
{enriched_section}

Analyze these search results and provide a comprehensive assessment.

IMPORTANT: The "ENRICHED CONTENT FROM ACTUAL PAGES" section contains full page content that was fetched and analyzed
for relevance. This is MORE RELIABLE than snippets because it includes the complete context. Give this enriched
content HIGHER WEIGHT in your analysis than basic search snippets.

Provide your assessment with:

1. SCAM INDICATORS: List any evidence of scams, fraud, phishing with:
   - Description of the scam indicator
   - Source/citation (prefer enriched content sources)
   - Severity (high/medium/low)
   - Specific quotes from enriched content when available

2. USER COMPLAINTS: List victim reports or complaints with:
   - Type of complaint
   - What happened
   - Source (note if from enriched content vs snippet)

3. REPUTATION SCORE: Calculate 0-100 (100=excellent, 0=terrible) based on:
   - Number and severity of scam reports
   - User complaint volume
   - Positive vs negative mentions
   - Weight enriched content findings more heavily

4. RISK LEVEL: Classify as LOW/MEDIUM/HIGH/CRITICAL

5. KEY FINDINGS: 2-3 most important discoveries (prioritize enriched content findings)

6. THREAT ASSESSMENT: What type of threat is this? (phishing/malware/scam/legitimate/unknown)

Return your analysis as JSON with this structure:
{{
  "scam_indicators": [
    {{
      "description": "...",
      "source": "...",
      "severity": "high|medium|low",
      "evidence": "specific quote or detail"
    }}
  ],
  "user_complaints": [
    {{
      "type": "...",
      "description": "...",
      "source": "..."
    }}
  ],
  "reputation_score": 0-100,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "threat_type": "phishing|malware|scam|ecommerce_fraud|legitimate|unknown",
  "confidence": 0-100,
  "summary": "2-3 sentence overall assessment"
}}

Your JSON analysis:"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using 4o-mini for analysis (cost-effective)
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust & safety analyst. Analyze search results and respond with JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"GPT-4o-mini analysis complete: {analysis.get('threat_type')} / {analysis.get('risk_level')}")
            return analysis

        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return {
                "scam_indicators": [],
                "user_complaints": [],
                "reputation_score": 50,
                "risk_level": "UNKNOWN",
                "key_findings": ["AI analysis unavailable"],
                "threat_type": "unknown",
                "confidence": 0,
                "summary": f"AI analysis failed: {str(e)}"
            }

    async def _fetch_page_content(
        self,
        url: str,
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Fetch and extract text content from a web page
        Returns extracted text and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "url": url
                    }

                # Parse HTML and extract text
                soup = BeautifulSoup(response.content, 'lxml')

                # Remove script and style elements
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()

                # Extract text from body
                body = soup.find('body')
                if body:
                    text = body.get_text(separator=' ', strip=True)
                else:
                    text = soup.get_text(separator=' ', strip=True)

                # Clean up whitespace
                text = ' '.join(text.split())

                # Truncate if too long
                if len(text) > max_length:
                    text = text[:max_length] + "..."

                # Extract title
                title = soup.find('title')
                title_text = title.get_text(strip=True) if title else "No title"

                return {
                    "success": True,
                    "url": url,
                    "title": title_text,
                    "text": text,
                    "length": len(text)
                }

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching page content: {url}")
            return {"success": False, "error": "Timeout", "url": url}
        except Exception as e:
            logger.warning(f"Error fetching page content from {url}: {str(e)}")
            return {"success": False, "error": str(e), "url": url}

    async def _extract_relevant_content_with_ai(
        self,
        target_url: str,
        page_content: Dict[str, Any],
        search_context: str
    ) -> Dict[str, Any]:
        """
        Use GPT-4o-mini to extract relevant information from page content
        """
        if not page_content.get("success") or not self.openai_client:
            return {"extracted": False, "reason": "Page fetch failed or no AI"}

        try:
            prompt = f"""You are analyzing a web page to find information about: {target_url}

This page was found in a search about the target URL's reputation and safety.

PAGE INFORMATION:
Title: {page_content.get('title', 'Unknown')}
URL: {page_content.get('url', 'Unknown')}
Search Context: {search_context}

PAGE CONTENT (first {page_content.get('length', 0)} characters):
{page_content.get('text', '')[:5000]}

Extract ONLY the information relevant to {target_url}'s safety, reputation, or trustworthiness.

Return ONLY a JSON object:
{{
  "relevant": true/false,
  "extracted_info": "The specific relevant information found (if any)",
  "relevance_type": "scam_report|user_complaint|review|warning|positive_mention|neutral|not_relevant",
  "severity": "high|medium|low|none",
  "key_quotes": ["exact quote 1", "exact quote 2"],
  "summary": "1-2 sentence summary of what this page says about the target URL"
}}

If the page doesn't contain relevant information about {target_url}, set relevant=false."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are extracting relevant information from web pages for trust & safety analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            extraction = json.loads(response.choices[0].message.content)
            extraction["source_url"] = page_content.get("url")
            extraction["source_title"] = page_content.get("title")
            return extraction

        except Exception as e:
            logger.error(f"AI content extraction error: {str(e)}")
            return {"extracted": False, "error": str(e)}

    async def _enrich_search_results_with_content(
        self,
        url: str,
        search_results: List[Dict[str, Any]],
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch actual page content from top search results and extract relevant info

        Args:
            url: Target URL being investigated
            search_results: List of search result items
            max_pages: Maximum number of pages to fetch (default 5)

        Returns:
            List of enriched results with extracted content
        """
        enriched_results = []
        pages_fetched = 0

        logger.info(f"Enriching search results by fetching page content (max {max_pages} pages)")

        for item in search_results:
            query = item.get("query", "")

            for result in item.get("results", [])[:3]:  # Top 3 results per query
                if pages_fetched >= max_pages:
                    break

                result_url = result.get("url", "")
                if not result_url:
                    continue

                # Skip fetching the target URL itself or unreliable sources
                if url.lower() in result_url.lower():
                    continue

                logger.info(f"Fetching content from: {result_url}")

                # Fetch page content
                page_content = await self._fetch_page_content(result_url)

                if page_content.get("success"):
                    # Extract relevant information using AI
                    extracted = await self._extract_relevant_content_with_ai(
                        url,
                        page_content,
                        f"Search query: {query}"
                    )

                    if extracted.get("relevant"):
                        enriched_results.append({
                            "query": query,
                            "original_snippet": result.get("snippet", ""),
                            "original_title": result.get("title", ""),
                            "url": result_url,
                            "extracted_content": extracted,
                            "fetched": True
                        })
                        pages_fetched += 1
                        logger.info(f"✓ Relevant content extracted from {result_url}")
                    else:
                        logger.info(f"✗ No relevant content found in {result_url}")

                if pages_fetched >= max_pages:
                    break

        logger.info(f"Content enrichment complete: {pages_fetched} pages fetched and analyzed")
        return enriched_results

    async def _fallback_queries(self, domain: str) -> List[str]:
        """Basic fallback queries when AI is not available"""
        return [
            f'"{domain}" scam',
            f'"{domain}" fraud',
            f'"{domain}" phishing',
            f'"{domain}" complaint',
            f'"{domain}" review',
            f'site:reddit.com "{domain}"',
        ][:6]

    def _fallback_analysis(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic fallback analysis when AI is not available"""
        scam_keywords = ['scam', 'fraud', 'phishing', 'fake', 'steal', 'stolen']
        scam_count = 0

        for item in search_results:
            for result in item.get("results", []):
                text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
                if any(kw in text for kw in scam_keywords):
                    scam_count += 1

        return {
            "reputation_score": max(0, 70 - (scam_count * 10)),
            "risk_level": "HIGH" if scam_count >= 3 else "MEDIUM" if scam_count >= 1 else "LOW",
            "scam_indicators": [],
            "user_complaints": []
        }

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
