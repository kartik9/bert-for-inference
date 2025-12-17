#!/usr/bin/env python3
"""
Trust & Safety Newsletter Automation - Main Runner
Orchestrates the complete newsletter generation workflow
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ts_newsletter.agents.orchestrator_agent import OrchestratorAgent
from ts_newsletter.config_loader import get_config
from ts_newsletter.llm_client import LLMClientFactory


def run_newsletter_generation(
    output_dir: str = "./output/newsletters",
    verbose: bool = False
):
    """
    Run the complete newsletter generation workflow

    Args:
        output_dir: Directory to save output
        verbose: Print detailed progress
    """
    print("="*60)
    print("Trust & Safety Newsletter Automation")
    print("="*60)

    # Load configuration
    print("\n[1/7] Loading configuration...")
    try:
        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"  - LLM: {config.llm.model}")
        print(f"  - Search: {config.search.provider}")
        print(f"  - Target articles: {config.newsletter.target_articles}")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        sys.exit(1)

    # Initialize LLM client
    print("\n[2/7] Initializing LLM client...")
    try:
        llm_client = LLMClientFactory.create(config, agent_name="orchestrator")
        print(f"✓ LLM client initialized (model: {llm_client.model})")
    except Exception as e:
        print(f"✗ Failed to initialize LLM: {e}")
        sys.exit(1)

    # Create orchestrator agent
    print("\n[3/7] Creating orchestrator agent...")
    try:
        orchestrator = OrchestratorAgent(
            agent_name="orchestrator-main",
            llm_client=llm_client,
            config=config,
            database_client=None  # TODO: Add database client
        )
        print("✓ Orchestrator agent created")
    except Exception as e:
        print(f"✗ Failed to create orchestrator: {e}")
        sys.exit(1)

    # Define task
    print("\n[4/7] Defining research task...")
    week_ending = (datetime.now() + timedelta(days=(6 - datetime.now().weekday())))
    week_str = week_ending.strftime("%B %d, %Y")

    task = f"""Generate this week's Trust & Safety newsletter for Microsoft Ads.

OBJECTIVE:
Create a comprehensive newsletter covering advertising fraud and security threats from the past 7 days.

WORKFLOW:
1. RESEARCH: Spawn 3-5 research agents to gather articles
   - Topics: malvertising, ad cloaking, deepfakes, bot traffic, platform incidents
   - Sources: Web search + RSS feeds (security blogs, ad tech industry)
   - Target: {config.newsletter.target_articles} high-quality articles

2. EVALUATION: Score all collected articles
   - Filter for relevance score ≥ {config.newsletter.min_relevance}
   - Ensure balanced coverage across threat types
   - Select top candidates

3. ANALYSIS: Perform threat intelligence analysis
   - Extract technical details and IOCs
   - Identify Aurora detection gaps
   - Generate actionable recommendations

4. GENERATION: Create newsletter summaries
   - Executive-friendly language
   - Include metrics and impact
   - Proper source attribution

5. QUALITY: Review and approve
   - Verify factual accuracy
   - Check style compliance
   - Final approval

Week Ending: {week_str}

Execute the complete workflow autonomously. Report progress and final newsletter."""

    print(f"✓ Task defined for week ending {week_str}")

    # Run workflow
    print("\n[5/7] Running newsletter generation workflow...")
    print("This may take 5-15 minutes depending on research depth...")
    print()

    try:
        start_time = datetime.now()

        result = orchestrator.run(task)

        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n✓ Workflow completed in {duration.total_seconds():.1f} seconds")

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Get workflow summary
    print("\n[6/7] Workflow summary:")
    summary = orchestrator.get_workflow_summary()

    print(f"  - Status: {summary['workflow_state']['status']}")
    print(f"  - Phase: {summary['workflow_state']['phase']}")
    print(f"  - Duration: {summary['workflow_state']['elapsed_time']}")
    print(f"\n  Metrics:")
    print(f"  - Articles collected: {summary['metrics']['articles_collected']}")
    print(f"  - Articles scored: {summary['metrics']['articles_scored']}")
    print(f"  - Articles analyzed: {summary['metrics']['articles_analyzed']}")
    print(f"  - Summaries generated: {summary['metrics']['summaries_generated']}")
    if summary['metrics']['quality_score']:
        print(f"  - Quality score: {summary['metrics']['quality_score']:.1f}/10")

    # Save output
    print("\n[7/7] Saving output...")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save newsletter
    newsletter = orchestrator.get_final_newsletter()

    if newsletter:
        # Save markdown
        newsletter_file = output_path / f"newsletter_{week_ending.strftime('%Y-%m-%d')}.md"
        with open(newsletter_file, 'w') as f:
            f.write(newsletter)
        print(f"✓ Newsletter saved: {newsletter_file}")

        # Save summary JSON
        summary_file = output_path / f"summary_{week_ending.strftime('%Y-%m-%d')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"✓ Summary saved: {summary_file}")

        # Save agent traces (if verbose)
        if verbose:
            traces_file = output_path / f"traces_{week_ending.strftime('%Y-%m-%d')}.json"
            trace_data = {
                "orchestrator": orchestrator.get_trace().__dict__,
                "summary": summary
            }
            with open(traces_file, 'w') as f:
                json.dump(trace_data, f, indent=2, default=str)
            print(f"✓ Agent traces saved: {traces_file}")

        # Print preview
        print("\n" + "="*60)
        print("NEWSLETTER PREVIEW")
        print("="*60)
        print(newsletter[:1000])
        if len(newsletter) > 1000:
            print(f"\n... ({len(newsletter) - 1000} more characters)")
            print(f"\nFull newsletter: {newsletter_file}")

    else:
        print("✗ No newsletter generated")
        sys.exit(1)

    print("\n" + "="*60)
    print("Newsletter generation completed successfully!")
    print("="*60)


def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Trust & Safety Newsletter Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate newsletter with default settings
  python run_newsletter.py

  # Specify output directory
  python run_newsletter.py --output ./my_newsletters

  # Verbose mode with agent traces
  python run_newsletter.py --verbose

  # Custom config file
  TS_NEWSLETTER_CONFIG=./custom_config.yaml python run_newsletter.py
        """
    )

    parser.add_argument(
        '--output',
        '-o',
        default='./output/newsletters',
        help='Output directory for newsletters (default: ./output/newsletters)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output and save agent traces'
    )

    parser.add_argument(
        '--config',
        '-c',
        help='Path to config file (default: ./ts_newsletter/config.yaml or TS_NEWSLETTER_CONFIG env var)'
    )

    args = parser.parse_args()

    # Set config path if provided
    if args.config:
        import os
        os.environ['TS_NEWSLETTER_CONFIG'] = args.config

    # Run newsletter generation
    try:
        run_newsletter_generation(
            output_dir=args.output,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
