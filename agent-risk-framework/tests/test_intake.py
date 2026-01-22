import pytest
from datetime import datetime
from src.intake.models import (
    AgentMetadata,
    AgentType,
    ToolDefinition,
    ToolCapability,
    RiskLevel
)

def test_agent_metadata_creation():
    """Test creating agent metadata"""
    agent = AgentMetadata(
        agent_id="test-001",
        name="Test Agent",
        agent_type=AgentType.OPENAI_GPT,
        description="A test agent for unit testing"
    )

    assert agent.agent_id == "test-001"
    assert agent.name == "Test Agent"
    assert agent.agent_type == AgentType.OPENAI_GPT
    assert agent.version == "1.0.0"  # Default
    assert agent.developer == "Unknown"  # Default
    assert isinstance(agent.created_at, datetime)

def test_tool_definition_with_capabilities():
    """Test creating tool definitions with capabilities"""
    tool = ToolDefinition(
        name="file_reader",
        description="Reads files from disk",
        capabilities=[ToolCapability.FILE_READ],
        risk_level=RiskLevel.MEDIUM
    )

    assert tool.name == "file_reader"
    assert ToolCapability.FILE_READ in tool.capabilities
    assert tool.risk_level == RiskLevel.MEDIUM

def test_agent_with_multiple_tools():
    """Test agent with multiple tool definitions"""
    tools = [
        ToolDefinition(
            name="web_search",
            description="Search the web",
            capabilities=[ToolCapability.NETWORK_ACCESS, ToolCapability.API_CALL]
        ),
        ToolDefinition(
            name="code_executor",
            description="Execute Python code",
            capabilities=[ToolCapability.CODE_EXECUTION],
            risk_level=RiskLevel.CRITICAL
        )
    ]

    agent = AgentMetadata(
        agent_id="multi-tool-001",
        name="Multi-Tool Agent",
        agent_type=AgentType.LANGCHAIN,
        tools=tools
    )

    assert len(agent.tools) == 2
    assert agent.tools[0].name == "web_search"
    assert agent.tools[1].risk_level == RiskLevel.CRITICAL

def test_agent_type_enum():
    """Test agent type enum values"""
    assert AgentType.OPENAI_GPT.value == "openai_gpt"
    assert AgentType.LANGCHAIN.value == "langchain"
    assert AgentType.MCP_SERVER.value == "mcp_server"
    assert AgentType.AUTOGEN.value == "autogen"
    assert AgentType.CREWAI.value == "crewai"
    assert AgentType.CUSTOM.value == "custom"

def test_tool_capability_enum():
    """Test tool capability enum values"""
    assert ToolCapability.CODE_EXECUTION.value == "code_execution"
    assert ToolCapability.FILE_READ.value == "file_read"
    assert ToolCapability.FILE_WRITE.value == "file_write"
    assert ToolCapability.NETWORK_ACCESS.value == "network_access"
    assert ToolCapability.DATABASE_ACCESS.value == "database_access"
    assert ToolCapability.API_CALL.value == "api_call"
    assert ToolCapability.BROWSER.value == "browser"
    assert ToolCapability.SHELL.value == "shell"

def test_risk_level_enum():
    """Test risk level enum values"""
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"

def test_agent_serialization():
    """Test that agent metadata can be serialized to dict"""
    agent = AgentMetadata(
        agent_id="serialize-001",
        name="Serialize Test Agent",
        agent_type=AgentType.CUSTOM,
        version="2.0.0",
        developer="Test Developer",
        description="Testing serialization",
        model_backend="gpt-4",
        temperature=0.7,
        max_tokens=2000
    )

    agent_dict = agent.dict()

    assert agent_dict["agent_id"] == "serialize-001"
    assert agent_dict["name"] == "Serialize Test Agent"
    assert agent_dict["version"] == "2.0.0"
    assert agent_dict["temperature"] == 0.7
    assert agent_dict["max_tokens"] == 2000
