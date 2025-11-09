"""
Shodan Infrastructure Intelligence Module
Provides infrastructure and security intelligence for URL safety analysis
"""

import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import socket

try:
    import shodan
    SHODAN_AVAILABLE = True
except ImportError:
    SHODAN_AVAILABLE = False
    logging.warning("Shodan library not installed. Run: pip install shodan")

logger = logging.getLogger(__name__)


class ShodanAnalyzer:
    """
    Provides infrastructure intelligence using Shodan API
    """

    def __init__(self):
        self.api_key = os.getenv('SHODAN_API_KEY')
        self.api = None

        if not SHODAN_AVAILABLE:
            logger.warning("Shodan library not available")
            return

        if self.api_key:
            try:
                self.api = shodan.Shodan(self.api_key)
                logger.info("Shodan API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Shodan API: {str(e)}")
        else:
            logger.warning("SHODAN_API_KEY not configured")

    def is_configured(self) -> bool:
        """Check if Shodan is properly configured"""
        return self.api is not None

    async def analyze_infrastructure(
        self,
        url: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Perform infrastructure intelligence analysis on target URL/domain

        Args:
            url: Full URL being investigated
            domain: Extracted domain name

        Returns: Dictionary with infrastructure intelligence findings
        """
        if not self.is_configured():
            return {
                "checked": False,
                "error": "Shodan not configured",
                "message": "SHODAN_API_KEY not set or library not available"
            }

        logger.info(f"Analyzing infrastructure for: {domain}")

        results = {
            "checked": True,
            "domain": domain,
            "host_intelligence": None,
            "services": [],
            "vulnerabilities": [],
            "ssl_info": None,
            "risk_indicators": [],
            "summary": ""
        }

        try:
            # Resolve domain to IP
            ip_address = await self._resolve_domain(domain)

            if not ip_address:
                results["error"] = "Could not resolve domain to IP"
                return results

            results["ip_address"] = ip_address

            # Query Shodan for host information
            host_info = await self._get_host_info(ip_address)

            if host_info:
                results["host_intelligence"] = self._extract_host_intelligence(host_info)
                results["services"] = self._extract_services(host_info)
                results["vulnerabilities"] = self._extract_vulnerabilities(host_info)
                results["ssl_info"] = self._extract_ssl_info(host_info)
                results["risk_indicators"] = self._assess_risk_indicators(host_info, domain)
                results["summary"] = self._generate_summary(results)

        except Exception as e:
            logger.error(f"Error during Shodan analysis: {str(e)}")
            results["error"] = str(e)

        return results

    async def _resolve_domain(self, domain: str) -> Optional[str]:
        """Resolve domain to IP address"""
        try:
            ip_address = socket.gethostbyname(domain)
            logger.info(f"Resolved {domain} to {ip_address}")
            return ip_address
        except socket.gaierror as e:
            logger.warning(f"Could not resolve {domain}: {str(e)}")
            return None

    async def _get_host_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Query Shodan API for host information"""
        try:
            host = self.api.host(ip_address)
            return host
        except shodan.APIError as e:
            logger.warning(f"Shodan API error for {ip_address}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error querying Shodan: {str(e)}")
            return None

    def _extract_host_intelligence(self, host_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key host intelligence from Shodan data"""
        return {
            "ip": host_info.get("ip_str"),
            "organization": host_info.get("org", "Unknown"),
            "isp": host_info.get("isp", "Unknown"),
            "asn": host_info.get("asn", "Unknown"),
            "country": host_info.get("country_name", "Unknown"),
            "city": host_info.get("city", "Unknown"),
            "hostnames": host_info.get("hostnames", []),
            "domains": host_info.get("domains", []),
            "tags": host_info.get("tags", []),
            "ports": host_info.get("ports", []),
            "last_update": host_info.get("last_update", "Unknown")
        }

    def _extract_services(self, host_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract service information from Shodan data"""
        services = []

        for item in host_info.get("data", []):
            service = {
                "port": item.get("port"),
                "protocol": item.get("transport", "tcp"),
                "service": item.get("product", item.get("_shodan", {}).get("module", "unknown")),
                "version": item.get("version", ""),
                "banner": item.get("data", "")[:200],  # Truncate banner
            }

            # Check for concerning patterns in banner
            banner_lower = service["banner"].lower()
            if any(keyword in banner_lower for keyword in ["admin", "default", "test", "debug"]):
                service["concern"] = "Potentially insecure configuration detected in banner"

            services.append(service)

        return services

    def _extract_vulnerabilities(self, host_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract vulnerability information (CVEs)"""
        vulnerabilities = []

        for item in host_info.get("data", []):
            vulns = item.get("vulns", {})

            for cve_id, cve_data in vulns.items():
                vuln = {
                    "cve_id": cve_id,
                    "port": item.get("port"),
                    "service": item.get("product", "unknown"),
                    "severity": "unknown"
                }

                # Try to determine severity from CVE data if available
                if isinstance(cve_data, dict):
                    vuln["cvss"] = cve_data.get("cvss")
                    vuln["summary"] = cve_data.get("summary", "")

                vulnerabilities.append(vuln)

        return vulnerabilities

    def _extract_ssl_info(self, host_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract SSL/TLS certificate information"""
        for item in host_info.get("data", []):
            if "ssl" in item:
                ssl_data = item["ssl"]
                cert = ssl_data.get("cert", {})

                return {
                    "port": item.get("port"),
                    "version": ssl_data.get("version", "unknown"),
                    "cipher": ssl_data.get("cipher", {}),
                    "certificate": {
                        "subject": cert.get("subject", {}),
                        "issuer": cert.get("issuer", {}),
                        "expires": cert.get("expires", "Unknown"),
                        "fingerprint": cert.get("fingerprint", {})
                    },
                    "dhparams": ssl_data.get("dhparams"),
                    "chain": ssl_data.get("chain", [])
                }

        return None

    def _assess_risk_indicators(
        self,
        host_info: Dict[str, Any],
        domain: str
    ) -> List[Dict[str, Any]]:
        """Assess risk indicators from Shodan data"""
        risk_indicators = []

        # Check for malicious tags
        tags = host_info.get("tags", [])
        malicious_tags = ["malware", "compromised", "botnet", "spam", "phishing",
                         "ransomware", "c2", "exploit", "scanner"]

        for tag in tags:
            if tag.lower() in malicious_tags:
                risk_indicators.append({
                    "type": "malicious_tag",
                    "severity": "high",
                    "description": f"Host tagged as: {tag}",
                    "source": "Shodan"
                })

        # Check for unusual open ports
        ports = host_info.get("ports", [])
        unusual_ports = [port for port in ports if port not in [80, 443, 22, 21, 25, 53]]

        if len(unusual_ports) > 5:
            risk_indicators.append({
                "type": "unusual_ports",
                "severity": "medium",
                "description": f"Many unusual open ports detected: {unusual_ports[:10]}",
                "source": "Shodan"
            })

        # Check for vulnerabilities
        total_vulns = 0
        for item in host_info.get("data", []):
            total_vulns += len(item.get("vulns", {}))

        if total_vulns > 0:
            severity = "critical" if total_vulns > 5 else "high" if total_vulns > 2 else "medium"
            risk_indicators.append({
                "type": "known_vulnerabilities",
                "severity": severity,
                "description": f"{total_vulns} known vulnerabilities (CVEs) detected",
                "source": "Shodan"
            })

        # Check for development/testing indicators
        hostnames = host_info.get("hostnames", [])
        dev_keywords = ["test", "dev", "staging", "demo", "temp"]

        for hostname in hostnames:
            hostname_lower = hostname.lower()
            if any(keyword in hostname_lower for keyword in dev_keywords):
                risk_indicators.append({
                    "type": "development_environment",
                    "severity": "low",
                    "description": f"Hostname suggests development/testing environment: {hostname}",
                    "source": "Shodan"
                })
                break

        # Check organization/ISP for cheap hosting patterns
        org = host_info.get("org", "").lower()
        isp = host_info.get("isp", "").lower()

        cheap_hosting = ["digitalocean", "ovh", "hetzner", "alibaba", "vultr",
                        "linode", "scaleway", "contabo"]

        if any(provider in org or provider in isp for provider in cheap_hosting):
            # Note: This is not necessarily bad, but worth noting for scam analysis
            risk_indicators.append({
                "type": "budget_hosting",
                "severity": "info",
                "description": f"Hosted on budget cloud provider: {host_info.get('org', 'Unknown')}",
                "source": "Shodan",
                "note": "Not necessarily malicious, but commonly used for disposable scam infrastructure"
            })

        return risk_indicators

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary of Shodan findings"""
        summary_parts = []

        host_intel = results.get("host_intelligence", {})
        if host_intel:
            summary_parts.append(
                f"Hosted by {host_intel.get('organization', 'Unknown')} "
                f"in {host_intel.get('country', 'Unknown')}"
            )

        vulns = results.get("vulnerabilities", [])
        if vulns:
            summary_parts.append(f"{len(vulns)} known vulnerabilities detected")

        risk_indicators = results.get("risk_indicators", [])
        high_risk = [r for r in risk_indicators if r.get("severity") in ["high", "critical"]]
        if high_risk:
            summary_parts.append(f"{len(high_risk)} high-risk indicators found")

        tags = host_intel.get("tags", []) if host_intel else []
        if tags:
            summary_parts.append(f"Tagged as: {', '.join(tags[:3])}")

        if not summary_parts:
            return "No significant infrastructure concerns detected"

        return " | ".join(summary_parts)


# Utility function for follow-up investigations
async def quick_shodan_lookup(domain: str) -> Dict[str, Any]:
    """Quick Shodan lookup for follow-up investigations"""
    analyzer = ShodanAnalyzer()

    if not analyzer.is_configured():
        return {
            "checked": False,
            "error": "Shodan not configured"
        }

    return await analyzer.analyze_infrastructure(
        url=f"https://{domain}",
        domain=domain
    )
