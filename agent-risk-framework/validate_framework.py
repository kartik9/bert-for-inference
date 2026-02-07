#!/usr/bin/env python3
"""
Framework validation script - validates all components work correctly.
This can run without browser/authentication to verify code integrity.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test all required imports work"""
    print("=" * 80)
    print("🧪 TEST 1: Module Imports")
    print("=" * 80)

    tests = []

    try:
        from src.intake.models import AgentMetadata, ToolDefinition, AgentType
        print("✅ intake.models - AgentMetadata, ToolDefinition, AgentType")
        tests.append(True)
    except Exception as e:
        print(f"❌ intake.models failed: {e}")
        tests.append(False)

    try:
        from src.intake.connectors.openai_gpt import OpenAIGPTConnector
        print("✅ intake.connectors.openai_gpt - OpenAIGPTConnector")
        tests.append(True)
    except Exception as e:
        print(f"❌ openai_gpt connector failed: {e}")
        tests.append(False)

    try:
        from src.intake.connectors.chatgpt_web import ChatGPTWebConnector
        print("✅ intake.connectors.chatgpt_web - ChatGPTWebConnector")
        tests.append(True)
    except Exception as e:
        print(f"❌ chatgpt_web connector failed: {e}")
        tests.append(False)

    try:
        from src.analysis.dynamic.agent_session import AgentSession, MockAgentSession
        print("✅ analysis.dynamic.agent_session - AgentSession, MockAgentSession")
        tests.append(True)
    except Exception as e:
        print(f"❌ agent_session failed: {e}")
        tests.append(False)

    try:
        from src.analysis.dynamic.chatgpt_web_session import ChatGPTWebSession
        print("✅ analysis.dynamic.chatgpt_web_session - ChatGPTWebSession")
        tests.append(True)
    except Exception as e:
        print(f"❌ chatgpt_web_session failed: {e}")
        tests.append(False)

    try:
        from src.analysis.dynamic.suites.base import BaseTestSuite
        from src.analysis.dynamic.suites.prompt_injection import PromptInjectionSuite
        print("✅ analysis.dynamic.suites - BaseTestSuite, PromptInjectionSuite")
        tests.append(True)
    except Exception as e:
        print(f"❌ test suites failed: {e}")
        tests.append(False)

    try:
        from src.scoring.aivss import AIVSSScorer
        print("✅ scoring.aivss - AIVSSScorer")
        tests.append(True)
    except Exception as e:
        print(f"❌ aivss scorer failed: {e}")
        tests.append(False)

    try:
        from src.reporting.nutrition_label import NutritionLabelGenerator
        print("✅ reporting.nutrition_label - NutritionLabelGenerator")
        tests.append(True)
    except Exception as e:
        print(f"❌ nutrition label generator failed: {e}")
        tests.append(False)

    try:
        from src.config import settings
        print("✅ config - settings")
        tests.append(True)
    except Exception as e:
        print(f"❌ config failed: {e}")
        tests.append(False)

    print(f"\n📊 Import Tests: {sum(tests)}/{len(tests)} passed")
    return all(tests)


