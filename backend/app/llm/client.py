"""Reusable OpenRouter LLM client (Member 4, lane A).

OpenRouter is OpenAI-compatible, so the langchain-openai ``ChatOpenAI`` client
points at ``OPENROUTER_BASE_URL``. Model, temperature, timeout and retry policy
all come from settings. Prompts live in ``app/llm/prompts`` and stay versioned
and separate from business logic.
"""
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.errors import UpstreamProviderError

settings = get_settings()

LLM_HEADER_APP_TITLE = "ChargeMate AI"


@lru_cache
def get_chat_model() -> BaseChatModel:
    """Shared ChatOpenAI instance pointed at OpenRouter.

    Raises a controlled UpstreamProviderError when credentials are missing,
    instead of a raw traceback.
    """
    if not settings.openrouter_api_key:
        raise UpstreamProviderError(
            "LLM provider is not configured (missing OPENROUTER_API_KEY)."
        )
    try:
        return ChatOpenAI(
            model=settings.openrouter_model,
            temperature=settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            default_headers={
                "X-Title": LLM_HEADER_APP_TITLE,
            },
            rate_limiter=InMemoryRateLimiter(requests_per_second=2),
        )
    except Exception as exc:  # controlled provider failure
        raise UpstreamProviderError(
            "Failed to initialize the LLM client.", details=None
        ) from exc
