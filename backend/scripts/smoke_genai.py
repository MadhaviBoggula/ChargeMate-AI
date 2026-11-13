"""GenAI smoke test: one OpenRouter chat call + one local embedding.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\smoke_genai.py
Downloads all-MiniLM-L6-v2 (~90 MB) on first run.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main() -> None:
    from app.llm.client import get_chat_model
    from app.rag.embeddings import get_embeddings
    from app.core.config import get_settings

    settings = get_settings()
    print(f"Model: {settings.openrouter_model}")

    result = await get_chat_model().ainvoke("Reply with exactly: CHARGEMATE_OK")
    text = str(result.content).strip()
    print(f"LLM replied: {text!r}")
    assert "CHARGEMATE_OK" in text, "LLM did not echo the marker"

    embeddings = get_embeddings()
    vector = embeddings.embed_query("What is the difference between AC and DC charging?")
    print(f"Embedding dimensions: {len(vector)}")
    assert len(vector) == settings.rag_embedding_dimensions, (
        f"Expected {settings.rag_embedding_dimensions} dims, got {len(vector)}"
    )

    print("SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
