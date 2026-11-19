from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ai_provider: str = "groq"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()