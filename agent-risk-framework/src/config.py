from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # Environment
    env: str = "development"
    log_level: str = "INFO"

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./agent_assessments.db"

    # Security
    api_key_enabled: bool = False
    api_key: Optional[str] = None

    # AIVSS Scoring Weights
    weight_security: float = 0.25
    weight_privacy: float = 0.20
    weight_reliability: float = 0.20
    weight_transparency: float = 0.15
    weight_autonomy: float = 0.20

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
