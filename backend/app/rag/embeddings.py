"""Local sentence-transformers embeddings (Member 4, lane D).

Uses the model from settings (default ``all-MiniLM-L6-v2``, 384 dimensions).
Downloads on first use and runs on CPU - no embedding API key needed.
"""
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings
from app.core.errors import UpstreamProviderError

settings = get_settings()


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    try:
        return HuggingFaceEmbeddings(
            model_name=settings.rag_sentence_transformers_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception as exc:
        raise UpstreamProviderError(
            "Failed to initialize the local embedding model.", details=None
        ) from exc
