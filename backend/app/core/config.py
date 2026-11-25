
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ChargeMate AI API"
    app_version: str = "0.1.0"
    app_environment: str = "development"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    database_url: str | None = None

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str | None = None

    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    max_tool_call_rounds: int = 5

    mcp_owner_server_url: str | None = None
    mcp_driver_server_url: str | None = None

    embedding_provider: str | None = None
    embedding_model: str | None = None

    rag_sentence_transformers_model: str = "all-MiniLM-L6-v2"
    rag_embedding_dimensions: int = 384
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 150
    rag_top_k: int = 4
    rag_min_score: float = 0.35

    knowledge_base_dir: Path = (
        Path(__file__).resolve().parents[2] / "knowledge_base"
    )
    owner_knowledge_dir: Path = knowledge_base_dir / "owner"
    driver_knowledge_dir: Path = knowledge_base_dir / "driver"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
