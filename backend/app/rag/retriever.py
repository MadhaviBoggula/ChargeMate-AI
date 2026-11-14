
"""Role-scoped retrieval from pgvector (Member 4, lane D).

Retrieval is always filtered by the caller's role (owner/driver isolation) and
uses configurable top-k / minimum score. Grounding responses in dynamic
application data (availability, pricing, revenue, bookings) is forbidden
here - that must come from domain services/MCP tools.
"""
import logging

from sqlalchemy import select

from app.core.config import settings
from app.rag.models import KnowledgeEmbedding

logger = logging.getLogger(__name__)


async def retrieve_for_role(role: str, query: str) -> list[dict]:
    """Retrieve role-scoped knowledge chunks for a query.

    Returns ``[{"content", "score", "metadata"}]`` ordered by cosine
    similarity. Controlled failure mode: errors become empty context so the
    graph can still answer without fabricating evidence.
    """
    if not query.strip():
        return []
    if role not in {"owner", "driver"}:
        logger.warning("retrieve_for_role called with unknown role=%s", role)
        return []

    try:
        from app.rag.embeddings import get_embeddings

        query_vector = get_embeddings().embed_query(query)
    except Exception:
        logger.exception("Embedding computation failed")
        return []

    try:
        return _search_pgvector(role=role, query_vector=query_vector)
    except Exception:
        logger.exception("Vector search failed")
        return []


def _search_pgvector(role: str, query_vector: list[float]) -> list[dict]:
    from app.database.session import engine

    distance = KnowledgeEmbedding.embedding.cosine_distance(query_vector)
    stmt = (
        select(
            KnowledgeEmbedding.content,
            KnowledgeEmbedding.metadata_,
            distance.label("distance"),
        )
        .where(KnowledgeEmbedding.role == role)
        .order_by(distance)
        .limit(settings.rag_top_k)
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).all()

    results: list[dict] = []
    for content, metadata, dist in rows:
        score = 1.0 - float(dist)  # cosine distance -> similarity
        if score < settings.rag_min_score:
            continue
        results.append(
            {
                "content": content,
                "score": round(score, 4),
                "metadata": metadata,
            }
        )
    return results
