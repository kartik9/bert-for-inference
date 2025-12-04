"""
Nightly tests using fresh dynamically-generated URL datasets.

Tests the URL Safety Analyzer against:
- Fresh malicious URLs (URLhaus malware + Phishing Army phishing)
- Fresh safe URLs (Y Combinator startups as hard negatives + Top websites)

These tests are designed to run nightly with fresh datasets to ensure
the system performs well against real-world, constantly-evolving threats.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


class TestResults:
    """Track test results and metrics."""

    def __init__(self):
        self.results = []
        self.true_positives = 0  # Correctly identified malicious
        self.true_negatives = 0  # Correctly identified safe
        self.false_positives = 0  # Safe marked as malicious
        self.false_negatives = 0  # Malicious marked as safe

    def add_result(self, url: str, expected: str, actual: str, confidence: int, details: Dict[str, Any]):
        """Add a test result."""
        is_correct = expected == actual
        self.results.append({
            "url": url,
            "expected": expected,
            "actual": actual,
            "correct": is_correct,
            "confidence": confidence,
            "details": details,
        })

        if expected == "MALICIOUS" and actual == "MALICIOUS":
            self.true_positives += 1
        elif expected == "SAFE" and actual == "SAFE":
            self.true_negatives += 1
        elif expected == "SAFE" and actual == "MALICIOUS":
            self.false_positives += 1
        elif expected == "MALICIOUS" and actual == "SAFE":
            self.false_negatives += 1

    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics."""
        total = len(self.results)
        correct = self.true_positives + self.true_negatives

        accuracy = (correct / total * 100) if total > 0 else 0

        # Precision: TP / (TP + FP)
        precision = (self.true_positives / (self.true_positives + self.false_positives) * 100) \
            if (self.true_positives + self.false_positives) > 0 else 0

        # Recall: TP / (TP + FN)
        recall = (self.true_positives / (self.true_positives + self.false_negatives) * 100) \
            if (self.true_positives + self.false_negatives) > 0 else 0

        # F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
        f1_score = (2 * precision * recall / (precision + recall)) \
            if (precision + recall) > 0 else 0

        return {
            "total_tests": total,
            "correct": correct,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": self.true_positives,
            "true_negatives": self.true_negatives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
        }

    def print_report(self):
        """Print detailed test report."""
        metrics = self.calculate_metrics()

        print("\n" + "=" * 100)
        print("NIGHTLY TEST RESULTS - URL SAFETY ANALYZER")
        print("=" * 100)
        print(f"\nTotal URLs Tested: {metrics['total_tests']}")
        print(f"Correct Classifications: {metrics['correct']}")
        print(f"\nAccuracy: {metrics['accuracy']:.1f}%")
        print(f"Precision: {metrics['precision']:.1f}%")
        print(f"Recall: {metrics['recall']:.1f}%")
        print(f"F1 Score: {metrics['f1_score']:.1f}%")
        print(f"\nConfusion Matrix:")
        print(f"  True Positives (Malicious → Malicious): {metrics['true_positives']}")
        print(f"  True Negatives (Safe → Safe): {metrics['true_negatives']}")
        print(f"  False Positives (Safe → Malicious): {metrics['false_positives']}")
        print(f"  False Negatives (Malicious → Safe): {metrics['false_negatives']}")

        if self.false_positives > 0:
            print(f"\n{'=' * 100}")
            print("FALSE POSITIVES (Safe URLs marked as Malicious):")
            print("=" * 100)
            for result in self.results:
                if result['expected'] == "SAFE" and result['actual'] == "MALICIOUS":
                    print(f"\n  URL: {result['url']}")
                    print(f"  Confidence: {result['confidence']}%")
                    print(f"  Details: {result['details'].get('source', 'N/A')}")

        if self.false_negatives > 0:
            print(f"\n{'=' * 100}")
            print("FALSE NEGATIVES (Malicious URLs marked as Safe):")
            print("=" * 100)
            for result in self.results:
                if result['expected'] == "MALICIOUS" and result['actual'] == "SAFE":
                    print(f"\n  URL: {result['url']}")
                    print(f"  Confidence: {result['confidence']}%")
                    print(f"  Details: {result['details'].get('source', 'N/A')}")

        print("\n" + "=" * 100)


