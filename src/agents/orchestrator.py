"""Orchestrator Agent — coordinates the full diagnostic workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from src.models.data_models import (
    Diagnosis,
    FixPlan,
    TestResults,
    UserRequest,
    VerificationResult,
)
from src.agents.testing_agent import TestingAgent
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.fix_agent import FixAgent
from src.agents.verify_agent import VerificationAgent


@dataclass
class OrchestratorResponse:
    """Full response returned to the caller."""

    url: str
    platform: str
    test_results: TestResults
    diagnosis: Diagnosis
    fix_plan: FixPlan
    verification: Optional[VerificationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrchestratorAgent:
    """Top-level coordinator: Test → Diagnose → Fix → (optionally) Verify."""

    def __init__(
        self,
        testing_agent: Optional[TestingAgent] = None,
        diagnostic_agent: Optional[DiagnosticAgent] = None,
        fix_agent: Optional[FixAgent] = None,
        verify_agent: Optional[VerificationAgent] = None,
    ) -> None:
        self.testing_agent = testing_agent or TestingAgent()
        self.diagnostic_agent = diagnostic_agent or DiagnosticAgent()
        self.fix_agent = fix_agent or FixAgent()
        self.verify_agent = verify_agent or VerificationAgent(self.testing_agent)

    @classmethod
    def create(cls) -> "OrchestratorAgent":
        testing = TestingAgent()
        return cls(
            testing_agent=testing,
            diagnostic_agent=DiagnosticAgent(),
            fix_agent=FixAgent(),
            verify_agent=VerificationAgent(testing),
        )

    async def process_request(
        self,
        request: UserRequest,
        *,
        run_verification: bool = False,
    ) -> OrchestratorResponse:
        platform = request.platform

        # Step 1: Run diagnostic tests
        test_results = await self.testing_agent.run_full_diagnostic_suite(
            request.url, platform
        )

        # Step 2: Diagnose
        diagnosis = await self.diagnostic_agent.diagnose(test_results, platform)

        # Step 3: Generate fix plan
        context = {
            "editorial_code": request.editorial_code,
            "description": request.description,
        }
        fix_plan = await self.fix_agent.generate_fixes(diagnosis, context)

        # Step 4 (optional): Verification
        verification: Optional[VerificationResult] = None
        if run_verification:
            verification = await self.verify_agent.verify_fix(
                request.url, diagnosis, platform
            )

        return OrchestratorResponse(
            url=request.url,
            platform=platform,
            test_results=test_results,
            diagnosis=diagnosis,
            fix_plan=fix_plan,
            verification=verification,
        )

    async def diagnose_only(self, request: UserRequest) -> Diagnosis:
        test_results = await self.testing_agent.run_full_diagnostic_suite(
            request.url, request.platform
        )
        return await self.diagnostic_agent.diagnose(test_results, request.platform)

    async def verify_only(
        self, url: str, diagnosis: Diagnosis, platform: str = "microsoft"
    ) -> VerificationResult:
        return await self.verify_agent.verify_fix(url, diagnosis, platform)
