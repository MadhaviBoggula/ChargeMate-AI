
from app.core.config import Settings
from app.core.config import settings


def test_settings_load_env_file_values():
    assert settings.llm_temperature == 0.2
    assert settings.llm_timeout_seconds == 60
    assert settings.llm_max_retries == 2
    assert settings.max_tool_call_rounds == 5
    assert settings.rag_sentence_transformers_model == "all-MiniLM-L6-v2"
    assert settings.rag_embedding_dimensions == 384
    assert settings.rag_chunk_size == 1000
    assert settings.rag_chunk_overlap == 150
    assert settings.rag_top_k == 4
    assert settings.rag_min_score == 0.35


def test_settings_apply_defaults_without_env_file():
    config = Settings(_env_file=None)

    assert config.llm_temperature == 0.2
    assert config.llm_timeout_seconds == 60
    assert config.llm_max_retries == 2
    assert config.max_tool_call_rounds == 5
    assert config.mcp_owner_server_url is None
    assert config.mcp_driver_server_url is None
    assert config.rag_embedding_dimensions == 384
    assert config.rag_chunk_size == 1000
    assert config.rag_chunk_overlap == 150
    assert config.rag_top_k == 4
    assert config.rag_min_score == 0.35


def test_settings_apply_env_overrides():
    config = Settings(
        _env_file=None,
        max_tool_call_rounds=3,
        rag_top_k=6,
        rag_chunk_size=800,
    )

    assert config.max_tool_call_rounds == 3
    assert config.rag_top_k == 6
    assert config.rag_chunk_size == 800


def test_settings_do_not_expose_openrouter_key_as_string():
    value = settings.openrouter_api_key

    if value is not None:
        assert str(value.get_secret_value()) != str(value)
