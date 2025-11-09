# Evaluation Framework Guide

## Overview

Comprehensive evaluation framework for the URL Safety Analysis Agent with detailed metrics collection including:

- **Classification Metrics**: Accuracy, Precision, Recall, F1 Score
- **GPT Token Consumption**: Breakdown by model and token type (text vs image)
- **Cost Analysis**: Estimated costs per URL and total
- **Performance Metrics**: Latency, throughput, P95 percentiles
- **Detailed Reporting**: JSON, HTML, and text formats

---

## Quick Start

### 1. Basic Evaluation Run

```bash
cd url-safety-analyzer/backend

# Run evaluation with example dataset
python run_evaluation.py \
    --dataset ../test_datasets/example_test_dataset.json \
    --output ./evaluation_results \
    --max-concurrent 5 \
    --max-iterations 3
```

### 2. Quick Test (3 Sample URLs)

```bash
# Fast test with 3 URLs for testing the framework
python run_evaluation.py --quick-test
```

### 3. Production Evaluation (Comprehensive)

```bash
# Full evaluation with verbose logging
python run_evaluation.py \
    --dataset ../test_datasets/production_test_set.json \
    --output ./eval_results_production \
    --max-concurrent 10 \
    --max-iterations 3 \
    --verbose
```

---

## Test Dataset Format

### JSON Structure

Create test datasets in JSON format:

```json
{
  "dataset_name": "My Test Dataset",
  "version": "1.0",
  "description": "Dataset description",
  "test_cases": [
    {
      "url": "https://example.com",
      "ground_truth_label": "SAFE|SUSPICIOUS|MALICIOUS|MANUAL_REVIEW_REQUIRED",
      "expected_category": "phishing|malware|scam|fraud|legitimate|unknown",
      "description": "Test case description",
      "metadata": {
        "source": "phishtank|manual|synthetic",
        "threat_indicators": ["indicator1", "indicator2"]
      }
    }
  ]
}
```

### Ground Truth Labels

Use these standardized labels:

- **`SAFE`**: Legitimate, no threats detected
- **`MANUAL_REVIEW_REQUIRED`**: Insufficient evidence, needs human review
- **`SUSPICIOUS`**: Concerning patterns, likely threat
- **`MALICIOUS`**: High confidence threat (phishing, malware, scam)

### Expected Categories

Common threat categories:

- `legitimate` - Verified safe sites
- `phishing` - Credential harvesting
- `malware` - Malicious software distribution
- `scam` - Fraud operations
- `fraud` - Financial deception
- `unknown` - Ambiguous cases

---

## Programmatic Usage

### Python API

```python
import asyncio
from evaluation_framework import EvaluationFramework
from url_analyzer import URLAnalyzer

async def run_custom_evaluation():
    # Initialize framework
    url_analyzer = URLAnalyzer()
    framework = EvaluationFramework(url_analyzer=url_analyzer)

    # Option 1: Load from JSON file
    framework.load_test_dataset("test_dataset.json")

    # Option 2: Add test cases programmatically
    framework.add_test_case(
        url="https://example.com",
        ground_truth_label="SAFE",
        expected_category="legitimate",
        description="Test description"
    )

    # Run evaluation
    summary = await framework.run_evaluation(
        max_concurrent=5,
        deep_analysis=True,
        max_iterations=3
    )

    # Print results
    framework.print_summary()

    # Export results
    framework.export_results("./my_eval_results")

    return summary

# Run
asyncio.run(run_custom_evaluation())
```

---

## Output Files

After evaluation, the following files are generated:

### 1. `evaluation_summary.json`

High-level metrics in JSON format:

```json
{
  "accuracy": 0.92,
  "precision_recall_f1": {
    "SAFE": {
      "precision": 0.95,
      "recall": 0.90,
      "f1": 0.92,
      "true_positives": 18,
      "false_positives": 1,
      "false_negatives": 2
    },
    "MALICIOUS": { "..." }
  },
  "token_usage": {
    "total_tokens": 45000,
    "total_cost_usd": 0.52,
    "avg_tokens_per_url": 3750,
    "model_breakdown": {
      "gpt-5": {
        "calls": 60,
        "tokens": 38000,
        "cost": 0.45
      },
      "gpt-4o-mini": {
        "calls": 20,
        "tokens": 7000,
        "cost": 0.07
      }
    },
    "token_type_breakdown": {
      "text": 43500,
      "image": 1500
    }
  },
  "performance": {
    "avg_duration": 35.2,
    "p95_duration": 58.3
  }
}
```

