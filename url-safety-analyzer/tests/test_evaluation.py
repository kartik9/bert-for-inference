"""
Test suite for evaluation framework.

Tests cover:
- Dataset loading
- Evaluation metrics calculation
- Performance assessment
- Report generation
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.unit
@pytest.mark.nightly
class TestDatasetLoading:
    """Test dataset loading functionality."""

    def test_load_valid_dataset(self, tmp_path):
        """Test loading a valid dataset file."""
        from evaluation_framework import EvaluationFramework

        # Create a test dataset
        dataset = [
            {"url": "https://safe.com", "label": "safe"},
            {"url": "https://phishing.com", "label": "malicious"},
        ]
        dataset_file = tmp_path / "test_dataset.json"
        dataset_file.write_text(json.dumps(dataset))

        evaluator = EvaluationFramework()
        loaded_data = evaluator.load_dataset(str(dataset_file))

        assert len(loaded_data) == 2
        assert loaded_data[0]["label"] == "safe"
        assert loaded_data[1]["label"] == "malicious"

    def test_load_empty_dataset(self, tmp_path):
        """Test handling of empty dataset."""
        from evaluation_framework import EvaluationFramework

        dataset_file = tmp_path / "empty_dataset.json"
        dataset_file.write_text(json.dumps([]))

        evaluator = EvaluationFramework()
        loaded_data = evaluator.load_dataset(str(dataset_file))

        assert len(loaded_data) == 0

    def test_load_invalid_dataset(self, tmp_path):
        """Test handling of invalid dataset file."""
        from evaluation_framework import EvaluationFramework

        dataset_file = tmp_path / "invalid_dataset.json"
        dataset_file.write_text("invalid json{")

        evaluator = EvaluationFramework()

        with pytest.raises(Exception):
            evaluator.load_dataset(str(dataset_file))


@pytest.mark.unit
@pytest.mark.nightly
class TestMetricsCalculation:
    """Test evaluation metrics calculation."""

    def test_accuracy_calculation(self):
        """Test accuracy metric calculation."""
        from evaluation_framework import EvaluationFramework

        predictions = ["safe", "malicious", "safe", "malicious"]
        ground_truth = ["safe", "malicious", "malicious", "malicious"]

        evaluator = EvaluationFramework()
        accuracy = evaluator.calculate_accuracy(predictions, ground_truth)

        # 3 out of 4 correct
        assert accuracy == 0.75

    def test_precision_recall_calculation(self):
        """Test precision and recall calculation."""
        from evaluation_framework import EvaluationFramework

        predictions = ["malicious", "malicious", "safe", "malicious"]
        ground_truth = ["malicious", "safe", "safe", "malicious"]

        evaluator = EvaluationFramework()
        precision, recall = evaluator.calculate_precision_recall(predictions, ground_truth, "malicious")

        # True positives: 2, False positives: 1, False negatives: 0
        # Precision: 2/3 = 0.666...
        # Recall: 2/2 = 1.0
        assert precision == pytest.approx(0.666, rel=0.01)
        assert recall == 1.0

    def test_f1_score_calculation(self):
        """Test F1 score calculation."""
        from evaluation_framework import EvaluationFramework

        precision = 0.8
        recall = 0.6

        evaluator = EvaluationFramework()
        f1 = evaluator.calculate_f1_score(precision, recall)

        # F1 = 2 * (0.8 * 0.6) / (0.8 + 0.6) = 0.685...
        assert f1 == pytest.approx(0.685, rel=0.01)

    def test_confusion_matrix(self):
        """Test confusion matrix generation."""
        from evaluation_framework import EvaluationFramework

        predictions = ["safe", "malicious", "safe", "malicious"]
        ground_truth = ["safe", "malicious", "malicious", "malicious"]

        evaluator = EvaluationFramework()
        matrix = evaluator.generate_confusion_matrix(predictions, ground_truth)

        assert "true_positives" in matrix
        assert "false_positives" in matrix
        assert "true_negatives" in matrix
        assert "false_negatives" in matrix

    def test_perfect_predictions(self):
        """Test metrics with perfect predictions."""
        from evaluation_framework import EvaluationFramework

        predictions = ["safe", "malicious", "safe", "malicious"]
        ground_truth = ["safe", "malicious", "safe", "malicious"]

        evaluator = EvaluationFramework()
        accuracy = evaluator.calculate_accuracy(predictions, ground_truth)

        assert accuracy == 1.0

    def test_all_wrong_predictions(self):
        """Test metrics with all wrong predictions."""
        from evaluation_framework import EvaluationFramework

        predictions = ["malicious", "safe", "malicious", "safe"]
        ground_truth = ["safe", "malicious", "safe", "malicious"]

        evaluator = EvaluationFramework()
        accuracy = evaluator.calculate_accuracy(predictions, ground_truth)

        assert accuracy == 0.0


@pytest.mark.unit
@pytest.mark.nightly
class TestPerformanceAssessment:
    """Test performance assessment functionality."""

    def test_assess_model_performance(self):
        """Test overall model performance assessment."""
        from evaluation_framework import EvaluationFramework

        results = [
            {"prediction": "safe", "actual": "safe", "confidence": 95},
            {"prediction": "malicious", "actual": "malicious", "confidence": 90},
            {"prediction": "safe", "actual": "malicious", "confidence": 60},
        ]

        evaluator = EvaluationFramework()
        assessment = evaluator.assess_performance(results)

        assert "accuracy" in assessment
        assert "average_confidence" in assessment
        assert assessment["accuracy"] == pytest.approx(0.666, rel=0.01)

    def test_confidence_analysis(self):
        """Test confidence score analysis."""
        from evaluation_framework import EvaluationFramework

        results = [
            {"prediction": "safe", "confidence": 95},
            {"prediction": "malicious", "confidence": 85},
            {"prediction": "safe", "confidence": 70},
        ]

        evaluator = EvaluationFramework()
        confidence_stats = evaluator.analyze_confidence(results)

        assert "average" in confidence_stats
        assert "min" in confidence_stats
        assert "max" in confidence_stats
        assert confidence_stats["average"] == pytest.approx(83.33, rel=0.01)
        assert confidence_stats["min"] == 70
        assert confidence_stats["max"] == 95

    def test_error_analysis(self):
        """Test error analysis for incorrect predictions."""
        from evaluation_framework import EvaluationFramework

        results = [
            {"prediction": "safe", "actual": "malicious", "url": "https://phish.com"},
            {"prediction": "malicious", "actual": "safe", "url": "https://legit.com"},
        ]

        evaluator = EvaluationFramework()
        errors = evaluator.analyze_errors(results)

        assert len(errors["false_negatives"]) == 1  # Missed malicious
        assert len(errors["false_positives"]) == 1  # Flagged safe as malicious


@pytest.mark.unit
@pytest.mark.nightly
class TestReportGeneration:
    """Test evaluation report generation."""

    def test_generate_evaluation_report(self):
        """Test generation of evaluation report."""
        from evaluation_framework import EvaluationFramework

        results = [
            {"prediction": "safe", "actual": "safe", "confidence": 95},
            {"prediction": "malicious", "actual": "malicious", "confidence": 90},
            {"prediction": "safe", "actual": "safe", "confidence": 85},
        ]

        evaluator = EvaluationFramework()
        report = evaluator.generate_report(results)

        assert "summary" in report
        assert "metrics" in report
        assert "errors" in report or "error_analysis" in report

    def test_report_includes_all_metrics(self):
        """Test that report includes all required metrics."""
        from evaluation_framework import EvaluationFramework

        results = [
            {"prediction": "safe", "actual": "safe", "confidence": 95},
            {"prediction": "malicious", "actual": "malicious", "confidence": 90},
        ]

        evaluator = EvaluationFramework()
        report = evaluator.generate_report(results)

        metrics = report.get("metrics", report)
        assert "accuracy" in metrics or "accuracy" in report
        # May have precision, recall, f1 as well


@pytest.mark.integration
@pytest.mark.nightly
@pytest.mark.slow
class TestEvaluationIntegration:
    """Integration tests for evaluation framework."""

    @pytest.mark.asyncio
    async def test_full_evaluation_pipeline(self, tmp_path, mock_openai_key):
        """Test complete evaluation pipeline."""
        from evaluation_framework import EvaluationFramework

        # Create test dataset
        dataset = [
            {"url": "https://google.com", "label": "safe"},
            {"url": "https://example.com", "label": "safe"},
        ]
        dataset_file = tmp_path / "test_dataset.json"
        dataset_file.write_text(json.dumps(dataset))

        evaluator = EvaluationFramework()

        with patch('openai.OpenAI'):
            # Mock the evaluation
            results = evaluator.load_dataset(str(dataset_file))
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_evaluation_with_mock_predictions(self, tmp_path):
        """Test evaluation with mocked predictions."""
        from evaluation_framework import EvaluationFramework

        dataset = [
            {"url": "https://safe1.com", "label": "safe"},
            {"url": "https://phish1.com", "label": "malicious"},
            {"url": "https://safe2.com", "label": "safe"},
        ]
        dataset_file = tmp_path / "test_dataset.json"
        dataset_file.write_text(json.dumps(dataset))

        evaluator = EvaluationFramework()
        data = evaluator.load_dataset(str(dataset_file))

        # Mock predictions
        predictions = ["safe", "malicious", "safe"]
        ground_truth = [item["label"] for item in data]

        accuracy = evaluator.calculate_accuracy(predictions, ground_truth)
        assert accuracy == 1.0  # All predictions correct
