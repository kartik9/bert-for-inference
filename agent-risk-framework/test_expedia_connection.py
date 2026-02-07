#!/usr/bin/env python3
"""
Test script to verify end-to-end connection with real Expedia GPT.
This will test:
1. Browser initialization
2. Authentication (manual login required)
3. Sending a real prompt to Expedia GPT
4. Receiving real response
5. Verifying no bot blockers
"""

import asyncio
import sys
from src.intake.connectors.chatgpt_web import ChatGPTWebConnector
from src.analysis.dynamic.suites.prompt_injection import PromptInjectionSuite

# Expedia GPT ID
EXPEDIA_GPT_ID = "g-68d8ecbe98388191bd93f6b1d03158bf"

async def test_basic_connection():
    """Test basic connection with a simple, safe prompt"""
    print("=" * 80)
    print("🧪 TEST 1: Basic Connection to Expedia GPT")
    print("=" * 80)

    connector = ChatGPTWebConnector(
        email=None,  # Will use manual login
        password=None,
        headless=False  # Show browser for manual login
    )

    try:
        print(f"\n📋 Testing GPT: {EXPEDIA_GPT_ID}")
        print("🌐 Creating browser session...")

        session = await connector.create_session(EXPEDIA_GPT_ID)

        print("✅ Browser session created")
        print("⏳ Please log in to ChatGPT in the browser window if prompted...")
        print("   The test will continue automatically after login.\n")

        # Test with a simple travel query
        test_prompt = "I'm looking for hotels in Paris for 2 nights in March. Can you help?"

        print(f"📤 Sending test prompt: '{test_prompt}'")
        response = await session.send_message(test_prompt)

        print("\n" + "=" * 80)
        print("✅ SUCCESS: Received response from Expedia GPT!")
        print("=" * 80)
        print(f"\n📥 Response preview (first 500 chars):")
        print("-" * 80)
        print(response[:500])
        print("-" * 80)

        # Verify response is not empty and not an error
        if not response or len(response) < 10:
            print("\n❌ ERROR: Response is too short or empty")
            return False

        if "error" in response.lower() or "blocked" in response.lower():
            print("\n⚠️  WARNING: Response may indicate an error or block")
            print(f"Full response: {response}")
            return False

        print("\n✅ Response appears valid!")
        print("✅ No bot blockers detected!")

        await session.close()
        return True

    except Exception as e:
        print(f"\n❌ ERROR during basic connection test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prompt_injection():
    """Test with actual prompt injection attacks"""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Prompt Injection Test Suite")
    print("=" * 80)

    connector = ChatGPTWebConnector(
        email=None,
        password=None,
        headless=False
    )

    try:
        print(f"\n📋 Testing GPT: {EXPEDIA_GPT_ID}")
        print("🌐 Creating browser session...")

        session = await connector.create_session(EXPEDIA_GPT_ID)

        print("✅ Browser session created")
        print("🔒 Running prompt injection test suite...\n")

        # Initialize test suite
        pi_suite = PromptInjectionSuite()
        await pi_suite.load_test_cases()

        print(f"📊 Loaded {len(pi_suite.test_cases)} test cases")
        print("⏳ Running tests (this may take a few minutes)...\n")

        # Run the suite
        results = await pi_suite.run(session)

        print("\n" + "=" * 80)
        print("✅ TEST SUITE COMPLETED!")
        print("=" * 80)
        print(f"\n📊 Results Summary:")
        print(f"   Total tests: {results.total_tests}")
        print(f"   Passed: {results.passed_tests}")
        print(f"   Failed: {results.failed_tests}")
        print(f"   Pass rate: {results.pass_rate:.1f}%")
        print(f"\n   Critical findings: {len(results.critical_findings)}")
        print(f"   High findings: {len(results.high_findings)}")
        print(f"   Medium findings: {len(results.medium_findings)}")
        print(f"   Low findings: {len(results.low_findings)}")

        # Show some sample results
        if results.test_results:
            print(f"\n📋 Sample Test Results:")
            print("-" * 80)
            for i, test_result in enumerate(results.test_results[:3]):
                print(f"\n{i+1}. {test_result.test_name}")
                print(f"   Status: {'✅ PASSED' if test_result.passed else '❌ FAILED'}")
                print(f"   Severity: {test_result.severity}")
                if test_result.vulnerability_found:
                    print(f"   ⚠️  Vulnerability found!")
                print(f"   Response preview: {test_result.agent_response[:100]}...")

        await session.close()
        return True

    except Exception as e:
        print(f"\n❌ ERROR during prompt injection test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 EXPEDIA GPT END-TO-END TESTING")
    print("=" * 80)
    print("\nThis script will test the AI Agent Risk Assessment Framework")
    print("against the REAL Expedia GPT from the ChatGPT Store.\n")
    print("⚠️  IMPORTANT: You will need to log in to ChatGPT manually")
    print("   when the browser window opens.\n")

    input("Press Enter to continue...")

    # Test 1: Basic connection
    test1_passed = await test_basic_connection()

    if not test1_passed:
        print("\n❌ Basic connection test failed. Stopping.")
        return 1

    print("\n" + "=" * 80)
    input("\n✅ Test 1 passed! Press Enter to continue to Test 2 (Prompt Injection)...")

    # Test 2: Prompt injection suite
    test2_passed = await test_prompt_injection()

    if not test2_passed:
        print("\n❌ Prompt injection test failed.")
        return 1

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
    print("\n✅ Framework is working with real Expedia GPT")
    print("✅ Can send real prompts and receive real responses")
    print("✅ No bot blockers detected")
    print("✅ Prompt injection test suite executed successfully")
    print("\n🚀 Ready to proceed with full assessments!")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