### 2. `detailed_results.json`

Per-URL analysis results:

```json
{
  "evaluation_date": "2024-11-09T12:00:00",
  "total_tests": 12,
  "results": [
    {
      "url": "https://example.com",
      "ground_truth": "SAFE",
      "predicted": "SAFE",
      "confidence": 95,
      "risk_score": 10,
      "correct": true,
      "duration_seconds": 32.5,
      "token_usage": { "..." },
      "cost_usd": 0.042
    }
  ]
}
```

### 3. `token_metrics.json`

Detailed token consumption with call history:

```json
{
  "summary": {
    "total_api_calls": 80,
    "total_tokens": 45000,
    "total_cost_usd": 0.52,
    "model_breakdown": { "..." },
    "operation_breakdown": {
      "create_investigation_plan": {
        "count": 12,
        "total_tokens": 8000,
        "total_cost_usd": 0.08,
        "average_tokens_per_call": 666
      },
      "investigate_iteration_1": { "..." }
    }
  },
  "call_history": [
    {
      "timestamp": "2024-11-09T12:00:00",
      "model": "gpt-5",
      "operation": "create_investigation_plan",
      "usage": {
        "prompt_tokens": 450,
        "completion_tokens": 250,
        "total_tokens": 700
      },
      "cost_usd": 0.0065
    }
  ]
}
```

### 4. `confusion_matrix.txt`

Human-readable confusion matrix:

```
CONFUSION MATRIX
================================================================================

Rows: Actual Labels
Columns: Predicted Labels

Actual/Predicted         SAFE                MANUAL_REVIEW_REQUIRED  SUSPICIOUS          MALICIOUS
---------------------------------------------------------------------------------------------------------
SAFE                     18                  1                       0                   0
MANUAL_REVIEW_REQUIRED   0                   2                       1                   0
SUSPICIOUS               1                   0                       8                   1
MALICIOUS                0                   0                       1                   19
```

### 5. `evaluation_report.html`

Interactive HTML report with charts and tables. Open in browser for visual analysis.

---

## Metrics Explained

### Classification Metrics

#### Accuracy
Overall correctness across all test cases.

```
Accuracy = (Correct Predictions) / (Total Predictions)
```

#### Precision
Of all URLs predicted as a specific label, how many were actually that label?

```
Precision = True Positives / (True Positives + False Positives)
```

High precision = Few false alarms

#### Recall
Of all URLs that are actually a specific label, how many did we correctly identify?

```
Recall = True Positives / (True Positives + False Negatives)
```

High recall = Few missed threats

#### F1 Score
Harmonic mean of precision and recall (balanced metric).

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

### Token Consumption Metrics

#### Total Tokens
Sum of all tokens consumed across all API calls.

#### Text Tokens vs Image Tokens
- **Text Tokens**: Tokens from text input/output
- **Image Tokens**: Tokens from image analysis (GPT-4o multimodal)

Typical breakdown:
- Text-only analysis: 100% text, 0% image
- With screenshot analysis: ~95% text, ~5% image

#### Cost Calculation

Based on OpenAI pricing (Nov 2024):

| Model | Prompt (per 1M tokens) | Completion (per 1M tokens) |
|-------|------------------------|----------------------------|
| GPT-5 | $3.00 | $15.00 |
| GPT-4o | $2.50 | $10.00 |
| GPT-4o-mini | $0.15 | $0.60 |

**Example Calculation**:

```python
# Investigation with GPT-5
prompt_tokens = 1200
completion_tokens = 800

prompt_cost = (1200 / 1_000_000) * $3.00 = $0.0036
completion_cost = (800 / 1_000_000) * $15.00 = $0.012

Total Cost = $0.0156 ≈ $0.016 per investigation round
```

### Performance Metrics

#### Average Duration
Mean time to analyze one URL (seconds).

#### P95 Duration
95th percentile latency - 95% of analyses complete within this time.

