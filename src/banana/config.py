from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Banana application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FalkorDB settings (Local or Cloud)
    falkordb_url: Optional[str] = Field(
        default=None,
        description="FalkorDB connection URL for cloud instances (e.g. falkor://user:pass@host:port)",
    )
    falkordb_host: str = Field(default="localhost", description="FalkorDB host address")
    falkordb_port: int = Field(default=6379, description="FalkorDB port")
    falkordb_password: Optional[str] = Field(default=None, description="FalkorDB password (optional)")
    falkordb_ssl: bool = Field(default=False, description="Enable SSL/TLS connection for FalkorDB Cloud")

    # Dual Graph names
    demand_graph_name: str = Field(
        default="banana_demand",
        description="FalkorDB graph name for task demand graph",
    )
    knowledge_graph_name: str = Field(
        default="banana_knowledge",
        description="FalkorDB graph name for company and market knowledge graph",
    )

    # Gemini settings
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for live model calls",
    )
    gemini_model: str = Field(
        default="gemini-3.8-flash",
        description="Gemini model name to use for agent execution",
    )

    # Context assembly defaults
    default_token_budget: int = Field(
        default=4000,
        ge=500,
        le=128000,
        description="Default token budget for context assembly",
    )

    @field_validator("falkordb_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @property
    def falkordb_uri(self) -> str:
        """Return formatted FalkorDB host:port connection string."""
        return f"{self.falkordb_host}:{self.falkordb_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()
