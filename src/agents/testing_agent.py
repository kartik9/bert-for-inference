"""Testing Agent — executes technical tests and returns raw data."""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

from src.models.data_models import (
    GeoTestResult,
    HTTPTestResult,
    PerformanceTestResult,
    Platform,
    RedirectTestResult,
    RobotsTestResult,
    SSLTestResult,
    TestConfig,
    TestResults,
)
from src.tools.http_client import AsyncHTTPClient
from src.tools.dns_resolver import DNSResolver
from src.tools.ssl_validator import SSLValidator


class TestingAgent:
    """Run all diagnostic tests against a URL. Returns raw data only."""

    def __init__(self, config: Optional[TestConfig] = None) -> None:
        self.config = config or TestConfig()
        self.http_client = AsyncHTTPClient(self.config)
        self.dns_resolver = DNSResolver(timeout=self.config.timeout_seconds)
        self.ssl_validator = SSLValidator(timeout=self.config.timeout_seconds)

    # ------------------------------------------------------------------
    # Full suite
    # ------------------------------------------------------------------

    async def run_full_diagnostic_suite(
        self, url: str, platform: str = "microsoft"
    ) -> TestResults:
        plat = Platform(platform)

        http_tests, dns_test, ssl_test, robots_test, geo_tests, redirect_test, tracking_tests = (
            await asyncio.gather(
                self._run_http_tests(url),
                self.test_dns_resolution(urlparse(url).hostname or url),
                self.test_ssl_certificate(url),
                self.test_robots_txt(url),
                self.test_geographic_access(url, self.config.proxy_locations),
                self.test_redirect_chain(url),
                self.test_with_tracking_params(url, platform),
                return_exceptions=True,
            )
        )

        # Safely unpack — treat exceptions as None / empty
        http_tests = http_tests if isinstance(http_tests, list) else []
        dns_test = dns_test if not isinstance(dns_test, BaseException) else None
        ssl_test = ssl_test if not isinstance(ssl_test, BaseException) else None
        robots_test = robots_test if not isinstance(robots_test, BaseException) else None
        geo_tests = geo_tests if isinstance(geo_tests, list) else []
        redirect_test = redirect_test if not isinstance(redirect_test, BaseException) else None
        tracking_tests = tracking_tests if isinstance(tracking_tests, list) else []

        # Performance test is sequential (multiple iterations)
        try:
            perf_test = await self.test_performance(url, iterations=5)
        except Exception:
            perf_test = None

        return TestResults(
            url=url,
            platform=plat,
            http_tests=http_tests,
            dns_test=dns_test,
            ssl_test=ssl_test,
            robots_test=robots_test,
            geo_tests=geo_tests,
            redirect_test=redirect_test,
            performance_test=perf_test,
            tracking_param_tests=tracking_tests,
        )

    # ------------------------------------------------------------------
    # Individual tests
    # ------------------------------------------------------------------

    async def _run_http_tests(self, url: str) -> List[HTTPTestResult]:
        return await self.http_client.fetch_with_agents(url)

    async def test_http_status(
        self,
        url: str,
        user_agent: str,
        location: Optional[str] = None,
    ) -> HTTPTestResult:
        proxy = self._proxy_for_location(location) if location else None
        return await self.http_client.fetch(url, user_agent, proxy=proxy)

    async def test_dns_resolution(self, domain: str):
        return await self.dns_resolver.resolve(domain)

    async def test_ssl_certificate(self, url: str) -> SSLTestResult:
        return await self.ssl_validator.validate(url)

    async def test_robots_txt(self, url: str) -> RobotsTestResult:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        result = await self.http_client.fetch(
            robots_url, self.config.user_agents["browser"]
        )

        if result.status_code != 200 or result.error:
            return RobotsTestResult(
                url=robots_url,
                exists=False,
                content=None,
                blocks_googlebot=False,
                blocks_bingbot=False,
                sitemaps=[],
            )

        # Fetch the actual content
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.get(robots_url)
                content = resp.text
        except Exception:
            content = ""

        blocks_googlebot = self._robots_blocks_agent(content, "googlebot")
        blocks_bingbot = self._robots_blocks_agent(content, "bingbot")
        sitemaps = [
            line.split(":", 1)[1].strip()
            for line in content.splitlines()
            if line.lower().startswith("sitemap:")
        ]

        return RobotsTestResult(
            url=robots_url,
            exists=True,
            content=content,
            blocks_googlebot=blocks_googlebot,
            blocks_bingbot=blocks_bingbot,
            sitemaps=sitemaps,
        )

    async def test_geographic_access(
        self, url: str, locations: List[str]
    ) -> List[GeoTestResult]:
        results: List[GeoTestResult] = []
        for loc in locations:
            proxy = self._proxy_for_location(loc)
            http_result = await self.http_client.fetch(
                url, self.config.user_agents["browser"], proxy=proxy
            )
            results.append(
                GeoTestResult(
                    url=url,
                    location=loc,
                    proxy_ip=proxy or "direct",
                    status_code=http_result.status_code,
                    accessible=http_result.status_code == 200,
                    response_time_ms=http_result.response_time_ms,
                )
            )
        return results

    async def test_redirect_chain(self, url: str) -> RedirectTestResult:
        chain_results = await self.http_client.fetch_redirect_chain(url)
        urls = [r.url for r in chain_results]
        status_codes = [r.status_code for r in chain_results]

        # Detect loop
        has_loop = len(urls) != len(set(urls))

        final_url = urls[-1] if urls else url
        # If the last response was a redirect with a location, that's the final target
        if chain_results and chain_results[-1].location:
            final_url = chain_results[-1].location

        return RedirectTestResult(
            url=url,
            chain=urls,
            final_url=final_url,
            num_redirects=max(0, len(urls) - 1),
            has_loop=has_loop,
            status_codes=status_codes,
        )

    async def test_with_tracking_params(
        self, url: str, platform: str
    ) -> List[HTTPTestResult]:
        params_map: Dict[str, Dict[str, str]] = {
            "microsoft": {"msclkid": "test_click_id_12345"},
            "google": {"gclid": "test_click_id_12345"},
        }
        params = params_map.get(platform, params_map["microsoft"])

        parsed = urlparse(url)
        existing_qs = parse_qs(parsed.query)
        existing_qs.update(params)
        new_query = urlencode(existing_qs, doseq=True)
        test_url = urlunparse(parsed._replace(query=new_query))

        result = await self.http_client.fetch(
            test_url, self.config.user_agents["browser"]
        )
        return [result]

    async def test_performance(
        self, url: str, iterations: int = 5
    ) -> PerformanceTestResult:
        times: List[float] = []
        successes = 0
        timeouts = 0
        errors = 0

        for _ in range(iterations):
            result = await self.http_client.fetch(
                url, self.config.user_agents["browser"]
            )
            if result.error:
                if "timeout" in (result.error or "").lower():
                    timeouts += 1
                else:
                    errors += 1
            else:
                successes += 1
            times.append(result.response_time_ms)

        sorted_times = sorted(times)
        p95_idx = max(0, int(len(sorted_times) * 0.95) - 1)

        return PerformanceTestResult(
            url=url,
            iterations=iterations,
            avg_response_time_ms=round(sum(times) / len(times), 2) if times else 0,
            min_response_time_ms=round(min(times), 2) if times else 0,
            max_response_time_ms=round(max(times), 2) if times else 0,
            p95_response_time_ms=round(sorted_times[p95_idx], 2) if sorted_times else 0,
            success_rate=round(successes / iterations, 2) if iterations else 0,
            timeout_count=timeouts,
            error_count=errors,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _robots_blocks_agent(content: str, agent: str) -> bool:
        """Simple robots.txt parser — checks for Disallow: / under the agent."""
        lines = content.lower().splitlines()
        in_agent_block = False
        for line in lines:
            line = line.strip()
            if line.startswith("user-agent:"):
                ua = line.split(":", 1)[1].strip()
                in_agent_block = ua == agent.lower() or ua == "*"
            elif line.startswith("disallow:") and in_agent_block:
                path = line.split(":", 1)[1].strip()
                if path == "/":
                    return True
            elif line.startswith("user-agent:"):
                in_agent_block = False
        return False

    @staticmethod
    def _proxy_for_location(location: str) -> Optional[str]:
        """Return proxy URL for a geographic location.

        In production this would return real proxy endpoints.
        Returns None for now (direct connection).
        """
        # Placeholder — real implementation would use ProxyMesh or similar
        return None
