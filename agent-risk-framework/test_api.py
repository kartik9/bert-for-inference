#!/usr/bin/env python
"""Quick test script to verify API functionality"""
import asyncio
import httpx

async def test_api():
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health: {response.json()}")

        # Create assessment
        print("\nCreating assessment...")
        assessment_data = {
            "agent_type": "openai_gpt",
            "agent_identifier": "test-agent-demo",
            "assessment_level": "standard"
        }
        response = await client.post(
            f"{base_url}/api/v1/assessments",
            json=assessment_data
        )
        result = response.json()
        print(f"Assessment created: {result}")

        assessment_id = result["assessment_id"]

        # Wait a moment for background task
        await asyncio.sleep(1)

        # Get assessment status
        print(f"\nGetting assessment status for {assessment_id}...")
        response = await client.get(f"{base_url}/api/v1/assessments/{assessment_id}")
        status = response.json()
        print(f"Status: {status['status']}")

        if status['status'] == 'completed':
            print(f"\nResults: {status['results']['score']}")

            # Get nutrition label
            print("\nGetting nutrition label...")
            response = await client.get(
                f"{base_url}/api/v1/reports/{assessment_id}/nutrition-label"
            )
            print(f"HTML label length: {len(response.text)} characters")
            print("\n✅ All API tests passed!")
        else:
            print(f"⚠️  Assessment not yet completed: {status['status']}")

if __name__ == "__main__":
    asyncio.run(test_api())
