"""Data models for AdDoctor: Inaccessible Site Debugger."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class Platform(Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Test result models
# ---------------------------------------------------------------------------

@dataclass
class HTTPTestResult:
    url: str
    user_agent: str
    status_code: int
    response_time_ms: float
    headers: Dict[str, str]
    content_length: int
    location: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DNSTestResult:
    domain: str
    a_records: List[str]
    ns_records: List[str]
    ttl: int
    dnssec_enabled: bool
    resolution_time_ms: float
    error: Optional[str] = None


@dataclass
class SSLTestResult:
    url: str
    valid: bool
    issuer: Optional[str] = None
    subject: Optional[str] = None
    not_before: Optional[datetime] = None
    not_after: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    protocol_version: Optional[str] = None
    cipher_suite: Optional[str] = None
    error: Optional[str] = None


@dataclass
class RobotsTestResult:
    url: str
    exists: bool
    content: Optional[str]
    blocks_googlebot: bool
    blocks_bingbot: bool
    sitemaps: List[str]


@dataclass
class GeoTestResult:
    url: str
    location: str
    proxy_ip: str
    status_code: int
    accessible: bool
    response_time_ms: float


@dataclass
class RedirectTestResult:
    url: str
    chain: List[str]
    final_url: str
    num_redirects: int
    has_loop: bool
    status_codes: List[int]
    error: Optional[str] = None


@dataclass
class PerformanceTestResult:
    url: str
    iterations: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    success_rate: float
    timeout_count: int
    error_count: int


# ---------------------------------------------------------------------------
# Aggregate test results
# ---------------------------------------------------------------------------

@dataclass
class TestResults:
    url: str
    platform: Platform
    http_tests: List[HTTPTestResult]
    dns_test: Optional[DNSTestResult] = None
    ssl_test: Optional[SSLTestResult] = None
    robots_test: Optional[RobotsTestResult] = None
    geo_tests: List[GeoTestResult] = field(default_factory=list)
    redirect_test: Optional[RedirectTestResult] = None
    performance_test: Optional[PerformanceTestResult] = None
    tracking_param_tests: List[HTTPTestResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def has_user_agent_discrimination(self) -> bool:
        """Return True when browsers succeed but bots are blocked."""
        browser = next(
            (t for t in self.http_tests if "bot" not in t.user_agent.lower()),
            None,
        )
        bots = [t for t in self.http_tests if "bot" in t.user_agent.lower()]
        return (
            browser is not None
            and browser.status_code == 200
            and any(b.status_code != 200 for b in bots)
        )

    def has_dns_failure(self) -> bool:
        return self.dns_test is not None and self.dns_test.error is not None

    def has_ssl_error(self) -> bool:
        return self.ssl_test is not None and not self.ssl_test.valid

    def has_robots_blocking(self) -> bool:
        if self.robots_test is None:
            return False
        return self.robots_test.blocks_googlebot or self.robots_test.blocks_bingbot

    def has_geo_blocking(self) -> bool:
        return any(not g.accessible for g in self.geo_tests)

    def has_redirect_loop(self) -> bool:
        return self.redirect_test is not None and self.redirect_test.has_loop

    def has_tracking_param_issue(self) -> bool:
        if not self.tracking_param_tests:
            return False
        return any(t.status_code >= 400 for t in self.tracking_param_tests)

    def has_performance_issue(self) -> bool:
        if self.performance_test is None:
            return False
        return (
            self.performance_test.avg_response_time_ms > 5000
            or self.performance_test.success_rate < 0.8
        )


# ---------------------------------------------------------------------------
# Diagnostic models
# ---------------------------------------------------------------------------

@dataclass
class EditorialCode:
    platform: Platform
    code: str
    description: str
    url: Optional[str] = None


@dataclass
class Finding:
    finding: str
    evidence: str
    severity: Severity
    confidence: float
    related_tests: List[str]


@dataclass
class Diagnosis:
    primary_issue: str
    root_cause: str
    confidence: float
    severity: Severity
    findings: List[Finding]
    editorial_codes: List[EditorialCode]
    reasoning_chain: List[str]
    why_works_for_user: str
    why_fails_for_ads: str
    technical_mechanism: str
    impact_assessment: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fix models
# ---------------------------------------------------------------------------

@dataclass
class CodeSnippet:
    language: str
    filename: str
    code: str
    description: str


@dataclass
class Fix:
    fix_id: str
    title: str
    description: str
    category: str
    priority: int  # 1=critical, 2=high, 3=medium, 4=low
    implementation_steps: List[str]
    code_snippets: List[CodeSnippet]
    estimated_time_minutes: int
    difficulty: str  # "easy", "medium", "hard"
    requires_developer: bool
    verification_steps: List[str]


@dataclass
class FixPlan:
    diagnosis: Diagnosis
    fixes: List[Fix]
    total_estimated_time_minutes: int
    can_implement_without_developer: bool
    warnings: List[str]


# ---------------------------------------------------------------------------
# Verification models
# ---------------------------------------------------------------------------

@dataclass
class StabilityResult:
    url: str
    duration_minutes: int
    checks_performed: int
    checks_passed: int
    all_stable: bool
    failures: List[Dict[str, Any]]


@dataclass
class AppealDoc:
    platform: Platform
    url: str
    original_issue: str
    fixes_applied: List[str]
    verification_summary: str
    test_evidence: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VerificationResult:
    url: str
    original_diagnosis: Diagnosis
    tests_passed: List[str]
    tests_failed: List[str]
    all_tests_passed: bool
    ready_for_appeal: bool
    new_test_results: TestResults
    stability_result: Optional[StabilityResult] = None
    appeal_doc: Optional[AppealDoc] = None


# ---------------------------------------------------------------------------
# Request / Config models
# ---------------------------------------------------------------------------

@dataclass
class UserRequest:
    url: str
    platform: str = "microsoft"
    description: Optional[str] = None
    editorial_code: Optional[str] = None


@dataclass
class TestConfig:
    timeout_seconds: int = 30
    max_redirects: int = 10
    user_agents: Dict[str, str] = field(default_factory=lambda: {
        "browser": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "googlebot": (
            "Mozilla/5.0 (compatible; Googlebot/2.1; "
            "+http://www.google.com/bot.html)"
        ),
        "bingbot": (
            "Mozilla/5.0 (compatible; bingbot/2.0; "
            "+http://www.bing.com/bingbot.htm)"
        ),
    })
    proxy_locations: List[str] = field(
        default_factory=lambda: ["us-east", "eu-west", "asia-southeast"]
    )
