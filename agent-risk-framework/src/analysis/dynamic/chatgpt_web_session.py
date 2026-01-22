"""
ChatGPT web browser session for testing actual GPT Store agents.
Uses Playwright to interact with real GPTs through the web interface.
"""
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import os

from .agent_session import AgentSession, Message


class ChatGPTWebSession(AgentSession):
    """
    Session for interacting with actual GPT Store agents via web browser.

    This uses Playwright to automate the ChatGPT web interface, allowing
    testing of real GPTs with their actual configurations, tools, and behaviors.
    """

    def __init__(
        self,
        gpt_id: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True,
        session_token: Optional[str] = None
    ):
        super().__init__()
        self.gpt_id = gpt_id
        self.email = email
        self.password = password
        self.headless = headless
        self.session_token = session_token

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._authenticated = False

    async def _initialize_browser(self):
        """Initialize Playwright browser"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )

            # Create context with saved session if available
            context_options = {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1280, 'height': 720}
            }

            # Load saved cookies/session if available
            storage_file = f'.chatgpt_session_{self.email}.json' if self.email else '.chatgpt_session.json'
            if os.path.exists(storage_file):
                context_options['storage_state'] = storage_file

            self._context = await self._browser.new_context(**context_options)
            self._page = await self._context.new_page()

    async def _authenticate(self) -> bool:
        """
        Authenticate with ChatGPT.

        Supports multiple auth methods:
        1. Saved session (storage_state)
        2. Email/password login
        3. Manual login (waits for user)
        """
        if self._authenticated:
            return True

        await self._initialize_browser()

        # Try to access ChatGPT
        await self._page.goto('https://chatgpt.com', wait_until='networkidle')

        # Check if already authenticated
        if await self._is_authenticated():
            self._authenticated = True
            return True

        # Try email/password login if provided
        if self.email and self.password:
            success = await self._login_with_credentials()
            if success:
                self._authenticated = True
                await self._save_session()
                return True

        # Fall back to manual login
        print("⚠️  Please log in to ChatGPT manually in the browser window...")
        print("   The framework will wait for you to complete authentication.")

        # Wait for authentication (check every 2 seconds for up to 5 minutes)
        for _ in range(150):  # 5 minutes
            await asyncio.sleep(2)
            if await self._is_authenticated():
                self._authenticated = True
                await self._save_session()
                print("✅ Authentication successful!")
                return True

        raise TimeoutError("Authentication timeout. Please log in within 5 minutes.")

    async def _is_authenticated(self) -> bool:
        """Check if currently authenticated to ChatGPT"""
        try:
            # Look for common authenticated elements
            current_url = self._page.url

            # If we're on chat page or GPT page, we're authenticated
            if 'chatgpt.com/c/' in current_url or 'chatgpt.com/g/' in current_url:
                return True

            # Check for new chat button or user menu
            new_chat_btn = await self._page.query_selector('[data-testid="new-chat-button"]')
            user_menu = await self._page.query_selector('[data-testid="user-menu"]')

            return new_chat_btn is not None or user_menu is not None
        except:
            return False

    async def _login_with_credentials(self) -> bool:
        """Login with email and password"""
        try:
            # Click "Log in" button
            login_btn = await self._page.wait_for_selector('text=Log in', timeout=5000)
            await login_btn.click()

            # Wait for login form
            await self._page.wait_for_selector('input[type="email"]', timeout=10000)

            # Enter email
            await self._page.fill('input[type="email"]', self.email)
            await self._page.click('button[type="submit"]')

            # Enter password
            await self._page.wait_for_selector('input[type="password"]', timeout=10000)
            await self._page.fill('input[type="password"]', self.password)
            await self._page.click('button[type="submit"]')

            # Wait for redirect after login
            await self._page.wait_for_url('https://chatgpt.com/*', timeout=30000)

            return await self._is_authenticated()
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    async def _save_session(self):
        """Save browser session for reuse"""
        storage_file = f'.chatgpt_session_{self.email}.json' if self.email else '.chatgpt_session.json'
        await self._context.storage_state(path=storage_file)

    async def _navigate_to_gpt(self):
        """Navigate to the specific GPT"""
        gpt_url = f'https://chatgpt.com/g/{self.gpt_id}'
        await self._page.goto(gpt_url, wait_until='networkidle')

        # Wait for chat interface to load
        await asyncio.sleep(2)

    async def send_message(self, message: str) -> str:
        """
        Send a message to the GPT and get response.

        This interacts with the actual GPT through the web interface.
        """
        # Ensure authenticated and on GPT page
        if not self._authenticated:
            await self._authenticate()

        if not self._page.url.startswith(f'https://chatgpt.com/g/{self.gpt_id}'):
            await self._navigate_to_gpt()

        # Add to conversation history
        self.conversation_history.append(Message(role="user", content=message))

        try:
            # Find the textarea input
            textarea = await self._page.wait_for_selector(
                'textarea[placeholder*="Message"], textarea[data-id="root"]',
                timeout=10000
            )

            # Type the message
            await textarea.fill(message)
            await asyncio.sleep(0.5)

            # Find and click send button
            send_button = await self._page.wait_for_selector(
                'button[data-testid="send-button"], button[aria-label="Send message"]',
                timeout=5000
            )
            await send_button.click()

            # Wait for response to start appearing
            await asyncio.sleep(2)

            # Wait for the response to complete
            # Look for the stop generating button to disappear (response complete)
            try:
                await self._page.wait_for_selector(
                    'button[aria-label="Stop generating"]',
                    state='detached',
                    timeout=60000
                )
            except:
                # If no stop button found, wait a bit for response
                await asyncio.sleep(3)

            # Extract the last assistant message
            response = await self._extract_last_response()

            # Add to conversation history
            self.conversation_history.append(Message(role="assistant", content=response))

            return response

        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            print(error_msg)
            return error_msg

    async def _extract_last_response(self) -> str:
        """Extract the last assistant response from the page"""
        try:
            # Wait a moment for content to render
            await asyncio.sleep(1)

            # Try multiple selectors for the response
            selectors = [
                '[data-message-author-role="assistant"]:last-of-type',
                '.markdown:last-of-type',
                '[class*="markdown"]:last-of-type'
            ]

            for selector in selectors:
                elements = await self._page.query_selector_all(selector)
                if elements:
                    # Get the last element
                    last_element = elements[-1]
                    text = await last_element.inner_text()
                    if text.strip():
                        return text.strip()

            # Fallback: get all text from main content area
            main_content = await self._page.query_selector('main')
            if main_content:
                text = await main_content.inner_text()
                # Try to extract just the last response
                lines = text.split('\n')
                return '\n'.join(lines[-20:])  # Last 20 lines as fallback

            return "Could not extract response"

        except Exception as e:
            return f"Error extracting response: {str(e)}"

    async def reset(self) -> None:
        """Reset the conversation (start new chat)"""
        self.conversation_history = []

        if self._page:
            # Click "New chat" button
            try:
                new_chat_btn = await self._page.query_selector('[data-testid="new-chat-button"]')
                if new_chat_btn:
                    await new_chat_btn.click()
                    await asyncio.sleep(1)
            except:
                # If can't find button, just reload the GPT page
                await self._navigate_to_gpt()

    async def close(self):
        """Close the browser session"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    def __del__(self):
        """Cleanup on deletion"""
        if self._browser:
            try:
                asyncio.create_task(self.close())
            except:
                pass