#### Throughput
URLs analyzed per second.

---

## Command-Line Options

### Full Option List

```bash
python run_evaluation.py [OPTIONS]

Options:
  --dataset PATH             Path to test dataset JSON file
                            Default: ../test_datasets/example_test_dataset.json

  --output PATH             Output directory for results
                            Default: ./evaluation_results

  --max-concurrent N        Maximum concurrent URL analyses
                            Default: 5
                            Higher = faster but more memory/API load

  --max-iterations N        Maximum investigation iterations per URL
                            Default: 3
                            Higher = more thorough but slower/costlier

  --no-deep-analysis        Disable deep AI analysis
                            Use rule-based analysis only (faster, cheaper, less accurate)

  --quick-test              Run quick test with 3 sample URLs
                            Useful for testing the framework

  --verbose                 Enable verbose logging
                            Shows detailed progress and debug info
```

### Examples

#### High Throughput Evaluation
```bash
python run_evaluation.py \
    --dataset large_test_set.json \
    --max-concurrent 20 \
    --max-iterations 2 \
    --output ./eval_high_throughput
```

#### Deep Analysis (Accuracy-Focused)
```bash
python run_evaluation.py \
    --dataset critical_urls.json \
    --max-concurrent 3 \
    --max-iterations 5 \
    --verbose \
    --output ./eval_deep_analysis
```

#### Cost-Optimized
```bash
python run_evaluation.py \
    --dataset test_set.json \
    --max-concurrent 10 \
    --max-iterations 1 \
    --output ./eval_cost_optimized
```

---

## Best Practices

### 1. Dataset Curation

**Do:**
- ✅ Include diverse threat types (phishing, malware, scams)
- ✅ Balance safe vs. malicious URLs (avoid class imbalance)
- ✅ Include edge cases (new domains, ambiguous URLs)
- ✅ Add metadata for threat indicators

**Don't:**
- ❌ Over-represent one category (e.g., 90% safe URLs)
- ❌ Use only synthetic/artificial URLs
- ❌ Forget to update ground truth labels regularly

### 2. Evaluation Configuration

**For Accuracy Testing:**
```python
max_concurrent = 3-5      # Lower concurrency for API stability
max_iterations = 3-5      # Higher iterations for thorough analysis
deep_analysis = True      # Enable AI reasoning
```

**For Performance Testing:**
```python
max_concurrent = 10-20    # Higher concurrency
max_iterations = 1-2      # Lower iterations
deep_analysis = True      # Still use AI but fewer iterations
```

**For Cost Testing:**
```python
max_concurrent = 5
max_iterations = 1        # Minimal iterations
deep_analysis = True      # Track token usage
```

### 3. Interpreting Results

**High Accuracy but Low Precision for MALICIOUS:**
- System is over-flagging safe URLs as malicious
- Tune down sensitivity or improve threat detection logic

**High Precision but Low Recall for MALICIOUS:**
- System misses some malicious URLs
- Increase iterations or improve investigation plan

**High Token Costs:**
- Reduce max_iterations
- Use GPT-4o-mini for non-critical operations
- Implement caching for repeat analyses

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: URL Safety Agent Evaluation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd url-safety-analyzer/backend
        pip install -r requirements.txt

    - name: Run Evaluation
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        cd url-safety-analyzer/backend
        python run_evaluation.py \
          --dataset ../test_datasets/ci_test_set.json \
          --output ./eval_results \
          --max-concurrent 5 \
          --max-iterations 2

    - name: Upload Results
      uses: actions/upload-artifact@v2
      with:
        name: evaluation-results
        path: url-safety-analyzer/backend/eval_results/

    - name: Check Accuracy Threshold
      run: |
        # Fail if accuracy < 85%
        python scripts/check_accuracy_threshold.py \
          --results ./eval_results/evaluation_summary.json \
          --threshold 0.85
```

---

## Troubleshooting

### Issue: High Token Costs

**Symptoms**: Evaluation costs more than expected

**Solutions**:
1. Reduce `max_iterations` (e.g., from 3 to 1-2)
2. Use smaller test dataset for quick iterations
3. Enable caching for repeat analyses
4. Profile which operations consume most tokens

```python
# Check token breakdown
summary = await framework.run_evaluation(...)
operation_breakdown = summary['token_usage']['operation_breakdown']

