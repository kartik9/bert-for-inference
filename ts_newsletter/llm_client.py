"""
LLM Client for GPT-5 Responses API
Wrapper around OpenAI's new Responses API with agent-friendly interface
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI, AzureOpenAI


@dataclass
class Tool:
    """Tool definition for agent function calling"""
    type: str  # "function" or "web_search", "code_interpreter", etc.
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAI Responses API format"""
        if self.type == "function":
            # Responses API uses internally-tagged format
            return {
                "type": "function",
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        else:
            # Built-in tools (web_search, etc.)
            return {"type": self.type}


@dataclass
class Message:
    """Message in conversation"""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class ToolCall:
    """Tool call made by the model"""
    id: str
    type: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ResponseOutput:
    """Output from Responses API"""
    id: str
    text: str
    reasoning_summary: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_output: List[Dict[str, Any]] = field(default_factory=list)
    previous_response_id: Optional[str] = None


class LLMClient:
    """
    Client for GPT-5 Responses API

    Provides a clean interface for agents to interact with GPT-5
    using the new Responses API primitives.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        store: bool = True,
        azure_endpoint: Optional[str] = None,
        azure_api_version: Optional[str] = None
    ):
        """
        Initialize LLM client

        Args:
            api_key: OpenAI or Azure OpenAI API key
            model: Model name or Azure deployment name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            store: Whether to store conversations (enables previous_response_id)
            azure_endpoint: Azure OpenAI endpoint (if using Azure)
            azure_api_version: Azure OpenAI API version (if using Azure)
        """
        # Initialize appropriate client based on configuration
        if azure_endpoint:
            # Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=azure_api_version or "2024-02-15-preview",
                azure_endpoint=azure_endpoint
            )
        else:
            # Standard OpenAI client
            self.client = OpenAI(api_key=api_key)

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.store = store

    def generate(
        self,
        input: Union[str, List[Message]],
        instructions: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        previous_response_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ResponseOutput:
        """
        Generate response from GPT-5

        Args:
            input: User input (string or list of messages)
            instructions: System-level instructions (optional)
            tools: List of tools available to the model
            previous_response_id: ID of previous response for multi-turn
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            ResponseOutput containing generated text and metadata
        """
        # Prepare input
        if isinstance(input, list):
            # Convert Message objects to dicts
            input_data = [{"role": msg.role, "content": msg.content} for msg in input]
        else:
            input_data = input

        # Prepare request parameters
        request_params = {
            "model": self.model,
            "input": input_data,
            "store": self.store,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens
        }

        # Add instructions if provided
        if instructions:
            request_params["instructions"] = instructions

        # Add tools if provided
        if tools:
            request_params["tools"] = [tool.to_dict() for tool in tools]

        # Add previous response for multi-turn
        if previous_response_id:
            request_params["previous_response_id"] = previous_response_id

        # Make API call
        response = self.client.responses.create(**request_params)

        # Parse response
        return self._parse_response(response)

    def _parse_response(self, response) -> ResponseOutput:
        """
        Parse response from Responses API

        The response.output is a list of items that can include:
        - reasoning items (type: "reasoning")
        - message items (type: "message")
        - function call items (type: "function_call")
        - function output items (type: "function_call_output")
        """
        output_text = ""
        reasoning_summary = None
        tool_calls = []
        raw_output = []

        # Iterate through output items
        for item in response.output:
            raw_output.append(item.model_dump() if hasattr(item, 'model_dump') else item)

            if item.type == "reasoning":
                # Extract reasoning summary
                if hasattr(item, 'summary') and item.summary:
                    reasoning_summary = " ".join(item.summary)

            elif item.type == "message":
                # Extract text content from message
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if content_item.get("type") == "output_text":
                            output_text += content_item.get("text", "")

            elif item.type == "function_call":
                # Extract tool calls
                tool_call = ToolCall(
                    id=item.id,
                    type="function",
                    name=item.name,
                    arguments=json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments
                )
                tool_calls.append(tool_call)

        # Use helper if available
        if hasattr(response, 'output_text') and not output_text:
            output_text = response.output_text

        return ResponseOutput(
            id=response.id,
            text=output_text,
            reasoning_summary=reasoning_summary,
            tool_calls=tool_calls,
            raw_output=raw_output,
            previous_response_id=getattr(response, 'previous_response_id', None)
        )

    def generate_with_context(
        self,
        user_message: str,
        conversation_history: List[Message],
        instructions: Optional[str] = None,
        tools: Optional[List[Tool]] = None
    ) -> ResponseOutput:
        """
        Generate response with full conversation context

        Args:
            user_message: Current user message
            conversation_history: List of previous messages
            instructions: System instructions
            tools: Available tools

        Returns:
            ResponseOutput
        """
        # Combine history with new message
        full_context = conversation_history + [Message(role="user", content=user_message)]

        return self.generate(
            input=full_context,
            instructions=instructions,
            tools=tools
        )


class LLMClientFactory:
    """Factory for creating LLM clients from configuration"""

    @staticmethod
    def create(config, agent_name: Optional[str] = None) -> LLMClient:
        """
        Create LLM client instance

        Args:
            config: Config object from config_loader
            agent_name: Optional agent name to get agent-specific model

        Returns:
            LLMClient instance
        """
        # Get model for specific agent or use default
        if agent_name:
            model = config.get_agent_model(agent_name)
        else:
            model = config.llm.model

        # Check if using Azure OpenAI
        if config.llm.provider == "azure_openai":
            return LLMClient(
                api_key=config.llm.azure_api_key,
                model=model,  # Azure uses deployment names
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                store=config.llm.store_conversations,
                azure_endpoint=config.llm.azure_endpoint,
                azure_api_version=config.llm.azure_api_version
            )
        else:
            # Standard OpenAI
            return LLMClient(
                api_key=config.llm.api_key,
                model=model,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                store=config.llm.store_conversations
            )


# Example usage:
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config

    # Load config
    config = get_config()

    # Create client
    client = LLMClientFactory.create(config)

    # Simple generation
    response = client.generate(
        input="What is advertising fraud?",
        instructions="You are an expert in advertising security."
    )

    print(f"Response: {response.text}")
    print(f"Response ID: {response.id}")

    # Multi-turn conversation
    response2 = client.generate(
        input="What are common techniques?",
        previous_response_id=response.id
    )

    print(f"\nFollow-up: {response2.text}")

    # With tools
    weather_tool = Tool(
        type="function",
        name="get_weather",
        description="Get current weather",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    )

    response3 = client.generate(
        input="What's the weather in Seattle?",
        tools=[weather_tool]
    )

    print(f"\nWith tools: {response3.text}")
    if response3.tool_calls:
        print(f"Tool calls: {response3.tool_calls}")
