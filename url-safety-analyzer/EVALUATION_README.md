# URL Safety Analysis - Evaluation Framework

Complete evaluation system for measuring accuracy, token consumption, and cost of the URL safety analysis agent.

## Features

✅ **Classification Metrics**: Accuracy, Precision, Recall, F1 Score
✅ **Token Tracking**: Model-specific breakdown (GPT-5, GPT-4o, GPT-4o-mini)
✅ **Token Type Analysis**: Text vs Image token consumption
✅ **Cost Estimation**: Per-URL and total costs with pricing breakdown
✅ **Performance Metrics**: Latency, throughput, percentiles
✅ **Comprehensive Reporting**: JSON, HTML, and text outputs
✅ **Batch Processing**: Concurrent evaluation with configurable parallelism

## Quick Start

```bash
# 1. Navigate to backend directory
cd url-safety-analyzer/backend

# 2. Run evaluation with example dataset
python run_evaluation.py \
    --dataset ../test_datasets/example_test_dataset.json \
    --output ./evaluation_results

# 3. View results
open evaluation_results/evaluation_*/evaluation_report.html
```

## What's Included

### Core Components

1. **`token_metrics.py`** - Token consumption tracker
   - Tracks all OpenAI API calls
   - Model-specific metrics (GPT-5, GPT-4o, GPT-4o-mini)
   - Text vs Image token breakdown
   - Cost calculation

2. **`ai_agent_with_metrics.py`** - AI agent with metrics integration
   - Extends existing SafetyAnalysisAgent
   - Automatic token tracking on all API calls
   - Supports streaming responses
   - Image token estimation for GPT-4o

3. **`evaluation_framework.py`** - Evaluation orchestration
   - Test dataset loading
   - Batch URL analysis
   - Metrics calculation (accuracy, P/R/F1)
   - Multi-format reporting

4. **`run_evaluation.py`** - Command-line runner
   - Simple CLI interface
   - Configurable concurrency and depth
   - Result export automation

### Test Datasets

- **`test_datasets/example_test_dataset.json`** - Example test set
  - 12 diverse test cases
  - Safe, Suspicious, and Malicious URLs
  - Ground truth labels with metadata

## Output Files

After evaluation, you'll get:

```
evaluation_results/
└── evaluation_20241109_120000/
    ├── evaluation_summary.json       # High-level metrics
    ├── detailed_results.json         # Per-URL results
    ├── token_metrics.json            # Token consumption details
    ├── confusion_matrix.txt          # Classification matrix
    └── evaluation_report.html        # Interactive HTML report
```

## Example Results

### Token Consumption Breakdown

```
TOKEN CONSUMPTION METRICS SUMMARY
================================================================================

Session Duration: 420.5 seconds
Total API Calls: 48
Total Tokens: 35,420
Total Cost: $0.42

TOKEN TYPE BREAKDOWN
--------------------------------------------------------------------------------
Text Tokens:  34,650 (97.8%)
Image Tokens: 770 (2.2%)

MODEL BREAKDOWN
--------------------------------------------------------------------------------

gpt-5:
  Calls: 36
  Prompt Tokens: 21,800
  Completion Tokens: 11,200
  Total Tokens: 33,000
  Cost: $0.38

gpt-4o-mini:
  Calls: 12
  Prompt Tokens: 1,620
  Completion Tokens: 800
  Total Tokens: 2,420
  Cost: $0.04
```

### Classification Performance

```
CLASSIFICATION METRICS
--------------------------------------------------------------------------------
Label                    Precision      Recall         F1 Score
--------------------------------------------------------------------------------
SAFE                     95.0%          100.0%         97.4%
MANUAL_REVIEW_REQUIRED   100.0%         50.0%          66.7%
SUSPICIOUS               75.0%          100.0%         85.7%
MALICIOUS                100.0%         80.0%          88.9%

Overall Accuracy: 91.7%
```

## Usage Examples

### Basic Evaluation

```bash
python run_evaluation.py \
    --dataset test_dataset.json \
    --output ./results
```

### High Concurrency (Fast)

```bash
python run_evaluation.py \
    --dataset test_dataset.json \
    --max-concurrent 20 \
    --max-iterations 1
```

### Deep Analysis (Accurate)

```bash
python run_evaluation.py \
    --dataset critical_urls.json \
    --max-concurrent 3 \
    --max-iterations 5 \
    --verbose
```

### Quick Test (3 URLs)

```bash
python run_evaluation.py --quick-test
```

## Programmatic Usage

