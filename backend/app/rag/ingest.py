"""Document ingestion pipeline (Member 4, lane D).

Flow (task doc 7.3): upload -> extract (PDF/DOCX/TXT) -> clean -> chunk ->
embed -> persist to pgvector, tagged with role metadata for owner/driver
knowledge isolation.

``knowledge_documents`` metadata persistence is coordinated with Member 1.
"""
import logging
from pathlib import Path

from app.core.errors import AppError, ValidationError
from app.rag.chunker import chunk_text

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
ALLOWED_ROLES = {"owner", "driver"}


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


async def ingest_document(
    path: Path,
    role: str,
    document_id: str,
    db_session=None,
) -> int:
    """Ingest one document into the role-scoped collection.

    Returns the number of chunks persisted. Vector persistence to pgvector is
    completed when the embeddings table/migration exists; extraction, chunking
    and metadata flow are already functional.
    """
    if role not in ALLOWED_ROLES:
        raise ValidationError(f"Unknown knowledge role: {role}")
    if not path.exists():
        raise AppError(f"Document not found: {path}")

    text = clean_text(extract_text(path))
    metadata = {
        "role": role,
        "document_id": document_id,
        "source": str(path.name),
    }
    chunks = chunk_text(text, metadata)
    logger.info(
        "Extracted %d chunks from %s for role=%s", len(chunks), path.name, role
    )
    # pgvector persistence (embeddings + insert) lands with the RAG phase.
    return len(chunks)
