from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentType(str, Enum):
    OPENAI_GPT = "openai_gpt"
    LANGCHAIN = "langchain"
    MCP_SERVER = "mcp_server"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    CUSTOM = "custom"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ToolCapability(str, Enum):
    CODE_EXECUTION = "code_execution"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK_ACCESS = "network_access"
    DATABASE_ACCESS = "database_access"
    API_CALL = "api_call"
    BROWSER = "browser"
    SHELL = "shell"

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    capabilities: List[ToolCapability] = []
    risk_level: RiskLevel = RiskLevel.MEDIUM

class AgentMetadata(BaseModel):
    agent_id: str
    name: str
    version: str = "1.0.0"
    developer: str = "Unknown"
    description: str = ""
    agent_type: AgentType
    source_url: Optional[str] = None

    # Capabilities
    tools: List[ToolDefinition] = []
    external_apis: List[str] = []

    # Configuration (if accessible)
    system_prompt: Optional[str] = None
    model_backend: str = "unknown"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    # Supply chain
    dependencies: List[str] = []
    framework: Optional[str] = None
    framework_version: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
