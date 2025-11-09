"""
Content Security Analyzer Module
Detects malicious JavaScript, suspicious links, and compromised website indicators
Integrates with DomainTools, VirusTotal, and URLhaus for comprehensive malware detection
"""

import os
import re
import logging
import hashlib
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urlparse, urljoin
import base64

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentSecurityAnalyzer:
    """
    Comprehensive content security analysis for detecting:
    - Malicious JavaScript patterns
    - Obfuscated code
    - Known exploit kits
    - Suspicious external resources
    - Links to malware domains
    - Compromised website indicators
    """

    def __init__(self):
        # API Keys
        self.domaintools_api_key = os.getenv('DOMAINTOOLS_API_KEY')
        self.domaintools_username = os.getenv('DOMAINTOOLS_USERNAME')
        self.virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY')

        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

        # URLhaus API (public, no key needed)
        self.urlhaus_api = "https://urlhaus-api.abuse.ch/v1/url/"

        # Malicious pattern signatures
        self._load_malware_signatures()

    def _load_malware_signatures(self):
        """Load known malware and exploit kit signatures"""

        # Suspicious JavaScript patterns
        self.js_malware_patterns = [
            # Obfuscation techniques
            r'eval\s*\(\s*(?:atob|unescape|String\.fromCharCode)',
            r'document\.write\s*\(\s*unescape',
            r'Function\s*\(\s*["\'].*return.*eval',

            # Base64 encoded payloads
            r'atob\s*\(["\'][A-Za-z0-9+/=]{50,}["\']',
            r'fromCharCode\s*\(\s*\d+(?:\s*,\s*\d+){10,}',

            # Suspicious eval chains
            r'eval\s*\(.*eval\s*\(',  # Nested evals
            r'setTimeout\s*\(\s*["\'].*eval',

            # Cryptominers
            r'coinhive|cryptonight|monero.*miner',
            r'new\s+Worker\s*\(\s*["\'].*crypto',

            # Keyloggers
            r'onkeypress|onkeydown|onkeyup.*\.log|\.send',
            r'document\.addEventListener\s*\(["\']key.*XMLHttpRequest',

            # Browser exploits
            r'ActiveXObject.*Shell\.Application',
            r'eval.*unescape.*%u[0-9a-fA-F]{4}',  # Heap spray pattern

            # Suspicious redirects
            r'location\.(?:href|replace)\s*=.*fromCharCode',
            r'window\.location.*atob',

            # Data exfiltration
            r'new\s+Image\(\).*\.src.*document\.cookie',
            r'XMLHttpRequest.*\.send.*(?:cookie|password|card)',
        ]

        # Exploit kit signatures
        self.exploit_kit_patterns = {
            'rig': r'(?:flashplayer|java).*update.*\.php\?',
            'angler': r'(?:\/[a-z]{8}\/[a-z]{8}\.swf)',
            'magnitude': r'(?:\.php\?[a-z]{1,3}=[0-9]{8,10})',
            'neutrino': r'(?:\/gate\.php|\/main\.php\?[a-z]=)',
            'blackhole': r'(?:\/tds\/|\/click\.php\?cnv=)',
        }

        # Suspicious external resource patterns
        self.suspicious_resource_patterns = [
            r'https?://(?:\d{1,3}\.){3}\d{1,3}/',  # IP-based URLs
            r'\.(?:tk|ml|ga|cf|gq)/',  # Free TLDs often used for malware
            r'/(?:payload|exploit|shell|backdoor|webshell)\.(?:js|php)',
            r'\.onion\.(?:to|cab|link)/',  # Tor proxies
        ]

        # Known malicious script patterns
        self.malicious_script_signatures = [
            'c99shell', 'r57shell', 'wso', 'b374k',  # Webshells
            'filesman', 'cloudflare-email-decode',  # Suspicious scripts
        ]

    async def analyze_content_security(
        self,
        html_content: str,
        url: str,
        page_domain: str
    ) -> Dict[str, Any]:
        """
        Comprehensive content security analysis

        Args:
            html_content: Raw HTML content
            url: Original URL
            page_domain: Domain of the page

        Returns:
            Dict with malware indicators, suspicious patterns, and threat intelligence
        """

        logger.info(f"Analyzing content security for: {url}")

        results = {
            "analyzed": True,
            "malicious_javascript": [],
            "suspicious_scripts": [],
            "suspicious_links": [],
            "exploit_kits": [],
            "obfuscated_code": [],
            "external_resources": {
                "total": 0,
                "suspicious": 0,
                "checked_domains": [],
                "malware_domains": []
            },
            "threat_intelligence": {
                "domaintools": {},
                "virustotal": {},
                "urlhaus": {}
            },
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "summary": ""
        }

        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # 1. Analyze JavaScript for malware patterns
            results["malicious_javascript"] = await self._analyze_javascript(soup, url)

            # 2. Detect obfuscated code
            results["obfuscated_code"] = self._detect_obfuscation(soup)

            # 3. Check for exploit kits
            results["exploit_kits"] = self._detect_exploit_kits(html_content, soup)

            # 4. Extract and analyze external resources
            external_resources = self._extract_external_resources(soup, url)
            results["external_resources"]["total"] = len(external_resources)

            # 5. Analyze suspicious scripts
            results["suspicious_scripts"] = self._analyze_suspicious_scripts(soup)

            # 6. Extract and check links
            links = self._extract_links(soup, url)
            results["suspicious_links"] = self._analyze_links(links, page_domain)

            # 7. Get threat intelligence for external domains
            suspicious_domains = set()

            # Collect suspicious domains from various sources
            for resource in external_resources:
                if self._is_suspicious_resource(resource):
                    domain = urlparse(resource).netloc
                    if domain and domain != page_domain:
                        suspicious_domains.add(domain)

            for link_info in results["suspicious_links"]:
                if link_info.get("domain"):
                    suspicious_domains.add(link_info["domain"])

            results["external_resources"]["suspicious"] = len(suspicious_domains)
            results["external_resources"]["checked_domains"] = list(suspicious_domains)[:10]  # Limit

            # 8. Query threat intelligence APIs (async for performance)
            if suspicious_domains:
                await self._gather_threat_intelligence(
                    results,
                    list(suspicious_domains)[:5]  # Check top 5 suspicious domains
                )

            # 9. Calculate risk score
            results["risk_score"] = self._calculate_risk_score(results)
            results["risk_level"] = self._determine_risk_level(results["risk_score"])
            results["summary"] = self._generate_summary(results)

        except Exception as e:
            logger.error(f"Content security analysis error: {str(e)}")
            results["error"] = str(e)
            results["analyzed"] = False

        return results

    async def _analyze_javascript(
        self,
        soup: BeautifulSoup,
        url: str
    ) -> List[Dict[str, Any]]:
        """Analyze JavaScript code for malicious patterns"""

        malicious_js = []

        # Find all script tags
        scripts = soup.find_all('script')

        for idx, script in enumerate(scripts):
            script_content = script.string or ''
            if not script_content.strip():
                continue

            # Check against malware patterns
            for pattern in self.js_malware_patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                if matches:
                    malicious_js.append({
                        "script_index": idx,
                        "pattern_matched": pattern[:50] + "...",
                        "match_preview": str(matches[0])[:100] if matches else "",
                        "severity": "high",
                        "type": self._classify_js_threat(pattern),
                        "location": "inline" if not script.get('src') else script.get('src')
                    })

        return malicious_js

    def _classify_js_threat(self, pattern: str) -> str:
        """Classify JavaScript threat type based on pattern"""
        pattern_lower = pattern.lower()

        if 'coin' in pattern_lower or 'miner' in pattern_lower:
            return "cryptominer"
        elif 'key' in pattern_lower:
            return "keylogger"
        elif 'eval' in pattern_lower or 'unescape' in pattern_lower:
            return "obfuscated_malware"
        elif 'activex' in pattern_lower or 'shell' in pattern_lower:
            return "browser_exploit"
        elif 'cookie' in pattern_lower or 'password' in pattern_lower:
            return "data_exfiltration"
        else:
            return "suspicious_code"

    def _detect_obfuscation(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Detect obfuscated code patterns"""

        obfuscated = []
        scripts = soup.find_all('script')

        for idx, script in enumerate(scripts):
            script_content = script.string or ''
            if not script_content.strip():
                continue

            # Check for high entropy (sign of obfuscation)
            if len(script_content) > 100:
                entropy = self._calculate_entropy(script_content)
                if entropy > 5.0:  # High entropy threshold
                    obfuscated.append({
                        "script_index": idx,
                        "type": "high_entropy",
                        "entropy_score": round(entropy, 2),
                        "severity": "medium",
                        "description": "Possibly obfuscated code (high entropy)"
                    })

            # Check for Base64 encoding
            base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'
            base64_matches = re.findall(base64_pattern, script_content)
            if len(base64_matches) > 3:
                obfuscated.append({
                    "script_index": idx,
                    "type": "base64_encoding",
                    "count": len(base64_matches),
                    "severity": "medium",
                    "description": f"Contains {len(base64_matches)} Base64 encoded strings"
                })

            # Check for hex encoding
            hex_pattern = r'(?:\\x[0-9a-fA-F]{2}){10,}'
            if re.search(hex_pattern, script_content):
                obfuscated.append({
                    "script_index": idx,
                    "type": "hex_encoding",
                    "severity": "medium",
                    "description": "Contains hex-encoded strings"
                })

        return obfuscated

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text (measure of randomness)"""
        if not text:
            return 0.0

        from collections import Counter
        import math

        # Count character frequencies
        counter = Counter(text)
        length = len(text)

        # Calculate entropy
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def _detect_exploit_kits(
        self,
        html_content: str,
        soup: BeautifulSoup
    ) -> List[Dict[str, Any]]:
        """Detect known exploit kit signatures"""

        exploit_kits = []

        for kit_name, pattern in self.exploit_kit_patterns.items():
            if re.search(pattern, html_content, re.IGNORECASE):
                exploit_kits.append({
                    "kit_name": kit_name.upper(),
                    "pattern_matched": pattern,
                    "severity": "critical",
                    "description": f"Possible {kit_name.upper()} exploit kit signature detected"
                })

        return exploit_kits

    def _extract_external_resources(
        self,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[str]:
        """Extract all external resources (scripts, iframes, images, etc.)"""

        resources = set()

        # Scripts
        for script in soup.find_all('script', src=True):
            resources.add(urljoin(base_url, script['src']))

        # Iframes
        for iframe in soup.find_all('iframe', src=True):
            resources.add(urljoin(base_url, iframe['src']))

        # Images (potential tracking/malware)
        for img in soup.find_all('img', src=True):
            resources.add(urljoin(base_url, img['src']))

        # Links to external stylesheets
        for link in soup.find_all('link', href=True, rel='stylesheet'):
            resources.add(urljoin(base_url, link['href']))

        return list(resources)

    def _is_suspicious_resource(self, resource_url: str) -> bool:
        """Check if resource URL matches suspicious patterns"""

        for pattern in self.suspicious_resource_patterns:
            if re.search(pattern, resource_url, re.IGNORECASE):
                return True

        # Check for suspicious file extensions
        suspicious_extensions = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.vbs', '.jar']
        if any(resource_url.lower().endswith(ext) for ext in suspicious_extensions):
            return True

        return False

    def _analyze_suspicious_scripts(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Analyze scripts for known malicious signatures"""

        suspicious = []

        for idx, script in enumerate(soup.find_all('script')):
            script_content = script.string or ''
            src = script.get('src', '')

            # Check content against known malicious signatures
            for signature in self.malicious_script_signatures:
                if signature.lower() in script_content.lower() or signature.lower() in src.lower():
                    suspicious.append({
                        "script_index": idx,
                        "signature": signature,
                        "severity": "high",
                        "type": "known_malware_signature",
                        "location": src if src else "inline"
                    })

        return suspicious

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from page"""
        links = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith(('#', 'javascript:', 'mailto:')):
                full_url = urljoin(base_url, href)
                links.add(full_url)

        return list(links)

    def _analyze_links(
        self,
        links: List[str],
        page_domain: str
    ) -> List[Dict[str, Any]]:
        """Analyze links for suspicious patterns"""

        suspicious_links = []

        for link in links[:50]:  # Limit to first 50 links
            parsed = urlparse(link)

            # Check for suspicious patterns
            is_suspicious = False
            reason = []

            # IP-based URL
            if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', parsed.netloc):
                is_suspicious = True
                reason.append("IP-based URL")

            # Suspicious TLD
            if parsed.netloc.endswith(('.tk', '.ml', '.ga', '.cf', '.gq', '.xyz')):
                is_suspicious = True
                reason.append("Suspicious TLD")

            # Download links
            if any(ext in link.lower() for ext in ['.exe', '.zip', '.rar', '.scr', '.bat']):
                is_suspicious = True
                reason.append("Download link (potential malware)")

            # Suspicious keywords in URL
            suspicious_keywords = ['payload', 'exploit', 'malware', 'virus', 'hack', 'crack']
            if any(kw in link.lower() for kw in suspicious_keywords):
                is_suspicious = True
                reason.append("Suspicious keywords in URL")

            if is_suspicious:
                suspicious_links.append({
                    "url": link,
                    "domain": parsed.netloc,
                    "reasons": reason,
                    "severity": "high" if "download" in str(reason).lower() else "medium"
                })

        return suspicious_links

    async def _gather_threat_intelligence(
        self,
        results: Dict[str, Any],
        domains: List[str]
    ):
        """Gather threat intelligence from multiple APIs"""

        # DomainTools
        if self.domaintools_api_key and self.domaintools_username:
            for domain in domains[:3]:  # Check top 3 domains
                dt_result = await self._check_domaintools(domain)
                if dt_result:
                    results["threat_intelligence"]["domaintools"][domain] = dt_result
                    if dt_result.get("risk_score", 0) > 70:
                        results["external_resources"]["malware_domains"].append(domain)

        # VirusTotal
        if self.virustotal_api_key:
            for domain in domains[:3]:
                vt_result = await self._check_virustotal(domain)
                if vt_result:
                    results["threat_intelligence"]["virustotal"][domain] = vt_result
                    if vt_result.get("malicious_count", 0) > 0:
                        results["external_resources"]["malware_domains"].append(domain)

        # URLhaus (public API, no key needed)
        for domain in domains[:5]:
            urlhaus_result = await self._check_urlhaus(domain)
            if urlhaus_result and urlhaus_result.get("found"):
                results["threat_intelligence"]["urlhaus"][domain] = urlhaus_result
                results["external_resources"]["malware_domains"].append(domain)

    async def _check_domaintools(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain reputation with DomainTools API"""

        try:
            # DomainTools Risk Score API
            url = f"https://api.domaintools.com/v1/{domain}/risk"

            params = {
                'api_username': self.domaintools_username,
                'api_key': self.domaintools_api_key
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                risk_score = data.get('risk_score', 0)

                return {
                    "checked": True,
                    "risk_score": risk_score,
                    "risk_level": "high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
                    "components": data.get('components', {}),
                    "evidence": data.get('evidence', [])
                }
            else:
                logger.warning(f"DomainTools API error for {domain}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"DomainTools check error for {domain}: {str(e)}")
            return None

    async def _check_virustotal(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain/URL with VirusTotal API"""

        try:
            # VirusTotal API v3
            url = f"https://www.virustotal.com/api/v3/domains/{domain}"

            headers = {
                'x-apikey': self.virustotal_api_key
            }

            response = await self.client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                stats = attributes.get('last_analysis_stats', {})

                return {
                    "checked": True,
                    "malicious_count": stats.get('malicious', 0),
                    "suspicious_count": stats.get('suspicious', 0),
                    "harmless_count": stats.get('harmless', 0),
                    "undetected_count": stats.get('undetected', 0),
                    "reputation": attributes.get('reputation', 0),
                    "categories": attributes.get('categories', {})
                }
            else:
                logger.warning(f"VirusTotal API error for {domain}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"VirusTotal check error for {domain}: {str(e)}")
            return None

    async def _check_urlhaus(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check domain/URL with URLhaus database"""

        try:
            # URLhaus API (public, no key needed)
            data = {
                'host': domain
            }

            response = await self.client.post(self.urlhaus_api, data=data)

            if response.status_code == 200:
                result = response.json()

                if result.get('query_status') == 'ok':
                    urls = result.get('urls', [])
                    return {
                        "found": True,
                        "malware_url_count": len(urls),
                        "threat_types": list(set([u.get('threat', 'unknown') for u in urls[:10]])),
                        "tags": list(set([tag for u in urls[:10] for tag in u.get('tags', [])]))
                    }
                else:
                    return {"found": False}
            else:
                return None

        except Exception as e:
            logger.error(f"URLhaus check error for {domain}: {str(e)}")
            return None

    def _calculate_risk_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall content security risk score"""

        score = 0

        # Malicious JavaScript
        score += len(results["malicious_javascript"]) * 25

        # Exploit kits (critical)
        score += len(results["exploit_kits"]) * 40

        # Suspicious scripts
        score += len(results["suspicious_scripts"]) * 20

        # Obfuscated code
        score += len(results["obfuscated_code"]) * 10

        # Suspicious links
        high_sev_links = [l for l in results["suspicious_links"] if l.get("severity") == "high"]
        score += len(high_sev_links) * 15

        # Malware domains found
        score += len(results["external_resources"]["malware_domains"]) * 30

        # Threat intelligence flags
        dt_high_risk = sum(
            1 for d in results["threat_intelligence"]["domaintools"].values()
            if d.get("risk_score", 0) > 70
        )
        score += dt_high_risk * 25

        vt_malicious = sum(
            1 for d in results["threat_intelligence"]["virustotal"].values()
            if d.get("malicious_count", 0) > 5
        )
        score += vt_malicious * 30

        return min(score, 100)

    def _determine_risk_level(self, risk_score: int) -> str:
        """Determine risk level from score"""

        if risk_score >= 75:
            return "CRITICAL"
        elif risk_score >= 50:
            return "HIGH"
        elif risk_score >= 25:
            return "MEDIUM"
        elif risk_score > 0:
            return "LOW"
        else:
            return "CLEAN"

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary"""

        parts = []

        if results["exploit_kits"]:
            parts.append(f"{len(results['exploit_kits'])} exploit kit signatures detected")

        if results["malicious_javascript"]:
            parts.append(f"{len(results['malicious_javascript'])} malicious JavaScript patterns found")

        if results["external_resources"]["malware_domains"]:
            parts.append(f"{len(results['external_resources']['malware_domains'])} malware-associated domains")

        if results["obfuscated_code"]:
            parts.append(f"{len(results['obfuscated_code'])} obfuscated code segments")

        if results["suspicious_links"]:
            parts.append(f"{len(results['suspicious_links'])} suspicious links")

        if not parts:
            return "No significant malware indicators detected"

        return " | ".join(parts)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Utility function for quick checks
async def quick_malware_scan(html_content: str, url: str, domain: str) -> Dict[str, Any]:
    """Quick malware scan for integration"""
    analyzer = ContentSecurityAnalyzer()
    result = await analyzer.analyze_content_security(html_content, url, domain)
    await analyzer.close()
    return result
