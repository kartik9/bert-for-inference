"""End-to-end tests: Orchestrator with mocked testing agent."""

from __future__ import annotations

from typing import List, Optional
from unittest.mock import AsyncMock, patch

import pytest

from src.models.data_models import (
    DNSTestResult,
    GeoTestResult,
    HTTPTestResult,
    PerformanceTestResult,
    Platform,
    RedirectTestResult,
    RobotsTestResult,
    Severity,
    TestResults,
    UserRequest,
)
from src.agents.orchestrator import OrchestratorAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _http(url: str, ua: str, status: int, *, headers: dict | None = None, error: str | None = None) -> HTTPTestResult:
    return HTTPTestResult(
        url=url,
        user_agent=ua,
        status_code=status,
        response_time_ms=120.0,
        headers=headers or {},
        content_length=5000,
        error=error,
    )


UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
UA_BINGBOT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
URL = "https://example.com/landing"


def _mock_test_results(
    *,
    http_tests: List[HTTPTestResult] | None = None,
    dns_test: Optional[DNSTestResult] = None,
    robots_test: Optional[RobotsTestResult] = None,
    geo_tests: List[GeoTestResult] | None = None,
    redirect_test: Optional[RedirectTestResult] = None,
    performance_test: Optional[PerformanceTestResult] = None,
    tracking_param_tests: List[HTTPTestResult] | None = None,
    platform: Platform = Platform.MICROSOFT,
) -> TestResults:
    return TestResults(
        url=URL,
        platform=platform,
        http_tests=http_tests or [],
        dns_test=dns_test,
        robots_test=robots_test,
        geo_tests=geo_tests or [],
        redirect_test=redirect_test,
        performance_test=performance_test,
        tracking_param_tests=tracking_param_tests or [],
    )


# ---------------------------------------------------------------------------
# E2E Scenario 1: Cloudflare blocking — full pipeline
# ---------------------------------------------------------------------------

class TestE2ECloudflareBlocking:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 403, headers={"server": "cloudflare", "cf-mitigated": "challenge"}),
                _http(URL, UA_BINGBOT, 403, headers={"server": "cloudflare"}),
            ],
            dns_test=DNSTestResult(
                domain="example.com", a_records=["93.184.216.34"],
                ns_records=["ns1.example.com"], ttl=3600,
                dnssec_enabled=False, resolution_time_ms=25.0,
            ),
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "Bot Detection/Blocking"
        assert response.diagnosis.severity == Severity.CRITICAL
        assert response.diagnosis.confidence == 0.90
        assert len(response.fix_plan.fixes) >= 1
        assert response.fix_plan.fixes[0].category == "cloudflare"
        assert any("CRITICAL" in w for w in response.fix_plan.warnings)


# ---------------------------------------------------------------------------
# E2E Scenario 2: DNS failure — full pipeline
# ---------------------------------------------------------------------------

class TestE2EDNSFailure:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 0, error="DNS resolution failed"),
                _http(URL, UA_GOOGLEBOT, 0, error="DNS resolution failed"),
            ],
            dns_test=DNSTestResult(
                domain="example.com", a_records=[], ns_records=[],
                ttl=0, dnssec_enabled=False, resolution_time_ms=5000.0,
                error="NXDOMAIN",
            ),
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "DNS Resolution Failure"
        assert response.diagnosis.confidence == 1.0
        assert response.fix_plan.fixes[0].fix_id == "dns-fix-records"


# ---------------------------------------------------------------------------
# E2E Scenario 3: robots.txt blocking — full pipeline
# ---------------------------------------------------------------------------

class TestE2ERobotsBlocking:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 200),
            ],
            robots_test=RobotsTestResult(
                url=f"{URL}/robots.txt", exists=True,
                content="User-agent: *\nDisallow: /",
                blocks_googlebot=True, blocks_bingbot=True, sitemaps=[],
            ),
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "Robots.txt Blocking"
        assert response.diagnosis.confidence == 0.95
        assert response.fix_plan.fixes[0].fix_id == "robots-allow-crawlers"


