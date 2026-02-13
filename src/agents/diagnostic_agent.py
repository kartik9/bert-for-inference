"""Diagnostic Agent — analyzes test results and identifies root causes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.models.data_models import (
    Diagnosis,
    EditorialCode,
    Finding,
    HTTPTestResult,
    Platform,
    Severity,
    TestResults,
)


# Editorial code registry
_EDITORIAL_CODES: Dict[str, List[EditorialCode]] = {
    "bot_blocking": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_CRAWLABLE", "Destination not crawlable by Google AdsBot"),
    ],
    "robots_blocking": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_CRAWLABLE", "Destination not crawlable by Google AdsBot"),
    ],
    "dns_failure": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
    "geo_blocking": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_ACCESSIBLE", "Destination not accessible in targeted location"),
    ],
    "redirect_loop": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
    "http_404": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
    "ssl_error": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
    "performance": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
    "tracking_params": [
        EditorialCode(Platform.MICROSOFT, "4", "Website must be accessible at all times"),
        EditorialCode(Platform.GOOGLE, "DESTINATION_NOT_WORKING", "Destinations that don't function properly"),
    ],
}


class DiagnosticAgent:
    """Analyze test results, determine root cause with confidence scoring."""

    async def diagnose(
        self, test_results: TestResults, platform: str = "microsoft"
    ) -> Diagnosis:
        signals = self._extract_signals(test_results)
        findings = self._generate_findings(test_results, signals)

        # Determine primary issue via priority-ordered pattern matching
        diagnosis = self._pattern_match(test_results, signals, findings, platform)
        return diagnosis

    # ------------------------------------------------------------------
    # Signal extraction
    # ------------------------------------------------------------------

    def _extract_signals(self, results: TestResults) -> Dict[str, Any]:
        return {
            "user_agent_discrimination": results.has_user_agent_discrimination(),
            "dns_failure": results.has_dns_failure(),
            "ssl_error": results.has_ssl_error(),
            "robots_blocking": results.has_robots_blocking(),
            "geo_blocking": results.has_geo_blocking(),
            "redirect_loop": results.has_redirect_loop(),
            "tracking_param_issue": results.has_tracking_param_issue(),
            "performance_issue": results.has_performance_issue(),
            "security_layer": self._identify_security_layer(results),
            "all_http_fail": self._all_http_fail(results),
            "http_404": self._is_http_404(results),
        }

    # ------------------------------------------------------------------
    # Pattern matching (priority-ordered)
    # ------------------------------------------------------------------

    def _pattern_match(
        self,
        results: TestResults,
        signals: Dict[str, Any],
        findings: List[Finding],
        platform: str,
    ) -> Diagnosis:
        plat = Platform(platform)

        # 1. DNS failure — highest confidence, critical
        if signals["dns_failure"]:
            return self._build_diagnosis(
                primary_issue="DNS Resolution Failure",
                root_cause="DNS records are missing or misconfigured, making the domain unresolvable",
                confidence=1.0,
                severity=Severity.CRITICAL,
                findings=findings,
                platform=plat,
                category="dns_failure",
                why_works="The site may have worked previously but DNS records have expired or been removed",
                why_fails="Ad platform crawlers cannot resolve the domain to an IP address",
                mechanism="DNS lookup returns NXDOMAIN or no A records, preventing any HTTP connection",
            )

        # 2. Redirect loop — deterministic
        if signals["redirect_loop"]:
            chain = results.redirect_test.chain if results.redirect_test else []
            return self._build_diagnosis(
                primary_issue="Redirect Loop",
                root_cause=f"URL creates an infinite redirect loop: {' → '.join(chain[:5])}",
                confidence=1.0,
                severity=Severity.CRITICAL,
                findings=findings,
                platform=plat,
                category="redirect_loop",
                why_works="Browser may cache or break the loop, or user accesses a different URL",
                why_fails="Ad crawlers follow redirects strictly and detect the infinite loop",
                mechanism="Server responds with 3xx redirects that cycle back to a previously visited URL",
            )

        # 3. HTTP 404
        if signals["http_404"]:
            return self._build_diagnosis(
                primary_issue="HTTP 404 Not Found",
                root_cause="The landing page URL returns a 404 status code",
                confidence=1.0,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="http_404",
                why_works="User may be accessing a different URL or the page was recently removed",
                why_fails="Ad crawlers visit the exact ad destination URL and receive 404",
                mechanism="Web server returns HTTP 404 indicating the resource does not exist",
            )

        # 4. Bot blocking (user-agent discrimination + security layer)
        if signals["user_agent_discrimination"]:
            sec_layer = signals["security_layer"]
            layer_name = sec_layer or "server-side bot detection"
            return self._build_diagnosis(
                primary_issue="Bot Detection/Blocking",
                root_cause=f"{layer_name} is blocking ad platform crawlers while allowing browsers",
                confidence=0.90,
                severity=Severity.CRITICAL,
                findings=findings,
                platform=plat,
                category="bot_blocking",
                why_works="Normal browsers pass bot detection checks and see the page normally",
                why_fails="Ad crawlers use bot user-agents that trigger blocking rules",
                mechanism=f"{layer_name} identifies crawler user-agents and returns 403/challenge pages",
            )

        # 5. robots.txt blocking
        if signals["robots_blocking"]:
            return self._build_diagnosis(
                primary_issue="Robots.txt Blocking",
                root_cause="robots.txt file blocks ad platform crawlers from accessing the site",
                confidence=0.95,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="robots_blocking",
                why_works="Browsers ignore robots.txt — it only affects well-behaved crawlers",
                why_fails="Ad platform crawlers respect robots.txt Disallow directives",
                mechanism="robots.txt contains Disallow: / for Googlebot/Bingbot user-agents",
            )

        # 6. Geographic blocking
        if signals["geo_blocking"]:
            blocked = [g.location for g in results.geo_tests if not g.accessible]
            return self._build_diagnosis(
                primary_issue="Geographic Restriction",
                root_cause=f"Site is blocked in some geographic locations: {', '.join(blocked)}",
                confidence=0.85,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="geo_blocking",
                why_works="User is in an allowed geographic region",
                why_fails=f"Ad crawlers access from blocked regions: {', '.join(blocked)}",
                mechanism="Server or CDN geo-IP filtering blocks requests from certain regions",
            )

        # 7. SSL errors
        if signals["ssl_error"]:
            ssl_err = results.ssl_test.error if results.ssl_test else "Unknown SSL error"
            return self._build_diagnosis(
                primary_issue="SSL/TLS Certificate Error",
                root_cause=f"SSL certificate is invalid: {ssl_err}",
                confidence=0.80,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="ssl_error",
                why_works="User's browser may ignore or accept the certificate warning",
                why_fails="Ad crawlers enforce strict SSL validation and reject invalid certs",
                mechanism=f"SSL validation fails: {ssl_err}",
            )

        # 8. Performance / timeout
        if signals["performance_issue"]:
            perf = results.performance_test
            avg_ms = perf.avg_response_time_ms if perf else 0
            rate = perf.success_rate if perf else 0
            return self._build_diagnosis(
                primary_issue="Performance / Timeout",
                root_cause=f"Server responds too slowly (avg {avg_ms:.0f}ms) with {rate*100:.0f}% success rate",
                confidence=0.85,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="performance",
                why_works="User's browser waits longer; cached content may load faster",
                why_fails=f"Ad crawlers timeout after a few seconds; server success rate is only {rate*100:.0f}%",
                mechanism=f"Average response time is {avg_ms:.0f}ms, exceeding crawler timeout thresholds",
            )

        # 9. Tracking parameter issue
        if signals["tracking_param_issue"]:
            failed_params = [
                t for t in results.tracking_param_tests if t.status_code >= 400
            ]
            codes = [str(t.status_code) for t in failed_params]
            return self._build_diagnosis(
                primary_issue="Tracking Parameter Handling Error",
                root_cause=f"Site breaks when tracking parameters are appended (HTTP {', '.join(codes)})",
                confidence=0.90,
                severity=Severity.HIGH,
                findings=findings,
                platform=plat,
                category="tracking_params",
                why_works="The base URL without tracking parameters works fine",
                why_fails="Ad platforms append click tracking params (gclid/msclkid) which cause server errors",
                mechanism="Server-side code fails to handle unexpected query parameters",
            )

        # 10. All HTTP failures (generic)
        if signals["all_http_fail"]:
            codes = [str(t.status_code) for t in results.http_tests if t.status_code != 200]
            return self._build_diagnosis(
                primary_issue="HTTP Error",
                root_cause=f"All HTTP requests fail with status codes: {', '.join(set(codes))}",
                confidence=0.70,
                severity=Severity.CRITICAL,
                findings=findings,
                platform=plat,
                category="dns_failure",
                why_works="Site may be intermittently down or recently broken",
                why_fails="All requests — browser and bot — return errors",
                mechanism="Server returns non-200 status codes for all requests",
            )

        # Fallback — no clear issue detected
        return self._build_diagnosis(
            primary_issue="No Clear Issue Detected",
            root_cause="All tests passed; the site appears accessible. The issue may be intermittent.",
            confidence=0.50,
            severity=Severity.LOW,
            findings=findings,
            platform=plat,
            category="dns_failure",
            why_works="Site is accessible from our test locations",
            why_fails="The ad platform may have cached a previous failure or tests from other locations",
            mechanism="No specific blocking mechanism detected",
        )

    # ------------------------------------------------------------------
    # Finding generation
    # ------------------------------------------------------------------

    def _generate_findings(
        self, results: TestResults, signals: Dict[str, Any]
    ) -> List[Finding]:
        findings: List[Finding] = []

        if signals["dns_failure"]:
            err = results.dns_test.error if results.dns_test else "unknown"
            findings.append(Finding(
                finding="DNS resolution failure",
                evidence=f"DNS error: {err}",
                severity=Severity.CRITICAL,
                confidence=1.0,
                related_tests=["dns"],
            ))

        if signals["redirect_loop"]:
            chain = results.redirect_test.chain if results.redirect_test else []
            findings.append(Finding(
                finding="Redirect loop detected",
                evidence=f"Redirect chain: {' → '.join(chain[:5])}",
                severity=Severity.CRITICAL,
                confidence=1.0,
                related_tests=["redirect"],
            ))

        if signals["http_404"]:
            findings.append(Finding(
                finding="HTTP 404 Not Found",
                evidence="All HTTP tests returned 404",
                severity=Severity.HIGH,
                confidence=1.0,
                related_tests=["http"],
            ))

        if signals["user_agent_discrimination"]:
            bot_results = [
                t for t in results.http_tests if "bot" in t.user_agent.lower()
            ]
            evidence_parts = [
                f"{t.user_agent.split('(')[0].strip()}: HTTP {t.status_code}"
                for t in bot_results
            ]
            findings.append(Finding(
                finding="User-agent discrimination detected",
                evidence=f"Browser: 200, Bots: {', '.join(evidence_parts)}",
                severity=Severity.CRITICAL,
                confidence=0.90,
                related_tests=["http"],
            ))

        if signals["robots_blocking"]:
            findings.append(Finding(
                finding="robots.txt blocks crawlers",
                evidence=(
                    f"blocks_googlebot={results.robots_test.blocks_googlebot}, "
                    f"blocks_bingbot={results.robots_test.blocks_bingbot}"
                    if results.robots_test
                    else "robots.txt blocks crawlers"
                ),
                severity=Severity.HIGH,
                confidence=0.95,
                related_tests=["robots"],
            ))

        if signals["geo_blocking"]:
            blocked = [g for g in results.geo_tests if not g.accessible]
            findings.append(Finding(
                finding="Geographic access restrictions",
                evidence=f"Blocked in: {', '.join(g.location for g in blocked)}",
                severity=Severity.HIGH,
                confidence=0.85,
                related_tests=["geo"],
            ))

        if signals["ssl_error"]:
            err = results.ssl_test.error if results.ssl_test else "unknown"
            findings.append(Finding(
                finding="SSL certificate error",
                evidence=f"SSL error: {err}",
                severity=Severity.HIGH,
                confidence=0.80,
                related_tests=["ssl"],
            ))

        if signals["performance_issue"]:
            perf = results.performance_test
            findings.append(Finding(
                finding="Performance degradation",
                evidence=(
                    f"Avg response: {perf.avg_response_time_ms:.0f}ms, "
                    f"success rate: {perf.success_rate*100:.0f}%"
                    if perf
                    else "Performance issue detected"
                ),
                severity=Severity.HIGH,
                confidence=0.85,
                related_tests=["performance"],
            ))

        if signals["tracking_param_issue"]:
            failed = [t for t in results.tracking_param_tests if t.status_code >= 400]
            findings.append(Finding(
                finding="Tracking parameter handling error",
                evidence=f"URL with tracking params returns HTTP {failed[0].status_code}" if failed else "Tracking params cause errors",
                severity=Severity.HIGH,
                confidence=0.90,
                related_tests=["tracking_params"],
            ))

        sec_layer = signals.get("security_layer")
        if sec_layer:
            findings.append(Finding(
                finding=f"Security layer detected: {sec_layer}",
                evidence=f"Response headers indicate {sec_layer} is active",
                severity=Severity.MEDIUM,
                confidence=0.85,
                related_tests=["http"],
            ))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _identify_security_layer(self, results: TestResults) -> Optional[str]:
        for test in results.http_tests:
            headers_lower = {k.lower(): v.lower() for k, v in test.headers.items()}
            server = headers_lower.get("server", "")
            if "cloudflare" in server:
                return "Cloudflare"
            if "akamai" in server or "akamaighost" in server:
                return "Akamai"
            if headers_lower.get("x-sucuri-id"):
                return "Sucuri"
            if "imperva" in server or headers_lower.get("x-iinfo"):
                return "Imperva"
            if headers_lower.get("x-aws-waf"):
                return "AWS WAF"
            if "cf-mitigated" in headers_lower:
                return "Cloudflare"
        return None

    @staticmethod
    def _detect_user_agent_discrimination(results: List[HTTPTestResult]) -> bool:
        browser = next(
            (t for t in results if "bot" not in t.user_agent.lower()), None
        )
        bots = [t for t in results if "bot" in t.user_agent.lower()]
        return (
            browser is not None
            and browser.status_code == 200
            and any(b.status_code != 200 for b in bots)
        )

    @staticmethod
    def _all_http_fail(results: TestResults) -> bool:
        if not results.http_tests:
            return False
        return all(t.status_code != 200 for t in results.http_tests)

    @staticmethod
    def _is_http_404(results: TestResults) -> bool:
        if not results.http_tests:
            return False
        return all(t.status_code == 404 for t in results.http_tests)

    def _match_editorial_codes(
        self, category: str, platform: Platform
    ) -> List[EditorialCode]:
        codes = _EDITORIAL_CODES.get(category, [])
        return [c for c in codes if c.platform == platform]

    def _build_diagnosis(
        self,
        *,
        primary_issue: str,
        root_cause: str,
        confidence: float,
        severity: Severity,
        findings: List[Finding],
        platform: Platform,
        category: str,
        why_works: str,
        why_fails: str,
        mechanism: str,
    ) -> Diagnosis:
        editorial_codes = self._match_editorial_codes(category, platform)
        reasoning = [f.finding for f in findings]
        reasoning.append(f"Primary issue identified: {primary_issue}")
        reasoning.append(f"Root cause: {root_cause}")

        return Diagnosis(
            primary_issue=primary_issue,
            root_cause=root_cause,
            confidence=confidence,
            severity=severity,
            findings=findings,
            editorial_codes=editorial_codes,
            reasoning_chain=reasoning,
            why_works_for_user=why_works,
            why_fails_for_ads=why_fails,
            technical_mechanism=mechanism,
            impact_assessment={
                "affects_all_ads": severity in (Severity.CRITICAL, Severity.HIGH),
                "requires_immediate_action": severity == Severity.CRITICAL,
            },
        )