async def test_prompt_injection_suite():
    """Test prompt injection suite loads correctly"""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Prompt Injection Test Suite")
    print("=" * 80)

    try:
        from src.analysis.dynamic.suites.prompt_injection import PromptInjectionSuite

        suite = PromptInjectionSuite()
        await suite.load_test_cases()

        print(f"✅ Test suite created")
        print(f"✅ Loaded {len(suite.test_cases)} test cases")

        # Show test cases
        print(f"\n📋 Test Cases:")
        for i, test in enumerate(suite.test_cases, 1):
            print(f"   {i}. {test['name']} (Severity: {test['severity']})")

        # Verify all required fields
        required_fields = ['id', 'name', 'category', 'severity', 'payload']
        for test in suite.test_cases:
            for field in required_fields:
                if field not in test:
                    print(f"❌ Test {test.get('id', 'unknown')} missing field: {field}")
                    return False

        print(f"\n✅ All test cases have required fields")
        return True

    except Exception as e:
        print(f"❌ Failed to load prompt injection suite: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_agent():
    """Test with mock agent to verify flow"""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: Mock Agent Testing Flow")
    print("=" * 80)

    try:
        from src.analysis.dynamic.agent_session import MockAgentSession
        from src.analysis.dynamic.suites.prompt_injection import PromptInjectionSuite

        # Create mock session
        session = MockAgentSession()
        print("✅ Mock agent session created")

        # Test sending a message
        response = await session.send_message("Hello")
        print(f"✅ Mock agent responded: '{response[:50]}...'")

        # Run one test case
        suite = PromptInjectionSuite()
        await suite.load_test_cases()

        test_case = suite.test_cases[0]
        print(f"\n📤 Testing case: {test_case['name']}")

        result = await suite.execute_test(session, test_case)

        print(f"✅ Test executed")
        print(f"   Passed: {result.passed}")
        print(f"   Vulnerability: {result.vulnerability_found}")
        print(f"   Response: {result.agent_response[:100]}")

        await session.close()
        print(f"\n✅ Mock testing flow complete")
        return True

    except Exception as e:
        print(f"❌ Mock agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scoring():
    """Test AIVSS scoring engine"""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: AIVSS Scoring Engine")
    print("=" * 80)

    try:
        from src.scoring.aivss import AIVSSScorer
        from src.intake.models import AgentMetadata, AgentType

        # Create test agent
        agent = AgentMetadata(
            agent_id="test-001",
            name="Test Agent",
            version="1.0.0",
            agent_type=AgentType.OPENAI_GPT,
            model_backend="gpt-4"
        )
        print("✅ Test agent metadata created")

        # Create mock dynamic results
        dynamic_results = {
            'prompt_injection': type('obj', (object,), {
                'total_tests': 10,
                'passed_tests': 7,
                'failed_tests': 3,
                'critical_findings': [],
                'high_findings': [{'test_name': 'Test 1'}],
                'medium_findings': [{'test_name': 'Test 2'}],
                'low_findings': []
            })()
        }

        scorer = AIVSSScorer()
        score = scorer.calculate_score(agent, dynamic_results, static_results=None)

        print(f"\n✅ Score calculated successfully")
        print(f"   Overall Score: {score.overall_score:.1f}/100")
        print(f"   Letter Grade: {score.letter_grade}")
        print(f"   Trust Tier: {score.trust_tier}")
        print(f"\n   Dimensional Scores:")
        print(f"   - Security: {score.security_score:.1f}")
        print(f"   - Privacy: {score.privacy_score:.1f}")
        print(f"   - Reliability: {score.reliability_score:.1f}")
        print(f"   - Transparency: {score.transparency_score:.1f}")
        print(f"   - Autonomy Risk: {score.autonomy_risk_score:.1f}")

        return True

    except Exception as e:
        print(f"❌ Scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_nutrition_label():
    """Test nutrition label generation"""
    print("\n" + "=" * 80)
    print("🧪 TEST 5: Nutrition Label Generation")
    print("=" * 80)

    try:
        from src.reporting.nutrition_label import NutritionLabelGenerator
        from src.scoring.aivss import AIVSSScore
        from src.intake.models import AgentMetadata, AgentType

        # Create test data
        agent = AgentMetadata(
            agent_id="expedia-test",
            name="Expedia",
            version="1.0.0",
            agent_type=AgentType.OPENAI_GPT,
            model_backend="gpt-4",
            description="Travel planning agent"
        )

        score = AIVSSScore(
            overall_score=85.5,
            letter_grade="B",
            trust_tier=3,
            security_score=80.0,
            privacy_score=90.0,
            reliability_score=85.0,
            transparency_score=82.0,
            autonomy_risk_score=88.0,
            recommendation="Trusted for general use with audit logging"
        )

        generator = NutritionLabelGenerator()

        # Test HTML generation
        html = generator.generate_html(agent, score)
        print(f"✅ HTML report generated ({len(html)} chars)")

        # Verify HTML content
        if "Expedia" in html and "85.5" in html and "Grade B" in html:
            print(f"✅ HTML contains expected content")
        else:
            print(f"⚠️  HTML may be missing content")

        # Test JSON generation
        json_report = generator.generate_json(agent, score)
        print(f"✅ JSON report generated ({len(json_report)} chars)")

        # Verify JSON structure
        import json
        data = json.loads(json_report)
        if 'agent' in data and 'score' in data:
            print(f"✅ JSON has correct structure")
        else:
            print(f"❌ JSON structure invalid")
            return False

        return True

    except Exception as e:
        print(f"❌ Nutrition label test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connector_parsing():
    """Test ChatGPT Web connector GPT ID parsing"""
    print("\n" + "=" * 80)
    print("🧪 TEST 6: ChatGPT Web Connector - GPT ID Parsing")
    print("=" * 80)

    try:
        from src.intake.connectors.chatgpt_web import ChatGPTWebConnector

        connector = ChatGPTWebConnector()

        test_cases = [
            ("g-68d8ecbe98388191bd93f6b1d03158bf", "g-68d8ecbe98388191bd93f6b1d03158bf"),
            ("https://chatgpt.com/g/g-68d8ecbe98388191bd93f6b1d03158bf-expedia", "g-68d8ecbe98388191bd93f6b1d03158bf"),
            ("https://chat.openai.com/g/g-68d8ecbe98388191bd93f6b1d03158bf", "g-68d8ecbe98388191bd93f6b1d03158bf"),
        ]

        all_passed = True
        for input_id, expected in test_cases:
            result = connector.parse_gpt_identifier(input_id)
            if result == expected:
                print(f"✅ '{input_id[:50]}...' → '{result}'")
            else:
                print(f"❌ '{input_id[:50]}...' → '{result}' (expected '{expected}')")
                all_passed = False

        if all_passed:
            print(f"\n✅ All ID parsing tests passed")
        else:
            print(f"\n❌ Some ID parsing tests failed")

        return all_passed

    except Exception as e:
        print(f"❌ Connector parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading"""
    print("\n" + "=" * 80)
    print("🧪 TEST 7: Configuration Loading")
    print("=" * 80)

    try:
        from src.config import settings

        print(f"✅ Settings loaded")
        print(f"\n📋 Current Configuration:")
        print(f"   USE_WEB_TESTING: {settings.use_web_testing}")
        print(f"   USE_AZURE_OPENAI: {settings.use_azure_openai}")
        print(f"   WEB_TESTING_HEADLESS: {settings.web_testing_headless}")
        print(f"   ENV: {settings.env}")
        print(f"   LOG_LEVEL: {settings.log_level}")

        if settings.use_web_testing:
            print(f"\n✅ Web testing is ENABLED")
            print(f"   Ready for Expedia GPT testing!")
        else:
            print(f"\n⚠️  Web testing is DISABLED")
            print(f"   Set USE_WEB_TESTING=true in .env to test real GPTs")

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests"""
    print("\n" + "=" * 80)
    print("🚀 AI AGENT RISK ASSESSMENT FRAMEWORK - VALIDATION")
    print("=" * 80)
    print("\nThis script validates all framework components are working correctly.")
    print("It does NOT require browser authentication - just code validation.\n")

    results = []

    # Run all tests
    results.append(("Module Imports", test_imports()))
    results.append(("Prompt Injection Suite", await test_prompt_injection_suite()))
    results.append(("Mock Agent Flow", await test_mock_agent()))
    results.append(("AIVSS Scoring", await test_scoring()))
    results.append(("Nutrition Label", await test_nutrition_label()))
    results.append(("GPT ID Parsing", test_connector_parsing()))
    results.append(("Configuration", test_config()))

    # Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} - {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n📈 Overall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n" + "=" * 80)
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("=" * 80)
        print("\n✅ Framework code is functioning correctly")
        print("✅ All imports working")
        print("✅ Test suites load properly")
        print("✅ Scoring engine operational")
        print("✅ Report generation working")
        print("✅ Configuration valid")
        print("\n🚀 READY FOR LIVE TESTING WITH EXPEDIA GPT!")
        print("\nNext steps:")
        print("1. Review EXPEDIA_TEST_GUIDE.md for live testing instructions")
        print("2. Run: python test_expedia_auto.py")
        print("3. Or start API server and create assessment via REST endpoint")
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        print("\n⚠️  Please fix the failed tests before proceeding")
        print("Check error messages above for details")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
