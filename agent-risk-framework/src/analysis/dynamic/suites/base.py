from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
import time

class TestResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"
    SKIPPED = "skipped"

class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TestCaseResult(BaseModel):
    test_id: str
    test_name: str
    category: str
    result: TestResult
    severity: Severity
    details: str
    evidence: Optional[str] = None
    payload_used: Optional[str] = None
    response_received: Optional[str] = None
    execution_time_ms: int

class TestSuiteResult(BaseModel):
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    pass_rate: float
    critical_findings: List[TestCaseResult]
    high_findings: List[TestCaseResult]
    all_results: List[TestCaseResult]
    execution_time_ms: int

class BaseTestSuite(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self):
        self.test_cases: List[Dict[str, Any]] = []

    @abstractmethod
    async def load_test_cases(self) -> None:
        """Load test cases from JSON files"""
        pass

    @abstractmethod
    async def execute_test(self, agent_session, test_case: Dict) -> TestCaseResult:
        """Execute a single test case against the agent"""
        pass

    async def run(self, agent_session) -> TestSuiteResult:
        """Run all test cases"""
        await self.load_test_cases()

        results: List[TestCaseResult] = []
        start_time = time.time()

        for test_case in self.test_cases:
            try:
                result = await self.execute_test(agent_session, test_case)
                results.append(result)
            except Exception as e:
                results.append(TestCaseResult(
                    test_id=test_case.get('id', 'unknown'),
                    test_name=test_case.get('name', 'unknown'),
                    category=self.name,
                    result=TestResult.ERROR,
                    severity=Severity.HIGH,
                    details=f"Execution error: {str(e)}",
                    execution_time_ms=0
                ))

        return self._aggregate_results(results, int((time.time() - start_time) * 1000))

    def _aggregate_results(self, results: List[TestCaseResult], total_time: int) -> TestSuiteResult:
        passed = sum(1 for r in results if r.result == TestResult.PASS)
        failed = sum(1 for r in results if r.result == TestResult.FAIL)
        errors = sum(1 for r in results if r.result == TestResult.ERROR)

        return TestSuiteResult(
            suite_name=self.name,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            pass_rate=passed / len(results) if results else 0,
            critical_findings=[r for r in results if r.severity == Severity.CRITICAL and r.result == TestResult.FAIL],
            high_findings=[r for r in results if r.severity == Severity.HIGH and r.result == TestResult.FAIL],
            all_results=results,
            execution_time_ms=total_time
        )
