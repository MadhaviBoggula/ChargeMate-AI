
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from openai import (
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from app.core.config import Settings
from app.core.config import settings
from app.llm.client import (
    LLMConfigError,
    LLMError,
    OpenRouterClient,
)


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return self.response


def build_inner(response=None, error=None):
    completions = FakeCompletions(response=response, error=error)

    return SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )


def build_response(content="Hello from the assistant"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def build_error_response(status_code: int):
    request = httpx.Request(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
    )

    return httpx.Response(
        status_code,
        request=request,
    )


def build_client(inner=None, **kwargs):
    defaults = {
        "api_key": "secret-test-key",
        "model": "test-model",
    }

    return OpenRouterClient(
        **{**defaults, **kwargs, "inner_client": inner}
    )


def test_client_requires_api_key():
    config = Settings(_env_file=None, database_url="postgresql://x")

    with pytest.raises(LLMConfigError):
        OpenRouterClient(model="test-model", config=config)


def test_client_requires_model():
    config = Settings(_env_file=None, database_url="postgresql://x")

    with pytest.raises(LLMConfigError):
        OpenRouterClient(api_key="secret-test-key", config=config)


def test_client_wires_settings_timeout_and_retries():
    client = build_client()

    assert client.inner_client.timeout == settings.llm_timeout_seconds
    assert client.inner_client.max_retries == settings.llm_max_retries


def test_chat_returns_assistant_content():
    inner = build_inner(response=build_response("Hello"))
    client = build_client(inner=inner)

    result = asyncio.run(
        client.chat([{"role": "user", "content": "Hi"}])
    )

    assert result == "Hello"
    assert inner.chat.completions.calls[0]["model"] == "test-model"


def test_chat_uses_explicit_overrides():
    inner = build_inner(response=build_response())
    client = build_client(inner=inner)

    asyncio.run(
        client.chat(
            [{"role": "user", "content": "Hi"}],
            model="other-model",
            temperature=0.7,
        )
    )

    call = inner.chat.completions.calls[0]

    assert call["model"] == "other-model"
    assert call["temperature"] == 0.7


def test_chat_empty_content_raises_controlled_error():
    inner = build_inner(response=build_response(content=None))
    client = build_client(inner=inner)

    with pytest.raises(LLMError):
        asyncio.run(
            client.chat([{"role": "user", "content": "Hi"}])
        )


@pytest.mark.parametrize(
    "error",
    [
        AuthenticationError(
            "invalid key",
            response=build_error_response(401),
            body=None,
        ),
        RateLimitError(
            "rate limited",
            response=build_error_response(429),
            body=None,
        ),
        APITimeoutError(
            httpx.Request(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
            )
        ),
    ],
)
def test_provider_errors_raise_controlled_llm_error(error):
    inner = build_inner(error=error)
    client = build_client(inner=inner)

    with pytest.raises(LLMError):
        asyncio.run(
            client.chat([{"role": "user", "content": "Hi"}])
        )


@pytest.mark.parametrize(
    "error",
    [
        AuthenticationError(
            "invalid key",
            response=build_error_response(401),
            body=None,
        ),
        RateLimitError(
            "rate limited",
            response=build_error_response(429),
            body=None,
        ),
        APITimeoutError(
            httpx.Request(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
            )
        ),
    ],
)
def test_error_messages_do_not_leak_api_key(error):
    inner = build_inner(error=error)
    client = build_client(inner=inner)

    with pytest.raises(LLMError) as exc_info:
        asyncio.run(
            client.chat([{"role": "user", "content": "Hi"}])
        )

    assert "secret-test-key" not in str(exc_info.value)
