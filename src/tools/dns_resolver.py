"""DNS resolution tool."""

from __future__ import annotations

import time
from typing import Optional
from urllib.parse import urlparse

import dns.resolver
import dns.rdatatype

from src.models.data_models import DNSTestResult


class DNSResolver:
    """Resolve DNS records for a domain."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _extract_domain(self, url_or_domain: str) -> str:
        if "://" in url_or_domain:
            return urlparse(url_or_domain).hostname or url_or_domain
        return url_or_domain

    async def resolve(self, url_or_domain: str) -> DNSTestResult:
        domain = self._extract_domain(url_or_domain)
        start = time.monotonic()

        a_records: list[str] = []
        ns_records: list[str] = []
        ttl = 0
        dnssec = False
        error: Optional[str] = None

        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            # A records
            try:
                answer = resolver.resolve(domain, "A")
                a_records = [rdata.address for rdata in answer]
                ttl = answer.rrset.ttl if answer.rrset else 0
            except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                pass

            # NS records
            try:
                ns_answer = resolver.resolve(domain, "NS")
                ns_records = [str(rdata.target) for rdata in ns_answer]
            except (dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.resolver.NXDOMAIN):
                pass

            # DNSSEC check
            try:
                resolver.resolve(domain, "DNSKEY")
                dnssec = True
            except Exception:
                dnssec = False

            if not a_records:
                error = "No A records found"

        except dns.resolver.NXDOMAIN:
            error = "NXDOMAIN"
        except dns.resolver.Timeout:
            error = "DNS resolution timed out"
        except Exception as exc:
            error = str(exc)

        elapsed = (time.monotonic() - start) * 1000
        return DNSTestResult(
            domain=domain,
            a_records=a_records,
            ns_records=ns_records,
            ttl=ttl,
            dnssec_enabled=dnssec,
            resolution_time_ms=round(elapsed, 2),
            error=error,
        )
