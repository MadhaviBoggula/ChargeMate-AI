"""Role-scoped retrieval from pgvector (Member 4, lane D).

Retrieval is always filtered by the caller's role (owner/driver isolation) and
uses configurable top-k / minimum score. Grounding responses in dynamic
application data (availability, pricing, revenue, bookings) is forbidden
here - that must come from domain services/MCP tools.
"""
import logging

from app.core.config import get_settings
from app.core.errors import UpstreamProviderError

logger = logging.getLogger(__name__)
settings = get_settings()


async def retrieve_for_role(role: str, query: str) -> list[dict]:
    """Retrieve role-scoped knowledge chunks for a query.

    Returns a list of ``{"content": ..., "score": ..., "metadata": ...}``
    dicts. Controlled error handling: failures become an empty context so the
    graph can still answer without fabricating evidence.
    """
    if not query.strip():
        return []
    try:
        from app.rag.embeddings import get_embeddings

        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)
    except UpstreamProviderError:
        logger.warning("Embedding model unavailable; returning empty context")
        return []
    except Exception:
        logger.exception("Embedding computation failed")
        return []

    try:
        # pgvector similarity search lands with the RAG phase; the search
        # shape (role filter + top_k + min_score) is fixed here.
        return _search_pgvector(role=role, query_vector=query_vector, query=query)
    except Exception:
        logger.exception("Vector search failed")
        return []


def _search_pgvector(role: str, query_vector: list[float], query: str) -> list[dict]:
    if not settings.database_url:
        return []
    from sqlalchemy import text as sql_text

    from app.database.session import get_engine

    embedding_literal = "[" + ",".join(f"{v:.6f}" for v in query_vector) + "]"
    stmt = sql_text(
        """
        SELECT content, metadata, embedding <=> CAST(:embedding AS vector) AS distance
        FROM knowledge_embeddings
        WHERE metadata->>'role' = :role
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """
    )
    with get_engine().connect() as conn:
        rows = conn.execute(
            stmt,
            {"embedding": embedding_literal, "role": role, "top_k": settings.rag_top_k},
        ).fetchall()

    results: list[dict] = []
    for content, metadata, distance in rows:
        score = 1.0 - float(distance)
        if score < settings.rag_min_score:
            continue
        results.append({"content": content, "score": score, "metadata": metadata})
    return results
