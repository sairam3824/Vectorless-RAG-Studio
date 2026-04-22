from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    documents: int
    pages: int
    sections: int
    index_ready: bool


class UploadDocumentSummary(BaseModel):
    document_id: str
    filename: str
    file_type: str
    page_count: int
    section_count: int
    indexing_status: str


class UploadSkip(BaseModel):
    filename: str
    reason: str


class UploadResponse(BaseModel):
    documents: list[UploadDocumentSummary]
    skipped: list[UploadSkip]
    total_uploaded: int


class IndexRequest(BaseModel):
    document_ids: list[str] | None = None


class IndexResponse(BaseModel):
    message: str
    indexed_document_ids: list[str]
    document_count: int
    page_count: int
    section_count: int
    retrieval_unit_count: int
    tfidf_enabled: bool
    created_at: str


class DocumentSummaryResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    title: str
    page_count: int
    section_count: int
    size_bytes: int
    indexing_status: str
    last_indexed_at: str | None
    error_message: str | None
    created_at: str
    updated_at: str


class PageResponse(BaseModel):
    id: str
    page_number: int
    label: str
    title: str | None
    snippet: str
    text: str
    word_count: int
    token_count: int


class SectionResponse(BaseModel):
    id: str
    title: str
    normalized_title: str
    heading_level: int
    page_number: int
    start_page: int
    end_page: int
    parent_section_id: str | None
    heading_path: str
    snippet: str
    text: str
    word_count: int
    token_count: int


class DocumentDetailResponse(DocumentSummaryResponse):
    pages: list[PageResponse]
    sections: list[SectionResponse]


class QueryRequest(BaseModel):
    question: str = Field(min_length=2)
    top_k: int = Field(default=6, ge=1, le=12)
    selected_document_ids: list[str] | None = None
    selected_filenames: list[str] | None = None
    selected_file_types: list[str] | None = None
    include_debug: bool = True


class CitationResponse(BaseModel):
    document_id: str
    filename: str
    page_number: int
    section_title: str | None
    heading_path: str | None
    snippet: str
    unit_type: str
    unit_id: str


class RetrievedPassageResponse(BaseModel):
    unit_id: str
    document_id: str
    filename: str
    document_title: str
    file_type: str
    unit_type: str
    page_number: int
    start_page: int
    end_page: int
    section_title: str | None
    heading_level: int | None
    heading_path: str | None
    title: str
    snippet: str
    text: str
    score: float
    bm25_score: float
    tfidf_score: float
    keyword_score: float
    title_score: float
    exact_match_score: float
    matched_terms: list[str]


class RetrievalSummaryResponse(BaseModel):
    candidate_count: int
    returned_count: int
    indexed_document_ids: list[str]
    selected_document_ids: list[str]


class QueryDebugResponse(BaseModel):
    normalized_query: str
    query_terms: list[str]
    candidate_count: int
    context_preview: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    answer_status: str
    llm_used: bool
    citations: list[CitationResponse]
    retrieved_chunks: list[RetrievedPassageResponse]
    retrieval_summary: RetrievalSummaryResponse
    selected_document_ids: list[str]
    debug: QueryDebugResponse | None = None


class DeleteDocumentResponse(BaseModel):
    message: str
    deleted_document_id: str
