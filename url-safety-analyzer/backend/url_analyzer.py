"""
URL Analysis Module
Performs comprehensive technical analysis of URLs including:
- WHOIS lookup
- DNS resolution
- SSL/TLS certificate analysis
- Content fetching and analysis
- Suspicious pattern detection
"""

import asyncio
import socket
import ssl
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime
import logging

import httpx
from bs4 import BeautifulSoup
import tldextract
import validators

from web_reputation_search import WebReputationSearcher

logger = logging.getLogger(__name__)


class URLAnalyzer:
    """Comprehensive URL analysis tool"""

    def __init__(self):
        self.timeout = httpx.Timeout(10.0, connect=5.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.reputation_searcher = WebReputationSearcher()

    async def analyze(self, url: str) -> Dict[str, Any]:
        """
        Perform comprehensive URL analysis
        """
        logger.info(f"Starting analysis for URL: {url}")

        # Validate URL
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")

        # Parse URL components
        parsed = urlparse(url)
        extracted = tldextract.extract(url)

        analysis = {
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "url_structure": self._analyze_url_structure(url, parsed, extracted),
            "dns_info": await self._get_dns_info(parsed.netloc or parsed.path),
            "ssl_info": await self._get_ssl_info(parsed.netloc or parsed.path),
            "http_response": await self._analyze_http_response(url),
            "content_analysis": {},
            "web_reputation": {},
            "risk_indicators": []
        }

        # Analyze content if available
        if analysis["http_response"].get("content"):
            analysis["content_analysis"] = self._analyze_content(
                analysis["http_response"]["content"],
                url
            )

        # Search web for reputation information
        if self.reputation_searcher.is_configured():
            try:
                logger.info("Performing context-aware web reputation search...")

                # Build context for intelligent query generation
                search_context = {
                    "url_structure": analysis["url_structure"],
                    "content_analysis": analysis["content_analysis"],
                    "ssl_info": analysis["ssl_info"],
                }

                analysis["web_reputation"] = await self.reputation_searcher.search_reputation(
                    url, extracted.fqdn, context=search_context
                )
            except Exception as e:
                logger.error(f"Web reputation search error: {str(e)}")
                analysis["web_reputation"] = {
                    "search_performed": False,
                    "error": str(e)
                }
        else:
            logger.info("Web reputation search not configured (no search API key)")
            analysis["web_reputation"] = {
                "search_performed": False,
                "error": "No search API configured. Set BRAVE_SEARCH_API_KEY, SERPAPI_KEY, or GOOGLE_CSE_API_KEY"
            }

        # Detect risk indicators
        analysis["risk_indicators"] = self._detect_risk_indicators(analysis)

        return analysis

    def _analyze_url_structure(
        self, url: str, parsed: Any, extracted: Any
    ) -> Dict[str, Any]:
        """Analyze URL structure for suspicious patterns"""
        return {
            "scheme": parsed.scheme,
            "domain": extracted.domain,
            "subdomain": extracted.subdomain,
            "suffix": extracted.suffix,
            "fqdn": extracted.fqdn,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "has_ip": self._is_ip_address(parsed.netloc),
            "url_length": len(url),
            "domain_length": len(extracted.fqdn),
            "suspicious_patterns": self._check_suspicious_url_patterns(url)
        }

    def _is_ip_address(self, hostname: str) -> bool:
        """Check if hostname is an IP address"""
        if not hostname:
            return False
        # Remove port if present
        host = hostname.split(':')[0]
        try:
            socket.inet_aton(host)
            return True
        except socket.error:
            return False

    def _check_suspicious_url_patterns(self, url: str) -> List[str]:
        """Check for suspicious patterns in URL"""
        patterns = []

        # Multiple subdomains
        if url.count('.') > 4:
            patterns.append("excessive_subdomains")

        # Suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top']
        if any(url.endswith(tld) for tld in suspicious_tlds):
            patterns.append("suspicious_tld")

        # URL shorteners
        shorteners = ['bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly']
        if any(short in url for short in shorteners):
            patterns.append("url_shortener")

        # Suspicious keywords
        suspicious_keywords = [
            'login', 'signin', 'account', 'verify', 'secure', 'update',
            'confirm', 'banking', 'paypal', 'ebay', 'amazon'
        ]
        url_lower = url.lower()
        found_keywords = [kw for kw in suspicious_keywords if kw in url_lower]
        if found_keywords:
            patterns.append(f"suspicious_keywords:{','.join(found_keywords)}")

        # @ symbol (potential phishing)
        if '@' in url:
            patterns.append("at_symbol")

        # Excessive hyphens
        domain_part = urlparse(url).netloc
        if domain_part.count('-') > 3:
            patterns.append("excessive_hyphens")

        return patterns

    async def _get_dns_info(self, hostname: str) -> Dict[str, Any]:
        """Get DNS information for hostname"""
        try:
            # Remove port if present
            host = hostname.split(':')[0]

            # Get IP addresses
            try:
                ip_addresses = socket.getaddrinfo(host, None)
                ips = list(set([ip[4][0] for ip in ip_addresses]))
            except socket.gaierror:
                ips = []

            return {
                "hostname": host,
                "ip_addresses": ips,
                "resolved": len(ips) > 0,
                "error": None
            }
        except Exception as e:
            logger.error(f"DNS lookup error: {str(e)}")
            return {
                "hostname": hostname,
                "ip_addresses": [],
                "resolved": False,
                "error": str(e)
            }

    async def _get_ssl_info(self, hostname: str) -> Dict[str, Any]:
        """Get SSL/TLS certificate information"""
        try:
            host = hostname.split(':')[0]

            context = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()

                    return {
                        "has_ssl": True,
                        "version": ssock.version(),
                        "issuer": dict(x[0] for x in cert.get('issuer', [])),
                        "subject": dict(x[0] for x in cert.get('subject', [])),
                        "valid_from": cert.get('notBefore'),
                        "valid_until": cert.get('notAfter'),
                        "san": cert.get('subjectAltName', []),
                        "error": None
                    }
        except Exception as e:
            logger.warning(f"SSL check error for {hostname}: {str(e)}")
            return {
                "has_ssl": False,
                "error": str(e)
            }

    async def _analyze_http_response(self, url: str) -> Dict[str, Any]:
        """Fetch URL and analyze HTTP response"""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False  # Allow invalid certs for analysis
            ) as client:
                response = await client.get(url, headers=self.headers)

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "final_url": str(response.url),
                    "redirect_chain": [str(r.url) for r in response.history],
                    "content_type": response.headers.get('content-type', ''),
                    "content_length": len(response.content),
                    "content": response.text[:50000] if response.status_code == 200 else None,  # Limit content
                    "error": None
                }
        except Exception as e:
            logger.error(f"HTTP request error: {str(e)}")
            return {
                "status_code": None,
                "error": str(e),
                "final_url": url,
                "redirect_chain": []
            }

    def _analyze_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Analyze HTML content for suspicious elements"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Extract key elements
            title = soup.find('title')
            meta_tags = soup.find_all('meta')
            forms = soup.find_all('form')
            scripts = soup.find_all('script')
            iframes = soup.find_all('iframe')
            links = soup.find_all('a')

            # Analyze forms (potential credential harvesting)
            form_analysis = []
            for form in forms:
                form_analysis.append({
                    'action': form.get('action', ''),
                    'method': form.get('method', 'get'),
                    'inputs': [inp.get('type', 'text') for inp in form.find_all('input')]
                })

            # Check for suspicious patterns
            suspicious_content = []

            # Hidden iframes
            if iframes:
                suspicious_content.append(f"contains_{len(iframes)}_iframes")

            # External scripts
            external_scripts = [
                s.get('src') for s in scripts
                if s.get('src') and not s.get('src').startswith(url)
            ]
            if external_scripts:
                suspicious_content.append(f"{len(external_scripts)}_external_scripts")

            # Forms submitting to external domains
            for form in form_analysis:
                action = form.get('action', '')
                if action and action.startswith('http') and url not in action:
                    suspicious_content.append("external_form_submission")
                    break

            return {
                "title": title.text.strip() if title else None,
                "meta_description": next(
                    (m.get('content') for m in meta_tags if m.get('name') == 'description'),
                    None
                ),
                "forms_count": len(forms),
                "forms": form_analysis,
                "scripts_count": len(scripts),
                "external_scripts_count": len(external_scripts),
                "iframes_count": len(iframes),
                "links_count": len(links),
                "suspicious_content": suspicious_content
            }
        except Exception as e:
            logger.error(f"Content analysis error: {str(e)}")
            return {"error": str(e)}

    def _detect_risk_indicators(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect risk indicators from analysis"""
        indicators = []

        # URL structure risks
        url_struct = analysis.get("url_structure", {})
        if url_struct.get("has_ip"):
            indicators.append({
                "type": "high",
                "category": "url_structure",
                "indicator": "IP address used instead of domain name",
                "risk": "Phishing sites often use IP addresses to avoid domain registration"
            })

        if url_struct.get("url_length", 0) > 100:
            indicators.append({
                "type": "medium",
                "category": "url_structure",
                "indicator": "Unusually long URL",
                "risk": "May indicate obfuscation or parameter tampering"
            })

        suspicious_patterns = url_struct.get("suspicious_patterns", [])
        for pattern in suspicious_patterns:
            if "suspicious_tld" in pattern:
                indicators.append({
                    "type": "high",
                    "category": "url_structure",
                    "indicator": "Suspicious top-level domain",
                    "risk": "TLD commonly associated with malicious sites"
                })

        # SSL risks
        ssl_info = analysis.get("ssl_info", {})
        if not ssl_info.get("has_ssl"):
            indicators.append({
                "type": "medium",
                "category": "security",
                "indicator": "No valid SSL/TLS certificate",
                "risk": "Lack of encryption, potential for man-in-the-middle attacks"
            })

        # HTTP response risks
        http_resp = analysis.get("http_response", {})
        if len(http_resp.get("redirect_chain", [])) > 3:
            indicators.append({
                "type": "medium",
                "category": "behavior",
                "indicator": "Multiple redirects detected",
                "risk": "May indicate cloaking or redirect-based attacks"
            })

        # Content risks
        content = analysis.get("content_analysis", {})
        if content.get("iframes_count", 0) > 0:
            indicators.append({
                "type": "medium",
                "category": "content",
                "indicator": "Contains hidden iframes",
                "risk": "May load malicious content from external sources"
            })

        if "external_form_submission" in content.get("suspicious_content", []):
            indicators.append({
                "type": "high",
                "category": "content",
                "indicator": "Form submits to external domain",
                "risk": "Potential credential harvesting or phishing"
            })

        # Web reputation risks
        web_rep = analysis.get("web_reputation", {})
        if web_rep.get("search_performed"):
            scam_count = len(web_rep.get("scam_indicators", []))
            complaint_count = len(web_rep.get("user_complaints", []))
            reputation_score = web_rep.get("reputation_score", 70)
            risk_level = web_rep.get("risk_level", "UNKNOWN")

            # Add indicators based on web reputation findings
            if scam_count > 0:
                high_severity = sum(1 for s in web_rep.get("scam_indicators", [])
                                  if s.get("severity") == "high")

                if high_severity >= 3:
                    indicators.append({
                        "type": "critical",
                        "category": "web_reputation",
                        "indicator": f"Multiple scam reports found online ({high_severity} high-severity)",
                        "risk": "Website has been widely reported as a scam across multiple sources"
                    })
                elif high_severity >= 1:
                    indicators.append({
                        "type": "high",
                        "category": "web_reputation",
                        "indicator": f"Scam reports found online ({high_severity} high-severity, {scam_count} total)",
                        "risk": "Website has been reported as potentially fraudulent"
                    })
                elif scam_count >= 2:
                    indicators.append({
                        "type": "medium",
                        "category": "web_reputation",
                        "indicator": f"{scam_count} scam-related mentions found",
                        "risk": "Some negative reputation signals detected"
                    })

            if complaint_count >= 3:
                indicators.append({
                    "type": "high",
                    "category": "web_reputation",
                    "indicator": f"{complaint_count} user complaints found",
                    "risk": "Multiple users have reported negative experiences"
                })
            elif complaint_count >= 1:
                indicators.append({
                    "type": "medium",
                    "category": "web_reputation",
                    "indicator": f"{complaint_count} user complaints found",
                    "risk": "Some users have reported issues with this website"
                })

            if reputation_score < 30:
                indicators.append({
                    "type": "high",
                    "category": "web_reputation",
                    "indicator": f"Very poor online reputation (score: {reputation_score}/100)",
                    "risk": "Website has overwhelmingly negative reputation online"
                })
            elif reputation_score < 50:
                indicators.append({
                    "type": "medium",
                    "category": "web_reputation",
                    "indicator": f"Poor online reputation (score: {reputation_score}/100)",
                    "risk": "Website has significant negative reputation signals"
                })

        return indicators
