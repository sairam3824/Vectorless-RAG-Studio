from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DocumentRecord:
    id: str
    filename: str
    file_type: str
    original_path: str
    content_hash: str
    size_bytes: int
    created_at: str


@dataclass(slots=True)
class ChunkRecord:
    id: str
    document_id: str
    filename: str
    file_type: str
    chunk_index: int
    text: str
    token_count: int
    char_start: int
    char_end: int
    snippet: str
    created_at: str

    @property
    def citation(self) -> str:
        return f"{self.filename} | {self.id}"


@dataclass(slots=True)
class RetrievalFilters:
    filename: str | None = None
    file_type: str | None = None


@dataclass(slots=True)
class RetrievalResult:
    chunk: ChunkRecord
    score: float
    bm25_score: float = 0.0
    tfidf_score: float = 0.0
    keyword_score: float = 0.0
    rerank_score: float = 0.0
    metadata: dict[str, str | float | int] = field(default_factory=dict)
