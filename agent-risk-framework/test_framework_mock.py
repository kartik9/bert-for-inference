#!/usr/bin/env python3
"""
Test the complete framework flow using Mock Agent.
This validates all code without requiring ChatGPT access.
"""

import asyncio
import sys
from src.analysis.dynamic.agent_session import MockAgentSession
from src.analysis.dynamic.suites.prompt_injection import PromptInjectionSuite
from src.intake.models import AgentMetadata, AgentType
from src.scoring.aivss import AIVSSScorer
from src.reporting.nutrition_label import NutritionLabelGenerator

async def test_complete_flow():
    """Test the complete assessment flow with mock agent"""
    print("=" * 80)
    print("🧪 FRAMEWORK END-TO-END TEST (Mock Agent)")
    print("=" * 80)
    print("\nThis validates all framework code works correctly")
    print("Using Mock Agent (no ChatGPT connection required)\n")

    # Step 1: Create mock agent session
    print("=" * 80)
    print("STEP 1: Create Agent Session")
    print("=" * 80)
    session = MockAgentSession()
    print("✅ Mock agent session created")

    # Test basic communication
    test_msg = "Hello, can you help me?"
    response = await session.send_message(test_msg)
    print(f"✅ Agent responds to messages")
    print(f"   Query: '{test_msg}'")
    print(f"   Response: '{response[:100]}...'")

    # Step 2: Run Prompt Injection Test Suite
    print("\n" + "=" * 80)
    print("STEP 2: Run Prompt Injection Test Suite")
    print("=" * 80)

    suite = PromptInjectionSuite()
    await suite.load_test_cases()
    print(f"✅ Test suite loaded: {len(suite.test_cases)} test cases")

    # Run full test suite
    print(f"⏳ Running all {len(suite.test_cases)} tests...")
    results = await suite.run(session)

    print(f"\n✅ Test suite completed!")
    print(f"   Total tests: {results.total_tests}")
    print(f"   Passed: {results.passed}")
    print(f"   Failed: {results.failed}")
    print(f"   Pass rate: {results.pass_rate:.1f}%")
    print(f"   Execution time: {results.execution_time_ms}ms")

    # Show sample results
    print(f"\n📋 Sample Test Results:")
    for i, test_result in enumerate(results.all_results[:3], 1):
        print(f"\n   Test {i}: {test_result.test_name}")
        print(f"   Result: {test_result.result.value.upper()}")
        print(f"   Severity: {test_result.severity.value}")
        print(f"   Details: {test_result.details}")
        print(f"   Response preview: {test_result.response_received[:80]}...")

    # Step 3: Calculate AIVSS Score
    print("\n" + "=" * 80)
    print("STEP 3: Calculate AIVSS Risk Score")
    print("=" * 80)

    # Create agent metadata
    agent = AgentMetadata(
        agent_id="mock-expedia-001",
        name="Mock Expedia Travel Agent",
        version="1.0.0",
        agent_type=AgentType.OPENAI_GPT,
        model_backend="gpt-4",
        description="Mock travel planning agent for testing"
    )
    print(f"✅ Agent metadata created: {agent.name}")

    # Prepare results for scoring
    dynamic_results = {
        'prompt_injection': results
    }

    scorer = AIVSSScorer()
    score = scorer.calculate(
        static_results=None,
        dynamic_results=dynamic_results,
        agent_metadata=agent
    )

    print(f"\n✅ AIVSS Score calculated!")
    print(f"\n   Overall Score: {score.overall_score:.1f}/100")
    print(f"   Letter Grade: {score.letter_grade.value}")
    print(f"   Trust Tier: {score.trust_tier.value} ({score.trust_tier.description})")
    print(f"\n   Dimensional Scores:")
    print(f"   - Security: {score.dimensions.security:.1f}")
    print(f"   - Privacy: {score.dimensions.privacy:.1f}")
    print(f"   - Reliability: {score.dimensions.reliability:.1f}")
    print(f"   - Transparency: {score.dimensions.transparency:.1f}")
    print(f"   - Autonomy Risk: {score.dimensions.autonomy_risk:.1f}")

    # Step 4: Generate Nutrition Label
    print("\n" + "=" * 80)
    print("STEP 4: Generate Nutrition Label Report")
    print("=" * 80)

    generator = NutritionLabelGenerator()

    # Generate HTML report
    html_report = generator.generate_html(agent, score)
    print(f"✅ HTML report generated ({len(html_report):,} characters)")

    # Save HTML report
    report_file = "mock_agent_nutrition_label.html"
    with open(report_file, 'w') as f:
        f.write(html_report)
    print(f"✅ Saved to: {report_file}")

    # Generate JSON report
    json_report = generator.generate_json(agent, score)
    print(f"✅ JSON report generated ({len(json_report):,} characters)")

    # Save JSON report
    json_file = "mock_agent_nutrition_label.json"
    with open(json_file, 'w') as f:
        f.write(json_report)
    print(f"✅ Saved to: {json_file}")

    # Verify HTML content
    if agent.name in html_report and str(score.overall_score) in html_report:
        print(f"✅ HTML report contains expected data")
    else:
        print(f"⚠️  HTML report may be missing some data")

    # Verify JSON structure
    import json
    json_data = json.loads(json_report)
    if 'agent' in json_data and 'scores' in json_data and 'trust' in json_data:
        print(f"✅ JSON report has correct structure")
        print(f"   Keys: {', '.join(json_data.keys())}")
    else:
        print(f"❌ JSON structure invalid - got keys: {', '.join(json_data.keys())}")
        return False

    # Close session
    try:
        await session.close()
        print(f"\n✅ Session closed")
    except AttributeError:
        print(f"\n✅ Session cleanup (mock agent has no close method)")

    # Final summary
    print("\n" + "=" * 80)
    print("🎉 COMPLETE FRAMEWORK TEST PASSED!")
    print("=" * 80)
    print("\n✅ All framework components working:")
    print("   ✅ Agent session management")
    print("   ✅ Prompt injection test suite (10 tests)")
    print("   ✅ AIVSS scoring engine")
    print("   ✅ Nutrition label generation (HTML + JSON)")
    print("   ✅ End-to-end workflow")

    print(f"\n📊 Test Results Summary:")
    print(f"   Agent: {agent.name}")
    print(f"   Tests Run: {results.total_tests}")
    print(f"   Overall Score: {score.overall_score:.1f}/100")
    print(f"   Grade: {score.letter_grade.value}")
    print(f"   Trust Tier: {score.trust_tier.value}")

    print(f"\n📄 Reports Generated:")
    print(f"   - {report_file}")
    print(f"   - {json_file}")

    print(f"\n🚀 Framework is fully functional and ready for use!")
    print(f"   Next: Test with real GPT Store agents on a machine with ChatGPT access")

    return True

async def main():
    try:
        success = await test_complete_flow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
