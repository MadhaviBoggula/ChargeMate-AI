
"""RAG integration tests (Member 4, lane D).

Live-database tests: ingest sample docs into pgvector, then verify role
isolation and score filtering. Skipped when DATABASE_URL is not configured so
the suite runs green on a clean checkout.
"""
import pytest

from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.database_url,
    reason="DATABASE_URL not configured",
)

OWNER_QUERY = "How often should DC charger cables be inspected?"
DRIVER_QUERY = "What is the difference between AC and DC charging?"


@pytest.fixture(scope="module")
def ingested() -> dict:
    from app.rag.ingest import ingest_document

    owner_result = ingest_document(
        settings.owner_knowledge_dir / "charger_operations.txt",
        "owner",
    )
    driver_result = ingest_document(
        settings.driver_knowledge_dir / "charging_basics.txt",
        "driver",
    )
    # "indexed" on a clean DB, "skipped" when the CLI already ingested them
    assert owner_result["status"] in {"indexed", "skipped"}, owner_result
    assert driver_result["status"] in {"indexed", "skipped"}, driver_result
    return {"owner": owner_result, "driver": driver_result}


async def test_idempotent_reingest(ingested: dict) -> None:
    from app.rag.ingest import ingest_document

    result = ingest_document(
        settings.driver_knowledge_dir / "charging_basics.txt",
        "driver",
    )
    assert result["status"] == "skipped"


async def test_retrieval_role_isolation(ingested: dict) -> None:
    from app.rag.retriever import retrieve_for_role

    owner_hits = await retrieve_for_role("owner", OWNER_QUERY)
    driver_hits = await retrieve_for_role("driver", DRIVER_QUERY)
    assert owner_hits, "Owner retrieval returned nothing"
    assert driver_hits, "Driver retrieval returned nothing"

    # Owner query hits must come only from owner documents
    assert all(h["metadata"]["role"] == "owner" for h in owner_hits)
    assert all(h["metadata"]["role"] == "driver" for h in driver_hits)

    # Cross-role queries should NOT leak the other collection's content
    leaked_owner = await retrieve_for_role("driver", OWNER_QUERY)
    for hit in leaked_owner:
        assert "maintenance schedule" not in hit["content"].lower()
        assert hit["metadata"]["role"] == "driver"


async def test_min_score_filters_irrelevant(ingested: dict) -> None:
    from app.rag.retriever import retrieve_for_role

    nonsense = await retrieve_for_role(
        "driver", "zzz qq quixotic xylophone 42"
    )
    for hit in nonsense:
        assert hit["score"] >= settings.rag_min_score


async def test_top_k_respected(ingested: dict) -> None:
    from app.rag.retriever import retrieve_for_role

    hits = await retrieve_for_role("driver", DRIVER_QUERY)
    assert len(hits) <= settings.rag_top_k


async def test_reindex_replaces_chunks(ingested: dict) -> None:
    from sqlalchemy import select

    from app.database.session import SessionLocal
    from app.rag.ingest import ingest_document
    from app.rag.models import KnowledgeEmbedding

    source = settings.driver_knowledge_dir / "charging_basics.txt"
    result = ingest_document(source, "driver", force=True)
    assert result["status"] == "indexed"

    session = SessionLocal()
    try:
        rows = session.execute(
            select(KnowledgeEmbedding).where(
                KnowledgeEmbedding.role == "driver"
            )
        ).scalars().all()
        assert len({row.document_id for row in rows}) == 1
    finally:
        session.close()