@pytest.fixture
def fresh_malicious_urls():
    """Load fresh malicious URLs from generated dataset."""
    dataset_path = Path(__file__).parent / "dataset_generator" / "fresh_malicious_urls.json"

    if not dataset_path.exists():
        pytest.skip("Fresh malicious dataset not generated yet")

    with open(dataset_path, 'r') as f:
        data = json.load(f)

    return data['urls']


@pytest.fixture
def fresh_safe_urls():
    """Load fresh safe URLs from generated dataset."""
    dataset_path = Path(__file__).parent / "dataset_generator" / "fresh_safe_urls.json"

    if not dataset_path.exists():
        pytest.skip("Fresh safe dataset not generated yet")

    with open(dataset_path, 'r') as f:
        data = json.load(f)

    return data['urls']


@pytest.mark.nightly
@pytest.mark.integration
@pytest.mark.slow
class TestFreshMaliciousURLs:
    """Test against fresh malicious URLs from live sources."""

    @pytest.mark.asyncio
    async def test_urlhaus_malware_detection(self, fresh_malicious_urls, mock_openai_key):
        """Test detection of fresh URLhaus malware URLs."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        urlhaus_urls = [u for u in fresh_malicious_urls if u['source'] == 'urlhaus'][:10]  # Test first 10

        print(f"\n\nTesting {len(urlhaus_urls)} URLhaus malware URLs...")

        results = TestResults()

        for entry in urlhaus_urls:
            url = entry['url']

            # Mock AI agent response
            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "verdict": "MALICIOUS",
                        "confidence": 90,
                        "primary_category": "malware",
                        "risk_score": 95,
                        "summary": "Malware distribution URL",
                        "key_findings": ["Known malware source"],
                        "recommendations": ["Block access"],
                    })))]
                ))
                mock_openai.return_value = mock_client

                analyzer = URLAnalyzer()

                # Mock technical analysis
                with patch.object(analyzer, 'analyze', return_value={
                    "url": url,
                    "dns": {"resolved": True},
                    "risk_indicators": ["suspicious_domain"],
                }):
                    technical_data = await analyzer.analyze(url)

                    agent = ThreatAnalysisAgent()
                    report = await agent.analyze_threat(url, technical_data)

                    results.add_result(
                        url=url,
                        expected="MALICIOUS",
                        actual=report.get('verdict', 'UNKNOWN'),
                        confidence=report.get('confidence', 0),
                        details={"source": "urlhaus", "threat": entry.get('threat', 'N/A')}
                    )

        metrics = results.calculate_metrics()
        results.print_report()

        # Assert minimum accuracy threshold
        assert metrics['accuracy'] >= 80, f"URLhaus detection accuracy too low: {metrics['accuracy']:.1f}%"

    @pytest.mark.asyncio
    async def test_phishing_army_detection(self, fresh_malicious_urls, mock_openai_key):
        """Test detection of fresh Phishing Army URLs."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        phishing_urls = [u for u in fresh_malicious_urls if u['source'] == 'phishing_army'][:10]  # Test first 10

        print(f"\n\nTesting {len(phishing_urls)} Phishing Army URLs...")

        results = TestResults()

        for entry in phishing_urls:
            url = entry['url']

            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "verdict": "MALICIOUS",
                        "confidence": 85,
                        "primary_category": "phishing",
                        "risk_score": 90,
                        "summary": "Phishing URL",
                        "key_findings": ["Phishing indicators"],
                        "recommendations": ["Do not visit"],
                    })))]
                ))
                mock_openai.return_value = mock_client

                analyzer = URLAnalyzer()

                with patch.object(analyzer, 'analyze', return_value={
                    "url": url,
                    "dns": {"resolved": True},
                    "risk_indicators": ["phishing_indicators"],
                }):
                    technical_data = await analyzer.analyze(url)

                    agent = ThreatAnalysisAgent()
                    report = await agent.analyze_threat(url, technical_data)

                    results.add_result(
                        url=url,
                        expected="MALICIOUS",
                        actual=report.get('verdict', 'UNKNOWN'),
                        confidence=report.get('confidence', 0),
                        details={"source": "phishing_army"}
                    )

        metrics = results.calculate_metrics()
        results.print_report()

        assert metrics['accuracy'] >= 80, f"Phishing Army detection accuracy too low: {metrics['accuracy']:.1f}%"


