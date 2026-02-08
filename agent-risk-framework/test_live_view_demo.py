#!/usr/bin/env python3
"""
Simple demo of browser-use cloud live session viewing.

This script creates a browser-use session and displays the live URL
so you can watch the agent in real-time as it navigates and interacts.

Requirements:
- BROWSER_USE_API_KEY set in environment or .env file
- browser-use library installed: pip install browser-use
"""

import asyncio
import os
import sys

# Set API key
os.environ['BROWSER_USE_API_KEY'] = os.getenv('BROWSER_USE_API_KEY', 'bu_zAGkEOM6lGgZrPKfrxSyZeK1tBgY2mlHC-j7uSTnG0o')

from browser_use import Agent, Browser, ChatBrowserUse


def display_live_url(browser=None, agent=None):
    """Extract and display live session URL for real-time viewing"""
    try:
        from urllib.parse import quote

        live_url = None
        # Primary method: compute from cdp_url (how browser-use does it internally)
        b = browser or (agent.browser if agent and hasattr(agent, 'browser') else None)
        if b and hasattr(b, 'cdp_url') and b.cdp_url:
            live_url = f'https://live.browser-use.com?wss={quote(b.cdp_url, safe="")}'

        if live_url:
            print("\n" + "=" * 80)
            print("📺 LIVE SESSION VIEW - OPEN NOW TO WATCH!")
            print("=" * 80)
            print(f"\n🔗 {live_url}")
            print("\n👁️  COPY AND OPEN THIS URL IN YOUR BROWSER NOW!")
            print("   You'll see the browser session in real-time as the agent works.")
            print("\n   What you'll see:")
            print("   - The actual browser window")
            print("   - Mouse movements and clicks")
            print("   - Text being typed")
            print("   - Pages loading")
            print("   - All interactions happening live!")
            print("\n" + "=" * 80 + "\n")
            return live_url
        else:
            print("\n💡 Live URL will be available once the session starts...")

    except Exception as e:
        print(f"\n⚠️  Note: Could not extract live URL ({e})")

    return None


async def demo_live_view():
    """Demo of live session viewing"""
    print("=" * 80)
    print("🎥 BROWSER-USE LIVE SESSION VIEWING DEMO")
    print("=" * 80)
    print("\nThis demo will:")
    print("1. Create a browser-use cloud session")
    print("2. Display the live viewing URL")
    print("3. Navigate to a website so you can watch it happen")
    print("\n" + "=" * 80)

    # Initialize
    print("\n📦 Initializing browser-use cloud...")
    browser = Browser()
    llm = ChatBrowserUse()
    print("✅ Cloud browser initialized")

    # Try to get live URL from browser
    live_url = display_live_url(browser=browser)

    # Create a simple task
    print("\n" + "=" * 80)
    print("🧪 DEMO TASK: Navigate to Wikipedia and Search")
    print("=" * 80)

    task = """
    Navigate to https://en.wikipedia.org

    Wait for the page to load.

    Find the search box and search for "Artificial Intelligence"

    Wait for the results page to load.

    Return a brief summary of what you found (first paragraph of the article).
    """

    print("\n📤 Creating agent with task...")
    print("   Task: Search Wikipedia for 'Artificial Intelligence'")

    agent = Agent(task=task, llm=llm, browser=browser)

    # Try to get live URL from agent
    if not live_url:
        live_url = display_live_url(browser=browser, agent=agent)

    if live_url:
        print("\n⏳ AGENT STARTING NOW - OPEN THE LIVE URL TO WATCH!")
        print(f"   🔗 {live_url}")
        print("\n   You should see:")
        print("   1. Browser navigating to Wikipedia")
        print("   2. Search box being located")
        print("   3. Text 'Artificial Intelligence' being typed")
        print("   4. Search being submitted")
        print("   5. Results page loading")
        print("\n" + "=" * 80)

        # Give user time to open the URL
        await asyncio.sleep(5)

    print("\n⏳ Agent running (this may take 30-60 seconds)...")

    try:
        history = await agent.run()

        # Extract result
        if hasattr(history, 'final_result'):
            result = str(history.final_result())
        elif hasattr(history, '__iter__'):
            result = str(list(history)[-1] if list(history) else history)
        else:
            result = str(history)

        print("\n" + "=" * 80)
        print("✅ TASK COMPLETED")
        print("=" * 80)
        print("\nResult:")
        print("-" * 80)
        print(result[:500])
        if len(result) > 500:
            print("...")
        print("-" * 80)

        print("\n" + "=" * 80)
        print("🎉 DEMO COMPLETE!")
        print("=" * 80)
        print("\n✅ You should have seen the browser automation happen live!")
        print("✅ This is the same technology used to test GPT Store agents")
        print("\n💡 Use this live viewing to:")
        print("   - Debug test failures")
        print("   - Verify agent behavior")
        print("   - Record demonstrations")
        print("   - Monitor security tests")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 STARTING LIVE VIEW DEMO")
    print("=" * 80)

    api_key = os.getenv('BROWSER_USE_API_KEY')
    if not api_key:
        print("\n❌ ERROR: BROWSER_USE_API_KEY not found")
        print("\nPlease set your API key:")
        print("  export BROWSER_USE_API_KEY=your-key-here")
        print("\nOr add to .env file:")
        print("  BROWSER_USE_API_KEY=your-key-here")
        sys.exit(1)

    print(f"\n🔑 API Key: {api_key[:20]}...")
    print("☁️  Using browser-use cloud service")

    try:
        result = asyncio.run(demo_live_view())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
