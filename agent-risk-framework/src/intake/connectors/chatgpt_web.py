"""
ChatGPT Web connector for testing actual GPT Store agents via browser automation.
"""
import re
from typing import Optional

from ..models import AgentMetadata, AgentType
from ...analysis.dynamic.chatgpt_web_session import ChatGPTWebSession


class ChatGPTWebConnector:
    """
    Connector for testing actual GPT Store agents via web browser.

    This enables testing of real GPTs with their actual:
    - Custom instructions/system prompts
    - Tools and actions
    - Knowledge files
    - Conversation behaviors
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True
    ):
        self.email = email
        self.password = password
        self.headless = headless

    @staticmethod
    def parse_gpt_identifier(identifier: str) -> str:
        """
        Parse GPT identifier from various formats.
        Reuses the same parsing logic as OpenAIGPTConnector.
        """
        # If it's already a GPT ID (starts with g- and is short)
        if identifier.startswith("g-") and len(identifier) < 20:
            return identifier

        # If it's a URL, extract the GPT ID
        if "chatgpt.com" in identifier or "chat.openai.com" in identifier:
            # Pattern: /g/g-{id}-{optional-name} or /g/g-{id}
            match = re.search(r'/g/(g-[a-zA-Z0-9]+)', identifier)
            if match:
                return match.group(1)

        # Try to extract anything that looks like a GPT ID
        match = re.search(r'(g-[a-zA-Z0-9]+)', identifier)
        if match:
            return match.group(1)

        raise ValueError(
            f"Could not parse GPT ID from identifier: {identifier}. "
            f"Expected format: 'g-xxxxx' or 'https://chatgpt.com/g/g-xxxxx'"
        )

    async def fetch_metadata(self, identifier: str) -> AgentMetadata:
        """
        Fetch metadata for a GPT.

        For web-based testing, we can only get basic info from the URL/ID.
        More detailed metadata would require scraping the GPT page.
        """
        gpt_id = self.parse_gpt_identifier(identifier)

        # Extract name from URL if provided
        name = self._extract_name_from_identifier(identifier, gpt_id)

        metadata = AgentMetadata(
            agent_id=gpt_id,
            name=name,
            version="1.0.0",
            developer="OpenAI GPT Store",
            description=f"Real GPT Store agent (ID: {gpt_id}) - tested via web browser",
            agent_type=AgentType.OPENAI_GPT,
            source_url=f"https://chatgpt.com/g/{gpt_id}",
            model_backend="gpt-4 (web)",
            tools=[],  # Would need page scraping to get actual tools
            external_apis=[],
            framework="OpenAI GPTs (Web)",
            framework_version="1.0"
        )

        return metadata

    def _extract_name_from_identifier(self, identifier: str, gpt_id: str) -> str:
        """Extract human-readable name from URL or default to ID"""
        if "chatgpt.com" in identifier:
            # Try to extract name from URL pattern /g/g-{id}-{name}
            match = re.search(r'/g/g-[a-zA-Z0-9]+-(.+?)(?:\?|$)', identifier)
            if match:
                name_slug = match.group(1)
                # Convert slug to title (replace - with space, capitalize)
                name = name_slug.replace('-', ' ').title()
                return name

        return f"GPT-{gpt_id}"

    async def create_session(self, identifier: str) -> ChatGPTWebSession:
        """
        Create a web browser session for interacting with the GPT.

        This creates a real browser that navigates to the GPT and
        sends messages through the actual ChatGPT interface.

        Args:
            identifier: GPT ID or URL

        Returns:
            ChatGPTWebSession instance
        """
        gpt_id = self.parse_gpt_identifier(identifier)

        return ChatGPTWebSession(
            gpt_id=gpt_id,
            email=self.email,
            password=self.password,
            headless=self.headless
        )
