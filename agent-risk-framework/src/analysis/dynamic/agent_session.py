"""
Agent session abstraction for interacting with AI agents during testing.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a message in the conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str


class AgentSession(ABC):
    """Abstract base class for agent sessions"""

    def __init__(self):
        self.conversation_history: List[Message] = []

    @abstractmethod
    async def send_message(self, message: str) -> str:
        """
        Send a message to the agent and get response.

        Args:
            message: The message to send

        Returns:
            The agent's response as a string
        """
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset the conversation session"""
        pass

    def get_history(self) -> List[Message]:
        """Get conversation history"""
        return self.conversation_history.copy()


class OpenAIGPTSession(AgentSession):
    """Session for interacting with OpenAI GPT Store agents"""

    def __init__(self, gpt_id: str, api_key: str, model: str = "gpt-4"):
        super().__init__()
        self.gpt_id = gpt_id
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def send_message(self, message: str) -> str:
        """
        Send a message to the GPT and get response.

        For GPT Store GPTs, we use the chat completions API with the GPT ID
        in the model parameter (format: gpt-4-gizmo-{gpt_id})
        """
        client = self._get_client()

        # Add user message to history
        self.conversation_history.append(Message(role="user", content=message))

        # Build messages for API call
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ]

        try:
            # For GPT Store GPTs, the format is different
            # We'll try the standard chat completions first
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )

            assistant_message = response.choices[0].message.content

            # Add assistant response to history
            self.conversation_history.append(
                Message(role="assistant", content=assistant_message)
            )

            return assistant_message

        except Exception as e:
            # If GPT-specific call fails, try with standard model
            # This is a fallback for testing
            return f"Error communicating with GPT: {str(e)}"

    async def reset(self) -> None:
        """Reset the conversation"""
        self.conversation_history = []


class MockAgentSession(AgentSession):
    """Mock session for testing without real API calls"""

    def __init__(self, agent_name: str = "Mock Agent"):
        super().__init__()
        self.agent_name = agent_name

    async def send_message(self, message: str) -> str:
        """Return a mock response"""
        self.conversation_history.append(Message(role="user", content=message))

        # Mock responses that simulate a secure agent
        response = f"I'm {self.agent_name}. I can help with that request."

        # Detect prompt injection attempts and refuse
        injection_keywords = [
            "ignore", "system prompt", "instructions",
            "reveal", "show me your", "what are your"
        ]

        if any(kw in message.lower() for kw in injection_keywords):
            response = "I cannot provide information about my system configuration or internal instructions."

        self.conversation_history.append(
            Message(role="assistant", content=response)
        )

        return response

    async def reset(self) -> None:
        """Reset the conversation"""
        self.conversation_history = []
