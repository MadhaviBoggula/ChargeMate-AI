
"""Document ingestion pipeline (Member 4, lane D).

Flow (product doc 7.3): extract (PDF/DOCX/TXT) -> clean -> chunk ->
batch-embed (local sentence-transformers) -> bulk insert into pgvector with
role metadata. Idempotent: re-ingesting an unchanged file is a no-op; a
changed file replaces its chunks. Status lives on ``knowledge_documents``.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ValidationError
from app.rag.chunker import DocumentChunk, chunk_text
from app.rag.embeddings import get_embeddings
from app.rag.models import KnowledgeDocument, KnowledgeEmbedding

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
ALLOWED_ROLES = {"owner", "driver"}
EMBED_BATCH_SIZE = 32
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024  # 10 MB MVP guard


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        import docx

        document = docx.Document(str(path))
        return "\n\n".join(p.text for p in document.paragraphs if p.text)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValidationError(f"Unsupported document type: {suffix}")


def clean_text(text: str) -> str:
    """Light cleaning; keep structure for chunking."""
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_source(path: Path, role: str) -> None:
    if role not in ALLOWED_ROLES:
        raise ValidationError(f"Unknown knowledge role: {role}")
    if not path.exists():
        raise AppError(f"Document not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported document type '{path.suffix}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValidationError(
            f"Document exceeds {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB limit."
        )


def _upsert_document_row(
    db: Session,
    *,
    role: str,
    path: Path,
    content_hash: str,
) -> tuple[KnowledgeDocument, bool]:
    """Return (document, changed). Marks status in place."""
    stmt = select(KnowledgeDocument).where(
        KnowledgeDocument.source_path == str(path.resolve())
    )
    document = db.execute(stmt).scalar_one_or_none()

    if document is None:
        document = KnowledgeDocument(
            role=role,
            source_filename=path.name,
            source_path=str(path.resolve()),
            content_hash=content_hash,
            status="processing",
            chunk_count=0,
        )
        db.add(document)
        db.flush()
        return document, True

    if document.content_hash == content_hash and document.status == "indexed":
        return document, False  # unchanged, already indexed

    document.content_hash = content_hash
    document.status = "processing"
    document.error = None
    document.chunk_count = 0
    db.flush()
    return document, True


def _insert_embeddings(
    db: Session, document: KnowledgeDocument, chunks: list[DocumentChunk]
) -> None:
    embeddings = get_embeddings()
    vectors = []

    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = [c.content for c in chunks[start : start + EMBED_BATCH_SIZE]]
        vectors.extend(embeddings.embed_documents(batch))

    rows = [
        KnowledgeEmbedding(
            document_id=document.id,
            role=document.role,
            chunk_index=i,
            content=chunk.content,
            metadata_={
                **chunk.metadata,
                "chunk_index": i,
                "source": document.source_filename,
                "role": document.role,
            },
            embedding=vector,
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    db.bulk_save_objects(rows)
    document.chunk_count = len(rows)
    document.status = "indexed"
    document.ingested_at = datetime.now(timezone.utc)


def ingest_document(
    path: Path,
    role: str,
    db: Session | None = None,
    force: bool = False,
) -> dict:
    """Ingest one document into the role-scoped collection.

    Returns a structured outcome:
    ``{"document_id", "status": indexed|skipped|failed, "chunks", "error"}``.
    Owns its session/transaction when called standalone (CLI); when a session
    is passed, commits belong to the caller.
    """
    path = Path(path)
    outcome: dict = {
        "document_id": None,
        "status": "failed",
        "chunks": 0,
        "error": None,
    }

    if db is None:
        from app.database.session import SessionLocal

        session = SessionLocal()
    else:
        session = db

    try:
        validate_source(path, role)
        content_hash = _content_hash(path)

        document, changed = _upsert_document_row(
            session, role=role, path=path, content_hash=content_hash
        )
        outcome["document_id"] = str(document.id)

        if not changed and not force:
            outcome["status"] = "skipped"
            return outcome

        # Replace previous chunks atomically with the new ones
        session.execute(
            delete(KnowledgeEmbedding).where(
                KnowledgeEmbedding.document_id == document.id
            )
        )
        text = clean_text(extract_text(path))
        chunks = chunk_text(text, {"role": role, "source": path.name})
        if not chunks:
            document.status = "failed"
            document.error = "No extractable content"
            outcome["error"] = "No extractable content"
            return outcome

        _insert_embeddings(session, document, chunks)
        outcome["status"] = "indexed"
        outcome["chunks"] = document.chunk_count
        session.commit()
        logger.info(
            "Ingested %s (%d chunks) for role=%s",
            path.name,
            len(chunks),
            role,
        )
        return outcome
    except (ValidationError, AppError) as exc:
        outcome["error"] = exc.message
        _mark_failed(session, outcome, db)
        return outcome
    except Exception as exc:
        logger.exception("Ingestion failed for %s", path.name)
        outcome["error"] = f"{exc.__class__.__name__}: {exc}"
        _mark_failed(session, outcome, db)
        return outcome
    finally:
        if db is None:
            session.close()


def _mark_failed(
    session: Session, outcome: dict, outer_db: Session | None
) -> None:
    """Roll back the failed transaction, then persist failure status on the
    knowledge_documents row if it already exists from a previous ingest."""
    target = outer_db or session
    try:
        target.rollback()
    except Exception:
        pass
    document_id = outcome.get("document_id")
    if not document_id:
        return
    try:
        document = target.get(KnowledgeDocument, uuid.UUID(document_id))
        if document is not None:
            document.status = "failed"
            document.error = (outcome.get("error") or "")[:2000]
            target.commit()
    except Exception:
        logger.exception(
            "Could not persist failure status for %s", document_id
        )
        try:
            target.rollback()
        except Exception:
            pass
