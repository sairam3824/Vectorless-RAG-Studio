from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalFiltersModel(BaseModel):
    filename: str | None = None
    file_type: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    use_tfidf: bool = True
    use_reranker: bool = True
    filters: RetrievalFiltersModel | None = None


class RetrievedChunkModel(BaseModel):
    chunk_id: str
    filename: str
    file_type: str
    score: float
    bm25_score: float
    tfidf_score: float
    keyword_score: float
    rerank_score: float
    snippet: str
    text: str


class CitationModel(BaseModel):
    filename: str
    chunk_id: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationModel]
    retrieved_chunks: list[RetrievedChunkModel]


class HealthResponse(BaseModel):
    status: str
    documents: int
    chunks: int
    index_ready: bool


class IngestedDocumentModel(BaseModel):
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    size_bytes: int


class IngestResponse(BaseModel):
    ingested_documents: list[IngestedDocumentModel]
    total_documents: int
    total_chunks: int
    skipped: list[dict[str, str]]


class IndexResponse(BaseModel):
    message: str
    document_count: int
    chunk_count: int
    tfidf_enabled: bool
    created_at: str
