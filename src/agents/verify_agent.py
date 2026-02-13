"""Verification Agent — re-tests after fixes and generates appeal documentation."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.data_models import (
    AppealDoc,
    Diagnosis,
    Platform,
    StabilityResult,
    TestResults,
    VerificationResult,
)
from src.agents.testing_agent import TestingAgent


class VerificationAgent:
    """Re-run failed tests, perform stability checks, generate appeal docs."""

    def __init__(self, testing_agent: Optional[TestingAgent] = None) -> None:
        self.testing_agent = testing_agent or TestingAgent()

    async def verify_fix(
        self,
        url: str,
        original_diagnosis: Diagnosis,
        platform: str = "microsoft",
    ) -> VerificationResult:
        # Re-run the full diagnostic suite
        new_results = await self.testing_agent.run_full_diagnostic_suite(url, platform)

        # Compare against original findings
        tests_passed, tests_failed = self._evaluate_results(
            new_results, original_diagnosis
        )

        all_passed = len(tests_failed) == 0

        result = VerificationResult(
            url=url,
            original_diagnosis=original_diagnosis,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            all_tests_passed=all_passed,
            ready_for_appeal=all_passed,
            new_test_results=new_results,
        )

        # Generate appeal doc if all tests pass
        if all_passed:
            appeal = self.generate_appeal_documentation(result, Platform(platform))
            result.appeal_doc = appeal

        return result

    async def stability_check(
        self, url: str, duration_minutes: int = 30, interval_seconds: int = 60
    ) -> StabilityResult:
        checks = max(1, duration_minutes * 60 // interval_seconds)
        passed = 0
        failures: List[Dict[str, Any]] = []

        for i in range(checks):
            if i > 0:
                await asyncio.sleep(interval_seconds)

            results = await self.testing_agent.run_full_diagnostic_suite(url)
            # A check passes if no user-agent discrimination and all HTTP tests are 200
            ok = (
                not results.has_user_agent_discrimination()
                and all(t.status_code == 200 for t in results.http_tests)
            )
            if ok:
                passed += 1
            else:
                http_statuses = {t.user_agent: t.status_code for t in results.http_tests}
                failures.append({"check": i + 1, "http_statuses": http_statuses})

        return StabilityResult(
            url=url,
            duration_minutes=duration_minutes,
            checks_performed=checks,
            checks_passed=passed,
            all_stable=len(failures) == 0,
            failures=failures,
        )

    def generate_appeal_documentation(
        self, verification: VerificationResult, platform: Platform
    ) -> AppealDoc:
        # Summarise fixes applied
        fixes_applied = [
            f"Resolved: {verification.original_diagnosis.primary_issue}"
        ]

        # Build evidence from new test results
        evidence: Dict[str, Any] = {}
        nr = verification.new_test_results
        if nr.http_tests:
            evidence["http_tests"] = [
                {"user_agent": t.user_agent, "status_code": t.status_code}
                for t in nr.http_tests
            ]
        if nr.dns_test:
            evidence["dns"] = {
                "a_records": nr.dns_test.a_records,
                "error": nr.dns_test.error,
            }
        if nr.robots_test:
            evidence["robots"] = {
                "blocks_googlebot": nr.robots_test.blocks_googlebot,
                "blocks_bingbot": nr.robots_test.blocks_bingbot,
            }
        if nr.geo_tests:
            evidence["geo"] = [
                {"location": g.location, "accessible": g.accessible}
                for g in nr.geo_tests
            ]

        summary_parts = [f"Tests passed: {', '.join(verification.tests_passed)}"]
        if verification.tests_failed:
            summary_parts.append(
                f"Tests still failing: {', '.join(verification.tests_failed)}"
            )
        else:
            summary_parts.append("All previously failing tests now pass.")

        return AppealDoc(
            platform=platform,
            url=verification.url,
            original_issue=verification.original_diagnosis.primary_issue,
            fixes_applied=fixes_applied,
            verification_summary="; ".join(summary_parts),
            test_evidence=evidence,
            generated_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_results(
        self, new_results: TestResults, original: Diagnosis
    ) -> tuple[list[str], list[str]]:
        passed: list[str] = []
        failed: list[str] = []

        issue = original.primary_issue

        # HTTP accessibility
        if new_results.http_tests:
            all_ok = all(t.status_code == 200 for t in new_results.http_tests)
            if all_ok:
                passed.append("http_accessibility")
            else:
                failed.append("http_accessibility")

        # User-agent discrimination
        if "Bot" in issue or "bot" in issue:
            if not new_results.has_user_agent_discrimination():
                passed.append("user_agent_equality")
            else:
                failed.append("user_agent_equality")

        # DNS
        if "DNS" in issue:
            if not new_results.has_dns_failure():
                passed.append("dns_resolution")
            else:
                failed.append("dns_resolution")

        # Robots
        if "Robots" in issue or "robots" in issue:
            if not new_results.has_robots_blocking():
                passed.append("robots_txt")
            else:
                failed.append("robots_txt")

        # Geo
        if "Geographic" in issue or "geo" in issue.lower():
            if not new_results.has_geo_blocking():
                passed.append("geographic_access")
            else:
                failed.append("geographic_access")

        # Redirect loop
        if "Redirect" in issue:
            if not new_results.has_redirect_loop():
                passed.append("redirect_chain")
            else:
                failed.append("redirect_chain")

        # SSL
        if "SSL" in issue or "TLS" in issue:
            if not new_results.has_ssl_error():
                passed.append("ssl_certificate")
            else:
                failed.append("ssl_certificate")

        # Performance
        if "Performance" in issue or "Timeout" in issue:
            if not new_results.has_performance_issue():
                passed.append("performance")
            else:
                failed.append("performance")

        # Tracking params
        if "Tracking" in issue:
            if not new_results.has_tracking_param_issue():
                passed.append("tracking_params")
            else:
                failed.append("tracking_params")

        # 404
        if "404" in issue:
            any_ok = any(t.status_code == 200 for t in new_results.http_tests)
            if any_ok:
                passed.append("page_exists")
            else:
                failed.append("page_exists")

        return passed, failed
