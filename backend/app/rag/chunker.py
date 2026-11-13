"""Document chunking (Member 4, lane D).

Chunk size / overlap come from settings (1000 / 150). Each chunk keeps role
and document metadata so retrieval can enforce role isolation.
"""
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings

settings = get_settings()


@dataclass
class DocumentChunk:
    content: str
    metadata: dict = field(default_factory=dict)


def chunk_text(text: str, base_metadata: dict) -> list[DocumentChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [
        DocumentChunk(content=chunk, metadata=dict(base_metadata))
        for chunk in splitter.split_text(text)
    ]
