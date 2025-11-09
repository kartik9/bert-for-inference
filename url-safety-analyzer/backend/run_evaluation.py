"""
Evaluation Runner Script

Run comprehensive evaluation of URL Safety Analysis Agent with:
- Test dataset loading
- Batch analysis execution
- Metrics collection (accuracy, tokens, cost)
- Report generation
"""

import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime

from evaluation_framework import EvaluationFramework
from url_analyzer import URLAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_evaluation(
    test_dataset_path: str,
    output_dir: str,
    max_concurrent: int = 5,
    deep_analysis: bool = True,
    max_iterations: int = 3,
    verbose: bool = False
):
    """
    Run comprehensive evaluation

    Args:
        test_dataset_path: Path to JSON test dataset file
        output_dir: Directory to save evaluation results
        max_concurrent: Maximum concurrent URL analyses
        deep_analysis: Enable deep AI analysis
        max_iterations: Maximum investigation iterations
        verbose: Print detailed progress
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("="*80)
    logger.info("URL SAFETY ANALYSIS AGENT - EVALUATION")
    logger.info("="*80)

    # Initialize framework
    logger.info("Initializing evaluation framework...")
    url_analyzer = URLAnalyzer()
    framework = EvaluationFramework(url_analyzer=url_analyzer)

    # Load test dataset
    logger.info(f"Loading test dataset from: {test_dataset_path}")
    framework.load_test_dataset(test_dataset_path)
    logger.info(f"Loaded {len(framework.test_cases)} test cases")

    # Display test distribution
    label_counts = {}
    for tc in framework.test_cases:
        label = tc.ground_truth_label
        label_counts[label] = label_counts.get(label, 0) + 1

    logger.info("\nTest case distribution:")
    for label, count in sorted(label_counts.items()):
        logger.info(f"  {label}: {count}")

    # Run evaluation
    logger.info("\n" + "="*80)
    logger.info("STARTING EVALUATION")
    logger.info("="*80)
    logger.info(f"Configuration:")
    logger.info(f"  Max Concurrent: {max_concurrent}")
    logger.info(f"  Deep Analysis: {deep_analysis}")
    logger.info(f"  Max Iterations: {max_iterations}")
    logger.info("")

    start_time = datetime.utcnow()

    summary = await framework.run_evaluation(
        max_concurrent=max_concurrent,
        deep_analysis=deep_analysis,
        max_iterations=max_iterations
    )

    end_time = datetime.utcnow()
    total_duration = (end_time - start_time).total_seconds()

    # Print summary
    logger.info("\n" + "="*80)
    logger.info("EVALUATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Total Duration: {total_duration:.1f}s")
    logger.info(f"Throughput: {len(framework.test_cases) / total_duration:.2f} URLs/sec")

    framework.print_summary()

    # Export results
    logger.info("\n" + "="*80)
    logger.info("EXPORTING RESULTS")
    logger.info("="*80)

    output_path = Path(output_dir)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    eval_output_dir = output_path / f"evaluation_{timestamp}"

    framework.export_results(str(eval_output_dir))

    logger.info(f"\nResults saved to: {eval_output_dir}")
    logger.info("\nGenerated files:")
    logger.info(f"  - evaluation_summary.json     (High-level metrics)")
    logger.info(f"  - detailed_results.json       (Per-URL results)")
    logger.info(f"  - token_metrics.json          (Token consumption details)")
    logger.info(f"  - confusion_matrix.txt        (Classification confusion matrix)")
    logger.info(f"  - evaluation_report.html      (Interactive HTML report)")

    logger.info("\n" + "="*80)
    logger.info("EVALUATION COMPLETE - ALL RESULTS EXPORTED")
    logger.info("="*80)

    return summary


async def run_quick_test():
    """
    Quick test with a few manually defined URLs
    Useful for testing the evaluation framework itself
    """
    logger.info("Running quick test with sample URLs...")

    framework = EvaluationFramework()

    # Add test cases manually
    framework.add_test_case(
        url="https://www.google.com",
        ground_truth_label="SAFE",
        expected_category="legitimate",
        description="Major search engine"
    )

    framework.add_test_case(
        url="https://paypa1-secure-login.net",
        ground_truth_label="MALICIOUS",
        expected_category="phishing",
        description="PayPal typosquatting"
    )

    framework.add_test_case(
        url="https://crypto-airdrop-free.com",
        ground_truth_label="SUSPICIOUS",
        expected_category="scam",
        description="Cryptocurrency scam"
    )

    # Run evaluation
    summary = await framework.run_evaluation(
        max_concurrent=2,
        deep_analysis=True,
        max_iterations=2
    )

    # Print summary
    framework.print_summary()

    # Export results
    framework.export_results("./eval_results_quick_test")

    return summary


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive evaluation of URL Safety Analysis Agent"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        help="Path to JSON test dataset file",
        default="../test_datasets/example_test_dataset.json"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for results",
        default="./evaluation_results"
    )

    parser.add_argument(
        "--max-concurrent",
        type=int,
        help="Maximum concurrent URL analyses",
        default=5
    )

    parser.add_argument(
        "--no-deep-analysis",
        action="store_true",
        help="Disable deep AI analysis (faster but less accurate)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum investigation iterations",
        default=3
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run quick test with 3 sample URLs"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Run evaluation
    if args.quick_test:
        asyncio.run(run_quick_test())
    else:
        asyncio.run(run_evaluation(
            test_dataset_path=args.dataset,
            output_dir=args.output,
            max_concurrent=args.max_concurrent,
            deep_analysis=not args.no_deep_analysis,
            max_iterations=args.max_iterations,
            verbose=args.verbose
        ))


if __name__ == "__main__":
    main()