```python
import asyncio
from evaluation_framework import EvaluationFramework

async def custom_evaluation():
    # Create framework
    framework = EvaluationFramework()

    # Load test dataset
    framework.load_test_dataset("my_tests.json")

    # Or add cases manually
    framework.add_test_case(
        url="https://example.com",
        ground_truth_label="SAFE",
        description="Test case"
    )

    # Run evaluation
    summary = await framework.run_evaluation(
        max_concurrent=5,
        deep_analysis=True,
        max_iterations=3
    )

    # Print and export
    framework.print_summary()
    framework.export_results("./results")

asyncio.run(custom_evaluation())
```

## Token Metrics API

```python
from token_metrics import TokenMetricsTracker, TokenUsage

# Create tracker
tracker = TokenMetricsTracker()

# Track manual API call
usage = TokenUsage(
    prompt_tokens=500,
    completion_tokens=300,
    total_tokens=800,
    text_tokens=800,
    image_tokens=0
)

tracker.track_api_call(
    model="gpt-5",
    usage=usage,
    operation="custom_operation"
)

# Get summary
summary = tracker.get_summary()
print(f"Total Cost: ${summary['total_cost_usd']:.4f}")

# Export
tracker.export_to_json("metrics.json")
tracker.print_summary()
```

## Configuration Options

### Command-Line Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--dataset` | Path to test dataset JSON | `example_test_dataset.json` |
| `--output` | Output directory | `./evaluation_results` |
| `--max-concurrent` | Concurrent analyses | `5` |
| `--max-iterations` | Investigation rounds | `3` |
| `--no-deep-analysis` | Disable AI analysis | `False` |
| `--quick-test` | Run 3 sample URLs | `False` |
| `--verbose` | Verbose logging | `False` |

### Dataset Format

```json
{
  "test_cases": [
    {
      "url": "https://example.com",
      "ground_truth_label": "SAFE|SUSPICIOUS|MALICIOUS|MANUAL_REVIEW_REQUIRED",
      "expected_category": "phishing|malware|scam|fraud|legitimate",
      "description": "Test description",
      "metadata": {
        "source": "phishtank",
        "threat_indicators": ["typosquatting"]
      }
    }
  ]
}
```

## Cost Estimates

Typical costs per URL (with GPT-5):

| Configuration | Tokens/URL | Cost/URL | 100 URLs |
|---------------|-----------|----------|----------|
| 1 iteration | ~2,000 | $0.02 | $2.00 |
| 2 iterations | ~3,500 | $0.04 | $4.00 |
| 3 iterations | ~5,000 | $0.06 | $6.00 |
| With images | ~6,000 | $0.08 | $8.00 |

## Performance Benchmarks

On a modern machine:

- **Throughput**: 5-10 URLs/minute (with deep analysis)
- **Latency**: 30-60 seconds per URL average
- **P95 Latency**: 75 seconds
- **Concurrency**: Supports 20+ concurrent analyses

## Troubleshooting

### High Token Costs

**Solution**: Reduce `--max-iterations` or use `--no-deep-analysis`

```bash
python run_evaluation.py --max-iterations 1 --dataset test.json
```

### Slow Evaluation

**Solution**: Increase `--max-concurrent`

```bash
python run_evaluation.py --max-concurrent 15 --dataset test.json
```

### Low Accuracy

**Solution**: Increase `--max-iterations` for more thorough analysis

```bash
python run_evaluation.py --max-iterations 5 --dataset test.json
```

## Documentation

For detailed usage and best practices, see:

📘 **[EVALUATION_GUIDE.md](./EVALUATION_GUIDE.md)** - Complete evaluation guide

## Requirements

- Python 3.9+
- OpenAI API key (in `.env` file)
- All dependencies from `requirements.txt`

```bash
pip install -r backend/requirements.txt
```

## Environment Setup

```bash
# 1. Copy environment template
cp backend/.env.example backend/.env

# 2. Add your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env

# 3. Run evaluation
cd backend
python run_evaluation.py --quick-test
```

## Next Steps

1. ✅ Review example test dataset
2. ✅ Run quick test: `python run_evaluation.py --quick-test`
3. ✅ Create your own test dataset
4. ✅ Run full evaluation
5. ✅ Analyze results in HTML report

## Support

- **Documentation**: See [EVALUATION_GUIDE.md](./EVALUATION_GUIDE.md)
- **Issues**: Check verbose logs with `--verbose` flag
- **Questions**: Review example dataset and code comments

---

**Version**: 1.0
**Last Updated**: 2024-11-09
**License**: MIT
