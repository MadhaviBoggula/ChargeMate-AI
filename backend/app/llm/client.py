
import logging
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.core.config import Settings, settings

logger = logging.getLogger("chargemate.llm")


class LLMConfigError(Exception):
    """Raised when the LLM provider is not configured correctly."""


class LLMError(Exception):
    """Raised when an LLM provider request fails in a controlled way."""


class OpenRouterClient:
    """
    Async client for OpenRouter chat completions.

    Wraps the OpenAI-compatible SDK with project defaults for model,
    temperature, timeout, and retries, and converts provider failures
    into controlled backend errors that never leak credentials.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        config: Settings | None = None,
        inner_client: AsyncOpenAI | None = None,
    ):
        config = config or settings

        self.api_key = api_key or (
            config.openrouter_api_key.get_secret_value()
            if config.openrouter_api_key
            else None
        )
        self.base_url = base_url or config.openrouter_base_url
        self.model = model or config.openrouter_model
        self.temperature = (
            temperature
            if temperature is not None
            else config.llm_temperature
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else config.llm_timeout_seconds
        )
        self.max_retries = (
            max_retries
            if max_retries is not None
            else config.llm_max_retries
        )

        if not self.api_key:
            raise LLMConfigError(
                "OpenRouter API key is not configured."
            )

        if not self.model:
            raise LLMConfigError(
                "OpenRouter model is not configured."
            )

        self.inner_client = inner_client or AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            max_retries=self.max_retries,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        **request_kwargs: Any,
    ) -> str:
        """
        Run a chat completion and return the assistant message content.

        Raises LLMConfigError for a missing configuration and LLMError
        for provider failures.
        """

        completion = await self.complete(
            messages,
            model=model,
            temperature=temperature,
            **request_kwargs,
        )

        content = completion.choices[0].message.content

        if content is None:
            raise LLMError(
                "LLM provider returned an empty response."
            )

        return content

    async def complete(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        **request_kwargs: Any,
    ):
        """
        Run a chat completion and return the raw completion object so
        callers can access tool calls or other message attributes.
        """

        try:
            completion = await self.inner_client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=(
                    temperature
                    if temperature is not None
                    else self.temperature
                ),
                **request_kwargs,
            )

            return completion

        except AuthenticationError:
            logger.error("LLM authentication failed")
            raise LLMError(
                "LLM provider rejected the configured credentials."
            )

        except RateLimitError:
            logger.error("LLM rate limit reached")
            raise LLMError(
                "LLM provider rate limit reached. Try again shortly."
            )

        except APITimeoutError:
            logger.error("LLM request timed out")
            raise LLMError(
                "LLM provider request timed out."
            )

        except APIConnectionError:
            logger.error("LLM connection failure")
            raise LLMError(
                "Could not reach the LLM provider."
            )

        except APIStatusError as exc:
            logger.error(
                "LLM provider error status=%s", exc.status_code
            )
            raise LLMError(
                "LLM provider returned an error response."
            )

        except Exception as exc:
            logger.exception("Unexpected LLM failure")
            raise LLMError(
                "Unexpected failure while contacting the LLM provider."
            ) from exc


_client: OpenRouterClient | None = None


def get_openrouter_client() -> OpenRouterClient:
    """Return a shared OpenRouter client instance."""

    global _client

    if _client is None:
        _client = OpenRouterClient()

    return _client


def reset_openrouter_client() -> None:
    """Clear the shared client so the next call rebuilds it."""

    global _client
    _client = None