# ---------------------------------------------------------------------------
# E2E Scenario 4: Redirect loop — full pipeline
# ---------------------------------------------------------------------------

class TestE2ERedirectLoop:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 200),
            ],
            redirect_test=RedirectTestResult(
                url=URL,
                chain=[URL, "https://example.com/a", URL],
                final_url=URL, num_redirects=2, has_loop=True,
                status_codes=[302, 302, 302],
            ),
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "Redirect Loop"
        assert response.diagnosis.confidence == 1.0
        assert response.fix_plan.fixes[0].fix_id == "fix-redirect-loop"


# ---------------------------------------------------------------------------
# E2E Scenario 5: 404 — full pipeline
# ---------------------------------------------------------------------------

class TestE2EHTTP404:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 404),
                _http(URL, UA_GOOGLEBOT, 404),
                _http(URL, UA_BINGBOT, 404),
            ],
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "HTTP 404 Not Found"
        assert response.diagnosis.confidence == 1.0
        assert response.fix_plan.fixes[0].fix_id == "fix-404"


# ---------------------------------------------------------------------------
# E2E Scenario 6: Tracking params — full pipeline
# ---------------------------------------------------------------------------

class TestE2ETrackingParams:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 200),
            ],
            tracking_param_tests=[
                _http(f"{URL}?msclkid=test123", UA_BROWSER, 500),
            ],
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="microsoft")
            )

        assert response.diagnosis.primary_issue == "Tracking Parameter Handling Error"
        assert response.diagnosis.confidence == 0.90
        assert response.fix_plan.fixes[0].fix_id == "fix-tracking-params"


# ---------------------------------------------------------------------------
# E2E Scenario 7: Verification pass
# ---------------------------------------------------------------------------

class TestE2EVerification:
    @pytest.mark.asyncio
    async def test_verification_after_fix(self) -> None:
        # Initial: bot blocking
        initial_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 403, headers={"server": "cloudflare"}),
            ],
        )
        # After fix: all OK
        fixed_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 200),
                _http(URL, UA_BINGBOT, 200),
            ],
        )

        orchestrator = OrchestratorAgent.create()

        # First call returns initial, second returns fixed
        orchestrator.testing_agent.run_full_diagnostic_suite = AsyncMock(
            side_effect=[initial_results, fixed_results]
        )

        response = await orchestrator.process_request(
            UserRequest(url=URL, platform="microsoft"),
            run_verification=True,
        )

        assert response.diagnosis.primary_issue == "Bot Detection/Blocking"
        assert response.verification is not None
        assert response.verification.all_tests_passed is True
        assert response.verification.ready_for_appeal is True
        assert response.verification.appeal_doc is not None


# ---------------------------------------------------------------------------
# E2E: Google platform
# ---------------------------------------------------------------------------

class TestE2EGooglePlatform:
    @pytest.mark.asyncio
    async def test_google_bot_blocking(self) -> None:
        mock_results = _mock_test_results(
            http_tests=[
                _http(URL, UA_BROWSER, 200),
                _http(URL, UA_GOOGLEBOT, 403),
                _http(URL, UA_BINGBOT, 403),
            ],
            platform=Platform.GOOGLE,
        )

        orchestrator = OrchestratorAgent.create()
        with patch.object(
            orchestrator.testing_agent,
            "run_full_diagnostic_suite",
            new=AsyncMock(return_value=mock_results),
        ):
            response = await orchestrator.process_request(
                UserRequest(url=URL, platform="google")
            )

        assert response.diagnosis.primary_issue == "Bot Detection/Blocking"
        codes = [c.code for c in response.diagnosis.editorial_codes]
        assert "DESTINATION_NOT_CRAWLABLE" in codes
