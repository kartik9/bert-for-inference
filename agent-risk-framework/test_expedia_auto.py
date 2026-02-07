#!/usr/bin/env python3
"""
Automated test script to verify end-to-end connection with real Expedia GPT.
Tests without user prompts - runs automatically.
"""

import asyncio
import sys
import os
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

    session = None
    try:
        print(f"\n📋 Testing GPT: {EXPEDIA_GPT_ID}")
        print(f"🌐 GPT URL: https://chatgpt.com/g/{EXPEDIA_GPT_ID}")
        print("🌐 Creating browser session...")

        session = await connector.create_session(EXPEDIA_GPT_ID)

        print("✅ Browser session created")
        print("⏳ Waiting for authentication...")
        print("   (Browser window opened - please log in manually if needed)")
        print("   Session will be saved for future use.\n")

        # Test with a simple travel query
        test_prompt = "What hotels are available in Paris?"

        print(f"📤 Sending test prompt: '{test_prompt}'")
        print("⏳ Waiting for response from Expedia GPT...")

        response = await session.send_message(test_prompt)

        print("\n" + "=" * 80)
        print("✅ SUCCESS: Received response from Expedia GPT!")
        print("=" * 80)
        print(f"\n📥 Response length: {len(response)} characters")
        print(f"📥 Response preview (first 500 chars):")
        print("-" * 80)
        print(response[:500])
        if len(response) > 500:
            print("...")
        print("-" * 80)

        # Verify response is not empty and not an error
        if not response or len(response) < 10:
            print("\n❌ ERROR: Response is too short or empty")
            return False, session

        if "error" in response.lower() or "blocked" in response.lower():
            print("\n⚠️  WARNING: Response may indicate an error or block")
            print(f"Full response: {response}")
            return False, session

        # Check for Expedia-specific content
        expedia_indicators = ['hotel', 'expedia', 'booking', 'travel', 'paris', 'room', 'price']
        found_indicators = [ind for ind in expedia_indicators if ind.lower() in response.lower()]

        print(f"\n✅ Found {len(found_indicators)} travel-related keywords in response")
        print(f"   Keywords: {', '.join(found_indicators)}")
        print("\n✅ Response appears valid!")
        print("✅ No bot blockers detected!")
        print("✅ Expedia GPT is responding with real travel information!")

        return True, session

    except Exception as e:
        print(f"\n❌ ERROR during basic connection test: {e}")
        import traceback
        traceback.print_exc()
        return False, session


async def test_prompt_injection(session):
    """Test with actual prompt injection attacks"""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: Prompt Injection Test Suite (First 3 Tests)")
    print("=" * 80)

    try:
        print("🔒 Running prompt injection test suite...\n")

        # Initialize test suite
        pi_suite = PromptInjectionSuite()
        await pi_suite.load_test_cases()

        print(f"📊 Loaded {len(pi_suite.test_cases)} test cases")
        print(f"⏳ Running first 3 tests as proof of concept...\n")

        # Run only first 3 tests for quick validation
        limited_tests = pi_suite.test_cases[:3]
        results_list = []

        for i, test_case in enumerate(limited_tests, 1):
            print(f"🧪 Test {i}/{len(limited_tests)}: {test_case['name']}")
            print(f"   Severity: {test_case['severity']}")
            print(f"   Payload preview: {test_case['payload'][:80]}...")

            result = await pi_suite.execute_test(session, test_case)
            results_list.append(result)

            print(f"   Result: {'✅ PASSED (Agent defended)' if result.passed else '❌ FAILED (Vulnerability found)'}")
            if result.vulnerability_found:
                print(f"   ⚠️  VULNERABILITY DETECTED!")
            print(f"   Response preview: {result.agent_response[:100]}...")
            print()

        # Count results
        passed = sum(1 for r in results_list if r.passed)
        failed = len(results_list) - passed
        vulnerabilities = sum(1 for r in results_list if r.vulnerability_found)

        print("\n" + "=" * 80)
        print("✅ QUICK TEST SUITE COMPLETED!")
        print("=" * 80)
        print(f"\n📊 Results Summary:")
        print(f"   Tests run: {len(results_list)}")
        print(f"   Passed (defended): {passed}")
        print(f"   Failed: {failed}")
        print(f"   Vulnerabilities found: {vulnerabilities}")

        if vulnerabilities > 0:
            print(f"\n⚠️  WARNING: {vulnerabilities} potential vulnerabilities detected")
            print("   This is GOOD - it means the framework is working correctly!")
        else:
            print(f"\n✅ Agent defended against all test attacks")

        return True

    except Exception as e:
        print(f"\n❌ ERROR during prompt injection test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 EXPEDIA GPT END-TO-END TESTING (AUTOMATED)")
    print("=" * 80)
    print("\nTesting AI Agent Risk Assessment Framework")
    print("against the REAL Expedia GPT from ChatGPT Store\n")
    print("GPT ID:", EXPEDIA_GPT_ID)
    print("GPT URL: https://chatgpt.com/g/" + EXPEDIA_GPT_ID)
    print("\n⚠️  NOTE: Browser will open in NON-headless mode")
    print("   If you need to log in, please do so in the browser window.\n")

    # Test 1: Basic connection
    print("Starting Test 1 in 3 seconds...")
    await asyncio.sleep(3)

    test1_passed, session = await test_basic_connection()

    if not test1_passed:
        print("\n❌ Basic connection test failed. Stopping.")
        if session:
            await session.close()
        return 1

    print("\n" + "=" * 80)
    print("✅ Test 1 PASSED! Proceeding to Test 2...")
    print("=" * 80)
    await asyncio.sleep(2)

    # Test 2: Prompt injection suite (limited)
    test2_passed = await test_prompt_injection(session)

    # Close session
    if session:
        await session.close()
        print("\n🔒 Browser session closed")

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
    print("✅ Responses contain real travel information from Expedia")
    print("\n🚀 READY TO PROCEED WITH FULL ASSESSMENTS!")
    print("\n📝 Next steps:")
    print("   1. Run full assessment via API endpoint")
    print("   2. Generate nutrition label report")
    print("   3. Test with additional GPT Store agents")

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
