#!/usr/bin/env python
"""
Test script for assessing real GPTs from the ChatGPT store.

Usage:
    python test_real_gpt.py <GPT_ID_or_URL>

Examples:
    # Using GPT ID
    python test_real_gpt.py g-h8l4uLHFQ

    # Using full URL
    python test_real_gpt.py "https://chatgpt.com/g/g-h8l4uLHFQ-video-ai-by-invideo"

    # Test featured GPTs
    python test_real_gpt.py --featured
"""
import asyncio
import httpx
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_gpt_assessment(gpt_identifier: str, api_key: str = None):
    """Test GPT assessment"""
    base_url = "http://localhost:8000"

    # Check what testing method is configured
    use_web = os.getenv("USE_WEB_TESTING", "false").lower() == "true"
    use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"

    # Determine what to use and provide helpful messages
    if use_web:
        print(f"🎭 Using WEB-BASED TESTING (testing REAL GPT Store agent)")
        chatgpt_email = os.getenv("CHATGPT_EMAIL")
        if chatgpt_email:
            print(f"   ChatGPT Account: {chatgpt_email}")
        else:
            print("   ⚠️  No ChatGPT email set - will require manual login")
    elif use_azure:
        print(f"☁️  Using AZURE OpenAI")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if not api_key:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if api_key:
            print(f"   Endpoint: {azure_endpoint}")
            print(f"   Deployment: {azure_deployment}")
            print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("❌ Error: Azure OpenAI API key not found.")
            print("   Set AZURE_OPENAI_API_KEY in .env")
            return
    else:
        # Standard OpenAI
        print(f"🤖 Using STANDARD OpenAI API")
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("❌ Error: OpenAI API key not found.")
            print("   Set OPENAI_API_KEY in .env or pass as argument")
            print()
            print("💡 Tip: For testing real GPT Store agents, use web-based testing:")
            print("   Set USE_WEB_TESTING=true in .env")
            return

    async with httpx.AsyncClient(timeout=120.0) as client:
        print(f"\n🔍 Testing GPT: {gpt_identifier}")
        print()

        # Create assessment
        print("📝 Creating assessment...")
        assessment_data = {
            "agent_type": "openai_gpt",
            "agent_identifier": gpt_identifier,
            "assessment_level": "standard",
            "openai_api_key": api_key
        }

        try:
            response = await client.post(
                f"{base_url}/api/v1/assessments",
                json=assessment_data
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Assessment created: {result['assessment_id']}")
            print(f"   Status: {result['status']}")
            print()

            assessment_id = result["assessment_id"]

            # Poll for completion
            print("⏳ Waiting for assessment to complete...")
            max_attempts = 60  # 60 seconds
            for attempt in range(max_attempts):
                await asyncio.sleep(1)

                response = await client.get(f"{base_url}/api/v1/assessments/{assessment_id}")
                status_data = response.json()

                if status_data['status'] == 'completed':
                    print("✅ Assessment completed!")
                    print()
                    print("=" * 60)
                    print("RESULTS")
                    print("=" * 60)

                    results = status_data['results']
                    agent = results['agent']
                    score = results['score']

                    print(f"\n🤖 Agent: {agent['name']}")
                    print(f"   ID: {agent['agent_id']}")
                    print(f"   Type: {agent['agent_type']}")
                    print(f"   URL: {agent.get('source_url', 'N/A')}")

                    print(f"\n📊 AIVSS Score: {score['overall']}/100")
                    print(f"   Letter Grade: {score['grade']}")
                    print(f"   Trust Tier: Level {score['trust_tier']}")
                    print(f"   Confidence: {score['confidence']:.0%}")

                    print(f"\n📈 Dimension Scores:")
                    for dim, value in score['dimensions'].items():
                        bar = "█" * int(value / 5) + "░" * (20 - int(value / 5))
                        print(f"   {dim:15s} [{bar}] {value:.1f}/100")

                    if score['flags']:
                        print(f"\n⚠️  Flags:")
                        for flag_key, flag_msg in score['flags'].items():
                            print(f"   - {flag_msg}")

                    # Show test results
                    if 'test_results' in results and results['test_results'].get('prompt_injection'):
                        pi = results['test_results']['prompt_injection']
                        print(f"\n🧪 Prompt Injection Tests:")
                        print(f"   Total: {pi['total_tests']}")
                        print(f"   Passed: {pi['passed']} ✅")
                        print(f"   Failed: {pi['failed']} ❌")
                        print(f"   Pass Rate: {pi['pass_rate']:.0%}")
                        print(f"   Critical Findings: {pi['critical_findings']} 🚨")
                        print(f"   High Findings: {pi['high_findings']} ⚠️")

                    # Get nutrition label URL
                    print(f"\n🏷️  View full nutrition label:")
                    print(f"   HTML: {base_url}/api/v1/reports/{assessment_id}/nutrition-label")
                    print(f"   JSON: {base_url}/api/v1/reports/{assessment_id}/nutrition-label.json")
                    print()

                    return

                elif status_data['status'] == 'failed':
                    print(f"❌ Assessment failed:")
                    print(f"   Error: {status_data.get('error', 'Unknown error')}")
                    if 'traceback' in status_data:
                        print(f"\n   Traceback:\n{status_data['traceback']}")
                    return

                # Show progress
                if attempt % 5 == 0:
                    print(f"   Still running... ({attempt}s elapsed)")

            print("⏱️  Timeout waiting for assessment")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def list_featured_gpts():
    """List featured GPTs"""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/api/v1/assessments/gpts/featured")
        data = response.json()

        print("🌟 Featured GPTs from ChatGPT Store:")
        print("=" * 60)

        for i, gpt in enumerate(data['featured_gpts'], 1):
            print(f"\n{i}. {gpt['name']}")
            print(f"   ID: {gpt['id']}")
            print(f"   Category: {gpt['category']}")
            print(f"   Description: {gpt['description']}")
            print(f"   URL: {gpt['url']}")
            print(f"\n   Test with: python test_real_gpt.py {gpt['id']}")

        print("\n" + "=" * 60)


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    if sys.argv[1] == "--featured":
        await list_featured_gpts()
    else:
        gpt_identifier = sys.argv[1]
        api_key = sys.argv[2] if len(sys.argv) > 2 else None
        await test_gpt_assessment(gpt_identifier, api_key)


if __name__ == "__main__":
    asyncio.run(main())
