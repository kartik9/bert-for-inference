"""
OpenAI GPT Store connector for fetching and testing GPTs.
"""
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from ..models import AgentMetadata, AgentType, ToolDefinition, ToolCapability
from ...analysis.dynamic.agent_session import OpenAIGPTSession, AzureOpenAIGPTSession


class OpenAIGPTConnector:
    """Connector for OpenAI GPT Store agents (supports both standard and Azure OpenAI)"""

    def __init__(
        self,
        api_key: str,
        use_azure: bool = False,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        azure_api_version: str = "2024-02-15-preview"
    ):
        self.api_key = api_key
        self.use_azure = use_azure
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.azure_api_version = azure_api_version

        # Validate Azure configuration if Azure is enabled
        if self.use_azure:
            if not self.azure_endpoint:
                raise ValueError("azure_endpoint is required when use_azure=True")
            if not self.azure_deployment:
                raise ValueError("azure_deployment is required when use_azure=True")

    @staticmethod
    def parse_gpt_identifier(identifier: str) -> str:
        """
        Parse GPT identifier from various formats:
        - GPT ID: "g-h8l4uLHFQ"
        - Full URL: "https://chatgpt.com/g/g-h8l4uLHFQ-video-ai-by-invideo"
        - Short URL: "chatgpt.com/g/g-abc123"

        Returns:
            The GPT ID (e.g., "g-h8l4uLHFQ")
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

        Note: OpenAI doesn't provide a public API to fetch GPT Store metadata.
        This implementation creates basic metadata from the identifier.

        For more detailed metadata, you would need to:
        1. Use web scraping to get GPT description, tools, etc.
        2. Or manually provide metadata via config files

        Args:
            identifier: GPT ID, URL, or identifier

        Returns:
            AgentMetadata with available information
        """
        gpt_id = self.parse_gpt_identifier(identifier)

        # Extract name from URL if provided
        name = self._extract_name_from_identifier(identifier, gpt_id)

        # Create basic metadata
        # In a real implementation, you might scrape the GPT page or use additional APIs
        metadata = AgentMetadata(
            agent_id=gpt_id,
            name=name,
            version="1.0.0",
            developer="OpenAI GPT Store",
            description=f"GPT from OpenAI GPT Store (ID: {gpt_id})",
            agent_type=AgentType.OPENAI_GPT,
            source_url=f"https://chatgpt.com/g/{gpt_id}",
            model_backend="gpt-4",
            tools=[],  # Would need scraping or API to get actual tools
            external_apis=[],
            framework="OpenAI GPTs",
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

    async def create_session(self, identifier: str, model: str = "gpt-4"):
        """
        Create a session for interacting with the GPT.

        Args:
            identifier: GPT ID or URL
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.) - ignored for Azure

        Returns:
            OpenAIGPTSession or AzureOpenAIGPTSession instance
        """
        gpt_id = self.parse_gpt_identifier(identifier)

        if self.use_azure:
            return AzureOpenAIGPTSession(
                gpt_id=gpt_id,
                azure_endpoint=self.azure_endpoint,
                api_key=self.api_key,
                deployment=self.azure_deployment,
                api_version=self.azure_api_version
            )
        else:
            return OpenAIGPTSession(
                gpt_id=gpt_id,
                api_key=self.api_key,
                model=model
            )

    async def fetch_gpt_details_from_web(self, identifier: str) -> Dict[str, Any]:
        """
        Fetch GPT details from the web page (requires web scraping).

        This is a placeholder for future implementation using:
        - httpx to fetch the page
        - BeautifulSoup or similar to parse HTML
        - Extract: name, description, tools, capabilities

        Args:
            identifier: GPT ID or URL

        Returns:
            Dictionary with GPT details
        """
        gpt_id = self.parse_gpt_identifier(identifier)
        url = f"https://chatgpt.com/g/{gpt_id}"

        # TODO: Implement web scraping
        # For now, return basic info
        return {
            "gpt_id": gpt_id,
            "url": url,
            "name": self._extract_name_from_identifier(identifier, gpt_id),
            "description": "Description not available (web scraping not implemented)",
            "tools": [],
            "capabilities": []
        }


# Example usage and helper functions

def get_featured_gpts() -> list[Dict[str, str]]:
    """
    Get a list of featured GPTs from ChatGPT store.

    In a production system, this would scrape or use an API.
    For now, returns a curated list.
    """
    return [
        {
            "name": "Video AI by invideo",
            "id": "g-h8l4uLHFQ",
            "url": "https://chatgpt.com/g/g-h8l4uLHFQ-video-ai-by-invideo",
            "description": "AI video maker - generate engaging videos with voiceovers",
            "category": "Creative"
        },
        {
            "name": "Canva",
            "id": "g-alKfVrz9K",
            "url": "https://chatgpt.com/g/g-alKfVrz9K-canva",
            "description": "Effortlessly design anything: presentations, logos, social media posts",
            "category": "Design"
        },
        {
            "name": "Scholar AI",
            "id": "g-L2HknCZTC",
            "url": "https://chatgpt.com/g/g-L2HknCZTC-scholar-ai",
            "description": "AI Research Assistant - search 200M+ scientific papers",
            "category": "Research"
        },
        {
            "name": "Expedia",
            "id": "g-EMMA4q6qv",
            "url": "https://chatgpt.com/g/g-EMMA4q6qv-expedia",
            "description": "Trip planning assistant",
            "category": "Travel"
        }
    ]
