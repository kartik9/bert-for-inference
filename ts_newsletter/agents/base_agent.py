"""
Base Agent Class
Foundation for all specialized agents with tool-use capabilities
"""

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ts_newsletter.llm_client import LLMClient, Message, ResponseOutput, Tool


@dataclass
class AgentAction:
    """Record of an agent action"""
    action_id: str
    timestamp: datetime
    action_type: str  # "thought", "tool_call", "observation", "decision"
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None


@dataclass
class AgentTrace:
    """Complete trace of agent execution"""
    agent_name: str
    agent_type: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    actions: List[AgentAction] = field(default_factory=list)
    final_output: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agents

    Implements ReAct pattern: Reasoning + Acting
    - Agents reason about tasks using LLM
    - Agents can call tools to gather information
    - Agents iterate until task completion
    """

    def __init__(
        self,
        agent_name: str,
        agent_type: str,
        llm_client: LLMClient,
        config: Any,
        max_iterations: int = 10
    ):
        """
        Initialize base agent

        Args:
            agent_name: Unique name for this agent instance
            agent_type: Type of agent (orchestrator, research, etc.)
            llm_client: LLM client for reasoning
            config: Global configuration object
            max_iterations: Maximum reasoning iterations
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.llm_client = llm_client
        self.config = config
        self.max_iterations = max_iterations

        # Execution tracking
        self.session_id = str(uuid.uuid4())
        self.trace = AgentTrace(
            agent_name=agent_name,
            agent_type=agent_type,
            session_id=self.session_id,
            start_time=datetime.now()
        )

        # Tool registry
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: List[Tool] = []

        # Register tools
        self._register_tools()

    @abstractmethod
    def _register_tools(self):
        """
        Register tools available to this agent
        Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get system prompt for this agent
        Must be implemented by subclasses
        """
        pass

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable
    ):
        """
        Register a tool that the agent can use

        Args:
            name: Tool name
            description: Tool description for LLM
            parameters: JSON schema for tool parameters
            function: Python function to execute when tool is called
        """
        # Store tool definition for LLM
        tool_def = Tool(
            type="function",
            name=name,
            description=description,
            parameters=parameters
        )
        self.tool_definitions.append(tool_def)

        # Store function for execution
        self.tools[name] = function

    def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool
            tool_args: Arguments for the tool

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        function = self.tools[tool_name]

        try:
            result = function(**tool_args)
            return result
        except Exception as e:
            error_msg = f"Tool execution error: {e}"
            print(error_msg)
            return {"error": error_msg}

    def log_action(
        self,
        action_type: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Any] = None
    ):
        """Log an agent action to the trace"""
        action = AgentAction(
            action_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action_type=action_type,
            content=content,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result
        )
        self.trace.actions.append(action)

    def run(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run the agent on a task using ReAct pattern

        Args:
            task: Task description
            context: Optional context dictionary

        Returns:
            Final output from the agent
        """
        self.log_action("task", f"Starting task: {task}")

        # Build system prompt
        system_prompt = self.get_system_prompt()

        # Add context if provided
        if context:
            task_with_context = f"{task}\n\nContext: {json.dumps(context, indent=2)}"
        else:
            task_with_context = task

        # ReAct loop
        conversation_history: List[Message] = []
        previous_response_id = None

        for iteration in range(self.max_iterations):
            self.log_action("thought", f"Iteration {iteration + 1}/{self.max_iterations}")

            try:
                # Generate response with tools
                if iteration == 0:
                    # First iteration: use task
                    response = self.llm_client.generate(
                        input=task_with_context,
                        instructions=system_prompt,
                        tools=self.tool_definitions if self.tool_definitions else None
                    )
                else:
                    # Subsequent iterations: use conversation history
                    response = self.llm_client.generate(
                        input=conversation_history,
                        instructions=system_prompt,
                        tools=self.tool_definitions if self.tool_definitions else None,
                        previous_response_id=previous_response_id
                    )

                previous_response_id = response.id

                # Log reasoning
                if response.reasoning_summary:
                    self.log_action("thought", response.reasoning_summary)

                # Check for tool calls
                if response.tool_calls:
                    # Execute each tool call
                    tool_results = []

                    for tool_call in response.tool_calls:
                        self.log_action(
                            "tool_call",
                            f"Calling tool: {tool_call.name}",
                            tool_name=tool_call.name,
                            tool_args=tool_call.arguments
                        )

                        # Execute tool
                        result = self.execute_tool(tool_call.name, tool_call.arguments)

                        self.log_action(
                            "observation",
                            f"Tool result: {str(result)[:200]}...",
                            tool_result=result
                        )

                        tool_results.append({
                            "call_id": tool_call.id,
                            "name": tool_call.name,
                            "result": result
                        })

                    # Add tool results to conversation
                    conversation_history.append(
                        Message(
                            role="assistant",
                            content=f"Tool calls executed: {len(tool_results)}"
                        )
                    )
                    conversation_history.append(
                        Message(
                            role="user",
                            content=f"Tool results: {json.dumps(tool_results, default=str)}"
                        )
                    )

                    # Continue loop for next iteration
                    continue

                # No tool calls - agent has reached conclusion
                if response.text:
                    self.log_action("decision", f"Final output: {response.text[:200]}...")
                    self.trace.final_output = response.text
                    self.trace.end_time = datetime.now()
                    self.trace.success = True
                    return response.text

                # No text and no tool calls - unexpected
                self.log_action("error", "No text or tool calls in response")
                break

            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {e}"
                self.log_action("error", error_msg)
                self.trace.error = error_msg
                self.trace.success = False
                raise

        # Max iterations reached
        self.trace.end_time = datetime.now()
        self.trace.success = False
        self.trace.error = "Max iterations reached"

        return "Task incomplete: Maximum iterations reached"

    def get_trace(self) -> AgentTrace:
        """Get execution trace"""
        return self.trace

    def print_trace(self):
        """Print execution trace for debugging"""
        print(f"\n{'='*60}")
        print(f"Agent Trace: {self.agent_name} ({self.agent_type})")
        print(f"Session: {self.session_id}")
        print(f"Start: {self.trace.start_time}")
        print(f"End: {self.trace.end_time}")
        print(f"Success: {self.trace.success}")
        if self.trace.error:
            print(f"Error: {self.trace.error}")
        print(f"{'='*60}\n")

        for action in self.trace.actions:
            print(f"[{action.timestamp.strftime('%H:%M:%S')}] {action.action_type.upper()}")
            print(f"  {action.content}")
            if action.tool_name:
                print(f"  Tool: {action.tool_name}")
                print(f"  Args: {action.tool_args}")
            print()

        if self.trace.final_output:
            print(f"\nFINAL OUTPUT:")
            print(self.trace.final_output)
            print(f"\n{'='*60}\n")


# Example: Simple calculator agent
class CalculatorAgent(BaseAgent):
    """Example agent that can perform calculations"""

    def _register_tools(self):
        """Register calculator tools"""
        self.register_tool(
            name="add",
            description="Add two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            },
            function=lambda a, b: a + b
        )

        self.register_tool(
            name="multiply",
            description="Multiply two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            },
            function=lambda a, b: a * b
        )

    def get_system_prompt(self) -> str:
        return """You are a calculator agent.

When given a math problem:
1. Break it down into steps
2. Use your tools (add, multiply) to solve it
3. Show your work
4. Provide the final answer

Be precise and explain your reasoning."""


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config)

    agent = CalculatorAgent(
        agent_name="calc-1",
        agent_type="calculator",
        llm_client=llm_client,
        config=config
    )

    result = agent.run("What is (5 + 3) * 4?")

    print(f"\nResult: {result}")
    agent.print_trace()