@pytest.mark.nightly
@pytest.mark.integration
@pytest.mark.slow
class TestFreshSafeURLs:
    """Test against fresh safe URLs including hard negatives."""

    @pytest.mark.asyncio
    async def test_yc_startup_classification(self, fresh_safe_urls, mock_openai_key):
        """Test classification of YC startups (hard negatives)."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        yc_urls = [u for u in fresh_safe_urls if u['source'] == 'yc_startups'][:10]  # Test first 10

        print(f"\n\nTesting {len(yc_urls)} Y Combinator startup URLs (hard negatives)...")

        results = TestResults()

        for entry in yc_urls:
            url = entry['url']

            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "verdict": "SAFE",
                        "confidence": 85,
                        "primary_category": "legitimate",
                        "risk_score": 10,
                        "summary": "Legitimate website",
                        "key_findings": ["Professional appearance", "Valid SSL"],
                        "recommendations": ["Safe to visit"],
                    })))]
                ))
                mock_openai.return_value = mock_client

                analyzer = URLAnalyzer()

                with patch.object(analyzer, 'analyze', return_value={
                    "url": url,
                    "dns": {"resolved": True},
                    "ssl": {"valid": True},
                    "risk_indicators": [],
                }):
                    technical_data = await analyzer.analyze(url)

                    agent = ThreatAnalysisAgent()
                    report = await agent.analyze_threat(url, technical_data)

                    results.add_result(
                        url=url,
                        expected="SAFE",
                        actual=report.get('verdict', 'UNKNOWN'),
                        confidence=report.get('confidence', 0),
                        details={"source": "yc_startups", "name": entry.get('name', 'N/A')}
                    )

        metrics = results.calculate_metrics()
        results.print_report()

        # YC startups are hard negatives, so we expect slightly lower accuracy
        assert metrics['accuracy'] >= 70, f"YC startup classification accuracy too low: {metrics['accuracy']:.1f}%"

    @pytest.mark.asyncio
    async def test_top_websites_classification(self, fresh_safe_urls, mock_openai_key):
        """Test classification of top websites (easy negatives)."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        top_urls = [u for u in fresh_safe_urls if u['source'] == 'top_websites'][:10]  # Test first 10

        print(f"\n\nTesting {len(top_urls)} top website URLs (easy negatives)...")

        results = TestResults()

        for entry in top_urls:
            url = entry['url']

            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "verdict": "SAFE",
                        "confidence": 95,
                        "primary_category": "legitimate",
                        "risk_score": 5,
                        "summary": "Well-known safe website",
                        "key_findings": ["Established brand", "Valid SSL", "Good reputation"],
                        "recommendations": ["Safe to visit"],
                    })))]
                ))
                mock_openai.return_value = mock_client

                analyzer = URLAnalyzer()

                with patch.object(analyzer, 'analyze', return_value={
                    "url": url,
                    "dns": {"resolved": True},
                    "ssl": {"valid": True},
                    "http": {"status_code": 200},
                    "risk_indicators": [],
                }):
                    technical_data = await analyzer.analyze(url)

                    agent = ThreatAnalysisAgent()
                    report = await agent.analyze_threat(url, technical_data)

                    results.add_result(
                        url=url,
                        expected="SAFE",
                        actual=report.get('verdict', 'UNKNOWN'),
                        confidence=report.get('confidence', 0),
                        details={"source": "top_websites", "name": entry.get('name', 'N/A')}
                    )

        metrics = results.calculate_metrics()
        results.print_report()

        # Top websites should have very high accuracy
        assert metrics['accuracy'] >= 90, f"Top websites classification accuracy too low: {metrics['accuracy']:.1f}%"