# Identify expensive operations
for op, stats in operation_breakdown.items():
    cost_per_call = stats['total_cost_usd'] / stats['count']
    print(f"{op}: ${cost_per_call:.4f} per call")
```

### Issue: Slow Evaluation

**Symptoms**: Evaluation takes too long

**Solutions**:
1. Increase `max_concurrent` (e.g., 10-20)
2. Reduce `max_iterations`
3. Use `--no-deep-analysis` for quick testing
4. Profile URL analysis duration

```python
# Check performance breakdown
perf_stats = summary['performance']
print(f"P95 Duration: {perf_stats['p95_duration']:.1f}s")
print(f"Max Duration: {perf_stats['max_duration']:.1f}s")

# Identify slow URLs in detailed_results.json
```

### Issue: Low Accuracy

**Symptoms**: Accuracy below expected threshold

**Solutions**:
1. Review confusion matrix to identify problem categories
2. Increase `max_iterations` for more thorough analysis
3. Check if test dataset labels are correct
4. Review false positives and false negatives in detailed results

```python
# Analyze false positives
false_positives = [
    r for r in framework.results
    if r.predicted_label == "MALICIOUS" and not r.correct
]

for fp in false_positives:
    print(f"False Positive: {fp.test_case.url}")
    print(f"  Predicted: {fp.predicted_label}, Actual: {fp.test_case.ground_truth_label}")
```

---

## Advanced Usage

### Custom Metrics

```python
from evaluation_framework import EvaluationMetrics

# Calculate custom metrics
metrics = EvaluationMetrics(results)

# Custom: Detection rate for phishing
phishing_results = [r for r in results if r.test_case.expected_category == "phishing"]
phishing_detected = sum(1 for r in phishing_results if r.predicted_label == "MALICIOUS")
phishing_detection_rate = phishing_detected / len(phishing_results)

print(f"Phishing Detection Rate: {phishing_detection_rate:.2%}")
```

### Token Usage Analysis

```python
from token_metrics import TokenMetricsTracker

# Analyze token usage patterns
tracker = framework.metrics_tracker
summary = tracker.get_summary()

# Cost by operation
for op, stats in summary['operation_breakdown'].items():
    avg_cost = stats['total_cost_usd'] / stats['count']
    print(f"{op}: ${avg_cost:.4f} avg cost, {stats['average_tokens_per_call']:.0f} avg tokens")

# Model efficiency
for model, metrics in summary['model_breakdown'].items():
    cost_per_token = metrics['estimated_cost_usd'] / metrics['total_tokens']
    print(f"{model}: ${cost_per_token*1000000:.2f} per 1M tokens")
```

---

## FAQ

**Q: How many test cases should I include?**

A: For initial testing: 10-20 URLs. For production validation: 100+ URLs with diverse threats.

**Q: How much does evaluation cost?**

A: Typical costs:
- With GPT-5 + 3 iterations: ~$0.05-0.10 per URL
- With GPT-5 + 1 iteration: ~$0.02-0.04 per URL
- 100 URL evaluation: ~$2-10 depending on configuration

**Q: Can I run evaluation without OpenAI API key?**

A: Yes, use `--no-deep-analysis` flag. This uses rule-based analysis only (faster, cheaper, but less accurate).

**Q: How do I add my own test URLs?**

A: Either:
1. Add to JSON test dataset file
2. Use programmatic API: `framework.add_test_case(url, label, ...)`

**Q: What's the difference between SUSPICIOUS and MALICIOUS?**

A:
- **SUSPICIOUS**: Concerning patterns, likely threat (70-85% confidence)
- **MALICIOUS**: High confidence threat (>85% confidence)

---

## Resources

- **Example Test Dataset**: `test_datasets/example_test_dataset.json`
- **Evaluation Runner**: `backend/run_evaluation.py`
- **Framework API**: `backend/evaluation_framework.py`
- **Token Tracking**: `backend/token_metrics.py`

---

## Support

For issues or questions:
1. Check this guide
2. Review example test dataset
3. Run `--quick-test` to verify framework
4. Check logs with `--verbose` flag

---

**Last Updated**: 2024-11-09
**Version**: 1.0
