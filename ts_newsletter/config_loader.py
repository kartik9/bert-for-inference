"""
Configuration loader for TS Newsletter Automation
Loads config from YAML and environment variables
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-5"
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 4000
    store_conversations: bool = True
    agent_models: Dict[str, str] = Field(default_factory=dict)


class SearchConfig(BaseModel):
    """Search API configuration"""
    provider: str = "duckduckgo"
    bing_api_key: Optional[str] = None
    bing_endpoint: str = "https://api.bing.microsoft.com/v7.0/search"
    max_results: int = 20


class DatabaseConfig(BaseModel):
    """Database configuration"""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "ts_newsletter"
    postgres_user: str = "ts_user"
    postgres_password: str

    weaviate_host: str = "localhost"
    weaviate_port: int = 8080
    weaviate_scheme: str = "http"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536


class NewsletterConfig(BaseModel):
    """Newsletter generation configuration"""
    target_articles: int = 8
    min_articles: int = 5
    max_articles: int = 12
    date_range_days: int = 7

    min_relevance: float = 7.0
    min_novelty: float = 5.0
    min_impact: float = 6.0
    min_actionability: float = 5.0
    high_priority_threshold: float = 8.0


class WorkflowConfig(BaseModel):
    """Workflow and orchestration configuration"""
    parallel_research_agents: int = 5
    output_dir: str = "./output/newsletters"
    save_reasoning_traces: bool = True
    reasoning_log_path: str = "./logs/agent_reasoning"


class Config:
    """Main configuration class"""

    def __init__(self, config_path: Optional[str] = None):
        # Load environment variables
        load_dotenv()

        # Determine config file path
        if config_path is None:
            config_path = os.getenv("TS_NEWSLETTER_CONFIG", "./ts_newsletter/config.yaml")

        self.config_path = Path(config_path)

        # Load YAML config
        with open(self.config_path, 'r') as f:
            self._raw_config = yaml.safe_load(f)

        # Initialize structured configs
        self.llm = self._load_llm_config()
        self.search = self._load_search_config()
        self.database = self._load_database_config()
        self.newsletter = self._load_newsletter_config()
        self.workflow = self._load_workflow_config()

        # Store raw config for accessing other sections
        self.raw = self._raw_config

    def _get_env_var(self, env_var_name: str, required: bool = True) -> Optional[str]:
        """Get environment variable value"""
        value = os.getenv(env_var_name)
        if required and not value:
            raise ValueError(f"Required environment variable {env_var_name} not set")
        return value

    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration"""
        llm_cfg = self._raw_config.get("llm", {})

        api_key_env = llm_cfg.get("api_key_env", "OPENAI_API_KEY")
        api_key = self._get_env_var(api_key_env)

        return LLMConfig(
            provider=llm_cfg.get("provider", "openai"),
            model=llm_cfg.get("model", "gpt-5"),
            api_key=api_key,
            temperature=llm_cfg.get("temperature", 0.7),
            max_tokens=llm_cfg.get("max_tokens", 4000),
            store_conversations=llm_cfg.get("store_conversations", True),
            agent_models=llm_cfg.get("agent_models", {})
        )

    def _load_search_config(self) -> SearchConfig:
        """Load search API configuration"""
        search_cfg = self._raw_config.get("search", {})

        bing_api_key = None
        if search_cfg.get("provider") == "bing":
            bing_cfg = search_cfg.get("bing", {})
            bing_api_key_env = bing_cfg.get("api_key_env", "BING_SEARCH_API_KEY")
            bing_api_key = self._get_env_var(bing_api_key_env)

        return SearchConfig(
            provider=search_cfg.get("provider", "duckduckgo"),
            bing_api_key=bing_api_key,
            bing_endpoint=search_cfg.get("bing", {}).get(
                "endpoint",
                "https://api.bing.microsoft.com/v7.0/search"
            ),
            max_results=search_cfg.get(search_cfg.get("provider", "duckduckgo"), {}).get(
                "max_results", 20
            )
        )

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        db_cfg = self._raw_config.get("databases", {})

        pg_cfg = db_cfg.get("postgresql", {})
        postgres_password = self._get_env_var(
            pg_cfg.get("password_env", "POSTGRES_PASSWORD")
        )

        weaviate_cfg = db_cfg.get("weaviate", {})

        return DatabaseConfig(
            postgres_host=pg_cfg.get("host", "localhost"),
            postgres_port=pg_cfg.get("port", 5432),
            postgres_database=pg_cfg.get("database", "ts_newsletter"),
            postgres_user=pg_cfg.get("user", "ts_user"),
            postgres_password=postgres_password,
            weaviate_host=weaviate_cfg.get("host", "localhost"),
            weaviate_port=weaviate_cfg.get("port", 8080),
            weaviate_scheme=weaviate_cfg.get("scheme", "http"),
            embedding_model=weaviate_cfg.get("embedding_model", "text-embedding-3-small"),
            embedding_dimensions=weaviate_cfg.get("embedding_dimensions", 1536)
        )

    def _load_newsletter_config(self) -> NewsletterConfig:
        """Load newsletter configuration"""
        nl_cfg = self._raw_config.get("newsletter", {})
        scoring_cfg = nl_cfg.get("scoring", {})

        return NewsletterConfig(
            target_articles=nl_cfg.get("target_articles", 8),
            min_articles=nl_cfg.get("min_articles", 5),
            max_articles=nl_cfg.get("max_articles", 12),
            date_range_days=nl_cfg.get("date_range_days", 7),
            min_relevance=scoring_cfg.get("min_relevance", 7.0),
            min_novelty=scoring_cfg.get("min_novelty", 5.0),
            min_impact=scoring_cfg.get("min_impact", 6.0),
            min_actionability=scoring_cfg.get("min_actionability", 5.0),
            high_priority_threshold=scoring_cfg.get("high_priority_threshold", 8.0)
        )

    def _load_workflow_config(self) -> WorkflowConfig:
        """Load workflow configuration"""
        wf_cfg = self._raw_config.get("workflow", {})

        return WorkflowConfig(
            parallel_research_agents=wf_cfg.get("parallel_research_agents", 5),
            output_dir=wf_cfg.get("output_dir", "./output/newsletters"),
            save_reasoning_traces=self._raw_config.get("logging", {}).get(
                "save_reasoning_traces", True
            ),
            reasoning_log_path=self._raw_config.get("logging", {}).get(
                "reasoning_log_path", "./logs/agent_reasoning"
            )
        )

    def get_search_queries(self) -> Dict[str, list]:
        """Get search queries from config"""
        return self._raw_config.get("search_queries", {})

    def get_rss_feeds(self) -> Dict[str, list]:
        """Get RSS feed sources from config"""
        return self._raw_config.get("rss_feeds", {})

    def get_agent_model(self, agent_name: str) -> str:
        """Get model for specific agent, fallback to default"""
        return self.llm.agent_models.get(agent_name, self.llm.model)


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config(config_path: Optional[str] = None):
    """Reload configuration"""
    global _config
    _config = Config(config_path)
    return _config