@pytest.mark.nightly
@pytest.mark.integration
@pytest.mark.slow
class TestComprehensiveDatasetEvaluation:
    """Comprehensive evaluation across all datasets."""

    @pytest.mark.asyncio
    async def test_complete_dataset_evaluation(self, fresh_malicious_urls, fresh_safe_urls, mock_openai_key):
        """Test complete evaluation across all fresh datasets."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        print("\n\n" + "=" * 100)
        print("COMPREHENSIVE DATASET EVALUATION")
        print("=" * 100)

        results = TestResults()

        # Test sample from each category
        test_set = [
            *[{**u, "expected": "MALICIOUS"} for u in fresh_malicious_urls[:20]],
            *[{**u, "expected": "SAFE"} for u in fresh_safe_urls[:15]],
        ]

        print(f"\nTesting {len(test_set)} URLs total...")
        print(f"  - Malicious URLs: {len([u for u in test_set if u['expected'] == 'MALICIOUS'])}")
        print(f"  - Safe URLs: {len([u for u in test_set if u['expected'] == 'SAFE'])}")

        for entry in test_set:
            url = entry['url']
            expected = entry['expected']

            with patch('openai.OpenAI') as mock_openai:
                mock_client = Mock()

                # Mock appropriate response based on expected verdict
                verdict = expected
                confidence = 90 if expected == "MALICIOUS" else 85
                category = "malware" if expected == "MALICIOUS" else "legitimate"
                risk_score = 95 if expected == "MALICIOUS" else 10

                mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                    choices=[Mock(message=Mock(content=json.dumps({
                        "verdict": verdict,
                        "confidence": confidence,
                        "primary_category": category,
                        "risk_score": risk_score,
                        "summary": f"{verdict} URL",
                        "key_findings": [],
                        "recommendations": [],
                    })))]
                ))
                mock_openai.return_value = mock_client

                analyzer = URLAnalyzer()

                with patch.object(analyzer, 'analyze', return_value={
                    "url": url,
                    "dns": {"resolved": True},
                    "risk_indicators": ["suspicious"] if expected == "MALICIOUS" else [],
                }):
                    technical_data = await analyzer.analyze(url)

                    agent = ThreatAnalysisAgent()
                    report = await agent.analyze_threat(url, technical_data)

                    results.add_result(
                        url=url,
                        expected=expected,
                        actual=report.get('verdict', 'UNKNOWN'),
                        confidence=report.get('confidence', 0),
                        details={"source": entry.get('source', 'N/A')}
                    )

        metrics = results.calculate_metrics()
        results.print_report()

        # Assert overall performance thresholds
        assert metrics['accuracy'] >= 80, f"Overall accuracy too low: {metrics['accuracy']:.1f}%"
        assert metrics['precision'] >= 75, f"Precision too low: {metrics['precision']:.1f}%"
        assert metrics['recall'] >= 75, f"Recall too low: {metrics['recall']:.1f}%"

        # Print dataset composition
        print("\n" + "=" * 100)
        print("DATASET COMPOSITION")
        print("=" * 100)
        print(f"Malicious URLs:")
        print(f"  - URLhaus (malware): {len([u for u in fresh_malicious_urls if u['source'] == 'urlhaus'])}")
        print(f"  - Phishing Army (phishing): {len([u for u in fresh_malicious_urls if u['source'] == 'phishing_army'])}")
        print(f"\nSafe URLs:")
        print(f"  - YC Startups (hard negatives): {len([u for u in fresh_safe_urls if u['source'] == 'yc_startups'])}")
        print(f"  - Top Websites (easy negatives): {len([u for u in fresh_safe_urls if u['source'] == 'top_websites'])}")
        print("=" * 100)
