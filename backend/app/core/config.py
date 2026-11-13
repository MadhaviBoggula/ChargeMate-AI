"""Application settings loaded from the repo-root .env file.

Single source of truth for configuration. pydantic-settings reads
``../.env`` relative to this backend/ package (the repo root).
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repo root is three levels up
REPO_ROOT = Path(__file__).resolve().parents[3]
DOTENV_PATH = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DOTENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "ChargeMate AI"
    app_env: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    api_v1_prefix: str = "/api/v1"

    # --- Database (Neon PostgreSQL) ---
    database_url: str = Field(default="", alias="DATABASE_URL")
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- LLM provider (OpenRouter, OpenAI-compatible) ---
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openrouter_model: str = Field(
        default="nvidia/nemotron-3.5-super-vl:free", alias="OPENROUTER_MODEL"
    )
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    max_tool_call_rounds: int = 5

    # --- MCP servers (empty until Members 2/3 deploy) ---
    mcp_owner_server_url: str = Field(default="", alias="MCP_OWNER_SERVER_URL")
    mcp_driver_server_url: str = Field(default="", alias="MCP_DRIVER_SERVER_URL")

    # --- RAG (local sentence-transformers embeddings) ---
    rag_sentence_transformers_model: str = "all-MiniLM-L6-v2"
    rag_embedding_dimensions: int = 384
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 150
    rag_top_k: int = 4
    rag_min_score: float = 0.35

    # Knowledge-base folders (repo root)
    knowledge_base_dir: Path = REPO_ROOT / "knowledge_base"
    owner_knowledge_dir: Path = knowledge_base_dir / "owner"
    driver_knowledge_dir: Path = knowledge_base_dir / "driver"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}

    def mcp_url_for_role(self, role: str) -> str:
        """MCP server URL for a role; empty string when not yet deployed."""
        return {
            "owner": self.mcp_owner_server_url,
            "driver": self.mcp_driver_server_url,
        }.get(role.lower(), "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
