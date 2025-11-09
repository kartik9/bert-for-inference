"""
Evaluation Framework for URL Safety Analysis Agent

Comprehensive testing and metrics collection including:
- Accuracy, Precision, Recall, F1 Score
- GPT token consumption by model and type
- Cost analysis
- Performance metrics (latency, throughput)
- Detailed reporting
"""

import json
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

from url_analyzer import URLAnalyzer
from ai_agent_with_metrics import SafetyAnalysisAgentWithMetrics
from token_metrics import TokenMetricsTracker

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Single test case for evaluation"""
    url: str
    ground_truth_label: str  # "SAFE", "SUSPICIOUS", "MALICIOUS", "MANUAL_REVIEW_REQUIRED"
    expected_category: Optional[str] = None  # "phishing", "malware", "scam", etc.
    description: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TestResult:
    """Result of a single test case"""
    test_case: TestCase
    predicted_label: str
    predicted_category: Optional[str]
    confidence: int
    risk_score: int
    correct: bool
    analysis_duration_seconds: float
    token_usage: Dict[str, Any]
    cost_usd: float
    full_report: Dict[str, Any]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.test_case.url,
            "ground_truth": self.test_case.ground_truth_label,
            "predicted": self.predicted_label,
            "predicted_category": self.predicted_category,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "correct": self.correct,
            "duration_seconds": self.analysis_duration_seconds,
            "token_usage": self.token_usage,
            "cost_usd": self.cost_usd,
            "error": self.error
        }


class EvaluationMetrics:
    """Calculate classification metrics"""

    def __init__(self, results: List[TestResult]):
        """
        Initialize with test results

        Args:
            results: List of TestResult objects
        """
        self.results = results
        self.labels = ["SAFE", "MANUAL_REVIEW_REQUIRED", "SUSPICIOUS", "MALICIOUS"]

    def calculate_accuracy(self) -> float:
        """Calculate overall accuracy"""
        if not self.results:
            return 0.0

        correct = sum(1 for r in self.results if r.correct)
        return correct / len(self.results)

    def calculate_precision_recall_f1(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate precision, recall, and F1 for each label

        Returns:
            Dict mapping label to {precision, recall, f1}
        """
        metrics = {}

        for label in self.labels:
            # True positives: predicted and ground truth both match label
            tp = sum(1 for r in self.results
                    if r.predicted_label == label and r.test_case.ground_truth_label == label)

            # False positives: predicted label but ground truth different
            fp = sum(1 for r in self.results
                    if r.predicted_label == label and r.test_case.ground_truth_label != label)

            # False negatives: ground truth is label but predicted different
            fn = sum(1 for r in self.results
                    if r.predicted_label != label and r.test_case.ground_truth_label == label)

            # Calculate metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            metrics[label] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn
            }

        return metrics

    def calculate_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate confusion matrix

        Returns:
            Dict[actual_label][predicted_label] = count
        """
        matrix = defaultdict(lambda: defaultdict(int))

        for result in self.results:
            actual = result.test_case.ground_truth_label
            predicted = result.predicted_label
            matrix[actual][predicted] += 1

        return dict(matrix)

    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        durations = [r.analysis_duration_seconds for r in self.results if r.error is None]

        if not durations:
            return {
                "avg_duration": 0.0,
                "min_duration": 0.0,
                "max_duration": 0.0,
                "total_duration": 0.0
            }

        return {
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
            "p50_duration": sorted(durations)[len(durations) // 2],
            "p95_duration": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
        }

    def get_token_stats(self) -> Dict[str, Any]:
        """Aggregate token usage statistics"""
        total_tokens = 0
        total_cost = 0.0
        model_breakdown = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "calls": 0})
        token_type_breakdown = {"text": 0, "image": 0}

        for result in self.results:
            if result.error:
                continue

            token_usage = result.token_usage
            total_tokens += token_usage.get("total_tokens", 0)
            total_cost += result.cost_usd

            # Aggregate by model
            for model, metrics in token_usage.get("model_breakdown", {}).items():
                model_breakdown[model]["tokens"] += metrics.get("total_tokens", 0)
                model_breakdown[model]["cost"] += metrics.get("estimated_cost_usd", 0.0)
                model_breakdown[model]["calls"] += metrics.get("call_count", 0)

            # Token type breakdown
            tb = token_usage.get("token_breakdown", {})
            token_type_breakdown["text"] += tb.get("text_tokens", 0)
            token_type_breakdown["image"] += tb.get("image_tokens", 0)

        return {
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_tokens_per_url": total_tokens / len(self.results) if self.results else 0,
            "avg_cost_per_url": total_cost / len(self.results) if self.results else 0,
            "model_breakdown": dict(model_breakdown),
            "token_type_breakdown": token_type_breakdown,
            "text_percentage": (token_type_breakdown["text"] / total_tokens * 100) if total_tokens > 0 else 0,
            "image_percentage": (token_type_breakdown["image"] / total_tokens * 100) if total_tokens > 0 else 0
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "accuracy": self.calculate_accuracy(),
            "precision_recall_f1": self.calculate_precision_recall_f1(),
            "confusion_matrix": self.calculate_confusion_matrix(),
            "performance": self.get_performance_stats(),
            "token_usage": self.get_token_stats(),
            "total_tests": len(self.results),
            "successful_tests": sum(1 for r in self.results if r.error is None),
            "failed_tests": sum(1 for r in self.results if r.error is not None)
        }


class EvaluationFramework:
    """
    Comprehensive evaluation framework for URL safety analysis

    Features:
    - Load test datasets with ground truth
    - Run batch evaluations
    - Collect metrics (accuracy, tokens, cost, performance)
    - Generate detailed reports
    """

    def __init__(self, url_analyzer: Optional[URLAnalyzer] = None):
        """
        Initialize evaluation framework

        Args:
            url_analyzer: Optional URLAnalyzer instance (creates new if None)
        """
        self.url_analyzer = url_analyzer or URLAnalyzer()
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self.metrics_tracker = TokenMetricsTracker()

    def load_test_dataset(self, filepath: str):
        """
        Load test dataset from JSON file

        Expected format:
        {
            "test_cases": [
                {
                    "url": "https://example.com",
                    "ground_truth_label": "SAFE",
                    "expected_category": "legitimate",
                    "description": "Test description",
                    "metadata": {}
                },
                ...
            ]
        }

        Args:
            filepath: Path to JSON test dataset file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        test_cases_data = data.get("test_cases", [])

        for tc in test_cases_data:
            test_case = TestCase(
                url=tc["url"],
                ground_truth_label=tc["ground_truth_label"],
                expected_category=tc.get("expected_category"),
                description=tc.get("description", ""),
                metadata=tc.get("metadata", {})
            )
            self.test_cases.append(test_case)

        logger.info(f"Loaded {len(self.test_cases)} test cases from {filepath}")

    def add_test_case(
        self,
        url: str,
        ground_truth_label: str,
        expected_category: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Manually add a test case

        Args:
            url: URL to test
            ground_truth_label: Expected verdict
            expected_category: Expected threat category
            description: Test case description
            metadata: Additional metadata
        """
        test_case = TestCase(
            url=url,
            ground_truth_label=ground_truth_label,
            expected_category=expected_category,
            description=description,
            metadata=metadata or {}
        )
        self.test_cases.append(test_case)

    async def run_evaluation(
        self,
        max_concurrent: int = 5,
        deep_analysis: bool = True,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run evaluation on all test cases

        Args:
            max_concurrent: Maximum number of concurrent analyses
            deep_analysis: Enable deep AI analysis
            max_iterations: Maximum investigation iterations

        Returns:
            Comprehensive evaluation metrics
        """
        logger.info(f"Starting evaluation with {len(self.test_cases)} test cases")
        logger.info(f"Max concurrent: {max_concurrent}, Deep analysis: {deep_analysis}")

        self.results = []
        self.metrics_tracker.reset()

        # Create AI agent with metrics tracking
        ai_agent = SafetyAnalysisAgentWithMetrics(metrics_tracker=self.metrics_tracker)

        # Run evaluations with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_single_test(test_case: TestCase) -> TestResult:
            async with semaphore:
                return await self._evaluate_single_url(
                    test_case,
                    ai_agent,
                    deep_analysis,
                    max_iterations
                )

        # Execute all tests
        tasks = [run_single_test(tc) for tc in self.test_cases]
        self.results = await asyncio.gather(*tasks, return_exceptions=False)

        # Calculate metrics
        metrics_calculator = EvaluationMetrics(self.results)
        summary = metrics_calculator.get_summary()

        logger.info(f"Evaluation complete. Accuracy: {summary['accuracy']:.2%}")

        return summary

    async def _evaluate_single_url(
        self,
        test_case: TestCase,
        ai_agent: SafetyAnalysisAgentWithMetrics,
        deep_analysis: bool,
        max_iterations: int
    ) -> TestResult:
        """
        Evaluate a single URL

        Args:
            test_case: Test case to evaluate
            ai_agent: AI agent with metrics tracking
            deep_analysis: Enable deep analysis
            max_iterations: Max investigation iterations

        Returns:
            TestResult object
        """
        start_time = time.time()
        error_msg = None
        report = {}

        try:
            logger.info(f"Testing: {test_case.url}")

            # Set investigation ID for tracking
            investigation_id = f"eval_{test_case.url}_{int(start_time)}"
            ai_agent.metrics_tracker.set_investigation_id(investigation_id)

            # Phase 1: Technical analysis
            technical_data = await self.url_analyzer.analyze(test_case.url)

            if deep_analysis and ai_agent.is_configured():
                # Phase 2: Create investigation plan
                plan = await ai_agent.create_investigation_plan(test_case.url, technical_data)

                # Phase 3: Iterative investigation (consume generator)
                async for update in ai_agent.investigate_url_iterative(
                    test_case.url,
                    technical_data,
                    plan,
                    url_analyzer_instance=self.url_analyzer,
                    max_iterations=max_iterations
                ):
                    # Just consume the generator, don't need to process updates
                    pass

                # Phase 4: Generate report
                report = await ai_agent.generate_report(test_case.url, technical_data)
            else:
                # Fallback report without AI
                report = ai_agent._generate_fallback_report(test_case.url, technical_data)

        except Exception as e:
            logger.error(f"Error evaluating {test_case.url}: {str(e)}")
            error_msg = str(e)
            report = {
                "verdict": "ERROR",
                "confidence": 0,
                "risk_score": 0,
                "primary_category": "unknown"
            }

        duration = time.time() - start_time

        # Extract predictions
        predicted_label = report.get("verdict", "ERROR")
        predicted_category = report.get("primary_category")
        confidence = report.get("confidence", 0)
        risk_score = report.get("risk_score", 0)

        # Check correctness
        correct = (predicted_label == test_case.ground_truth_label)

        # Get token usage for this test
        token_usage = ai_agent.get_metrics_summary()
        cost = token_usage.get("total_cost_usd", 0.0)

        result = TestResult(
            test_case=test_case,
            predicted_label=predicted_label,
            predicted_category=predicted_category,
            confidence=confidence,
            risk_score=risk_score,
            correct=correct,
            analysis_duration_seconds=duration,
            token_usage=token_usage,
            cost_usd=cost,
            full_report=report,
            error=error_msg
        )

        logger.info(
            f"Completed: {test_case.url} | "
            f"Ground truth: {test_case.ground_truth_label} | "
            f"Predicted: {predicted_label} | "
            f"Correct: {correct} | "
            f"Duration: {duration:.1f}s | "
            f"Cost: ${cost:.4f}"
        )

        return result

    def export_results(self, output_dir: str):
        """
        Export detailed results and reports

        Creates:
        - evaluation_summary.json: High-level metrics
        - detailed_results.json: Per-URL results
        - token_metrics.json: Detailed token consumption
        - confusion_matrix.txt: Human-readable confusion matrix

        Args:
            output_dir: Directory to save results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Calculate metrics
        metrics_calculator = EvaluationMetrics(self.results)
        summary = metrics_calculator.get_summary()

        # Save summary
        summary_file = output_path / "evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Saved summary to {summary_file}")

        # Save detailed results
        detailed_file = output_path / "detailed_results.json"
        detailed_results = {
            "evaluation_date": datetime.utcnow().isoformat(),
            "total_tests": len(self.results),
            "results": [r.to_dict() for r in self.results]
        }

        with open(detailed_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)

        logger.info(f"Saved detailed results to {detailed_file}")

        # Save token metrics
        token_file = output_path / "token_metrics.json"
        self.metrics_tracker.export_to_json(str(token_file))

        logger.info(f"Saved token metrics to {token_file}")

        # Save confusion matrix (human-readable)
        cm_file = output_path / "confusion_matrix.txt"
        self._save_confusion_matrix(summary["confusion_matrix"], cm_file)

        logger.info(f"Saved confusion matrix to {cm_file}")

        # Generate HTML report
        html_file = output_path / "evaluation_report.html"
        self._generate_html_report(summary, html_file)

        logger.info(f"Saved HTML report to {html_file}")

    def _save_confusion_matrix(self, matrix: Dict[str, Dict[str, int]], filepath: Path):
        """Save confusion matrix as formatted text"""
        labels = ["SAFE", "MANUAL_REVIEW_REQUIRED", "SUSPICIOUS", "MALICIOUS"]

        with open(filepath, 'w') as f:
            f.write("CONFUSION MATRIX\n")
            f.write("="*80 + "\n\n")
            f.write("Rows: Actual Labels\n")
            f.write("Columns: Predicted Labels\n\n")

            # Header
            f.write(f"{'Actual/Predicted':<25}")
            for label in labels:
                f.write(f"{label:<20}")
            f.write("\n" + "-"*105 + "\n")

            # Rows
            for actual in labels:
                f.write(f"{actual:<25}")
                for predicted in labels:
                    count = matrix.get(actual, {}).get(predicted, 0)
                    f.write(f"{count:<20}")
                f.write("\n")

    def _generate_html_report(self, summary: Dict[str, Any], filepath: Path):
        """Generate HTML evaluation report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>URL Safety Analysis Evaluation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric {{ display: inline-block; margin: 15px 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 24px; color: #4CAF50; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .timestamp {{ color: #999; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>URL Safety Analysis - Evaluation Report</h1>
        <p class="timestamp">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

        <h2>Overall Performance</h2>
        <div class="metric">
            <div class="metric-label">Accuracy</div>
            <div class="metric-value">{summary['accuracy']:.2%}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Tests</div>
            <div class="metric-value">{summary['total_tests']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Successful</div>
            <div class="metric-value">{summary['successful_tests']}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Failed</div>
            <div class="metric-value">{summary['failed_tests']}</div>
        </div>

        <h2>Classification Metrics</h2>
        <table>
            <tr>
                <th>Label</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1 Score</th>
                <th>True Positives</th>
                <th>False Positives</th>
                <th>False Negatives</th>
            </tr>
"""

        for label, metrics in summary['precision_recall_f1'].items():
            html += f"""
            <tr>
                <td><b>{label}</b></td>
                <td>{metrics['precision']:.2%}</td>
                <td>{metrics['recall']:.2%}</td>
                <td>{metrics['f1']:.2%}</td>
                <td>{metrics['true_positives']}</td>
                <td>{metrics['false_positives']}</td>
                <td>{metrics['false_negatives']}</td>
            </tr>
"""

        perf = summary['performance']
        token_usage = summary['token_usage']

        html += f"""
        </table>

        <h2>Performance Metrics</h2>
        <div class="metric">
            <div class="metric-label">Average Duration</div>
            <div class="metric-value">{perf['avg_duration']:.1f}s</div>
        </div>
        <div class="metric">
            <div class="metric-label">Min Duration</div>
            <div class="metric-value">{perf['min_duration']:.1f}s</div>
        </div>
        <div class="metric">
            <div class="metric-label">Max Duration</div>
            <div class="metric-value">{perf['max_duration']:.1f}s</div>
        </div>
        <div class="metric">
            <div class="metric-label">P95 Duration</div>
            <div class="metric-value">{perf.get('p95_duration', 0):.1f}s</div>
        </div>

        <h2>Token Consumption & Cost</h2>
        <div class="metric">
            <div class="metric-label">Total Tokens</div>
            <div class="metric-value">{token_usage['total_tokens']:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Cost</div>
            <div class="metric-value">${token_usage['total_cost_usd']:.4f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Avg Tokens/URL</div>
            <div class="metric-value">{token_usage['avg_tokens_per_url']:.0f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Avg Cost/URL</div>
            <div class="metric-value">${token_usage['avg_cost_per_url']:.4f}</div>
        </div>

        <h2>Token Type Breakdown</h2>
        <table>
            <tr>
                <th>Token Type</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            <tr>
                <td>Text Tokens</td>
                <td>{token_usage['token_type_breakdown']['text']:,}</td>
                <td>{token_usage['text_percentage']:.1f}%</td>
            </tr>
            <tr>
                <td>Image Tokens</td>
                <td>{token_usage['token_type_breakdown']['image']:,}</td>
                <td>{token_usage['image_percentage']:.1f}%</td>
            </tr>
        </table>

        <h2>Model Breakdown</h2>
        <table>
            <tr>
                <th>Model</th>
                <th>API Calls</th>
                <th>Total Tokens</th>
                <th>Total Cost</th>
            </tr>
"""

        for model, model_data in token_usage['model_breakdown'].items():
            html += f"""
            <tr>
                <td><b>{model}</b></td>
                <td>{model_data['calls']}</td>
                <td>{model_data['tokens']:,}</td>
                <td>${model_data['cost']:.4f}</td>
            </tr>
"""

        html += """
        </table>
    </div>
</body>
</html>
"""

        with open(filepath, 'w') as f:
            f.write(html)

    def print_summary(self):
        """Print human-readable summary to console"""
        metrics_calculator = EvaluationMetrics(self.results)
        summary = metrics_calculator.get_summary()

        print("\n" + "="*80)
        print("EVALUATION SUMMARY")
        print("="*80)

        print(f"\nTotal Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"\nOverall Accuracy: {summary['accuracy']:.2%}")

        print("\n" + "-"*80)
        print("CLASSIFICATION METRICS")
        print("-"*80)
        print(f"{'Label':<25}{'Precision':<15}{'Recall':<15}{'F1 Score':<15}")
        print("-"*80)

        for label, metrics in summary['precision_recall_f1'].items():
            print(f"{label:<25}{metrics['precision']:<15.2%}{metrics['recall']:<15.2%}{metrics['f1']:<15.2%}")

        print("\n" + "-"*80)
        print("PERFORMANCE METRICS")
        print("-"*80)
        perf = summary['performance']
        print(f"Average Duration: {perf['avg_duration']:.2f}s")
        print(f"Min Duration: {perf['min_duration']:.2f}s")
        print(f"Max Duration: {perf['max_duration']:.2f}s")
        print(f"P95 Duration: {perf.get('p95_duration', 0):.2f}s")

        print("\n" + "-"*80)
        print("TOKEN CONSUMPTION & COST")
        print("-"*80)
        token_usage = summary['token_usage']
        print(f"Total Tokens: {token_usage['total_tokens']:,}")
        print(f"Total Cost: ${token_usage['total_cost_usd']:.4f}")
        print(f"Avg Tokens/URL: {token_usage['avg_tokens_per_url']:.0f}")
        print(f"Avg Cost/URL: ${token_usage['avg_cost_per_url']:.4f}")
        print(f"\nText Tokens: {token_usage['token_type_breakdown']['text']:,} ({token_usage['text_percentage']:.1f}%)")
        print(f"Image Tokens: {token_usage['token_type_breakdown']['image']:,} ({token_usage['image_percentage']:.1f}%)")

        print("\n" + "-"*80)
        print("MODEL BREAKDOWN")
        print("-"*80)
        for model, model_data in token_usage['model_breakdown'].items():
            print(f"\n{model}:")
            print(f"  Calls: {model_data['calls']}")
            print(f"  Tokens: {model_data['tokens']:,}")
            print(f"  Cost: ${model_data['cost']:.4f}")

        print("\n" + "="*80 + "\n")
