from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DocumentRecord:
    id: str
    filename: str
    file_type: str
    title: str
    storage_path: str
    content_hash: str
    size_bytes: int
    page_count: int
    section_count: int
    indexing_status: str
    last_indexed_at: str | None
    error_message: str | None
    created_at: str
    updated_at: str


@dataclass(slots=True)
class PageRecord:
    id: str
    document_id: str
    page_number: int
    label: str
    title: str | None
    text: str
    snippet: str
    word_count: int
    token_count: int
    char_count: int


@dataclass(slots=True)
class SectionRecord:
    id: str
    document_id: str
    title: str
    normalized_title: str
    heading_level: int
    page_number: int
    start_page: int
    end_page: int
    parent_section_id: str | None
    heading_path: str
    text: str
    snippet: str
    word_count: int
    token_count: int


@dataclass(slots=True)
class RetrievalUnit:
    unit_id: str
    document_id: str
    filename: str
    document_title: str
    file_type: str
    unit_type: str
    page_number: int
    start_page: int
    end_page: int
    section_id: str | None
    section_title: str | None
    heading_level: int | None
    heading_path: str | None
    title: str
    text: str
    snippet: str


@dataclass(slots=True)
class RetrievalFilters:
    document_ids: list[str] | None = None
    filenames: list[str] | None = None
    file_types: list[str] | None = None


@dataclass(slots=True)
class RetrievedPassage:
    unit: RetrievalUnit
    score: float
    bm25_score: float
    tfidf_score: float
    keyword_score: float
    title_score: float
    exact_match_score: float
    matched_terms: list[str] = field(default_factory=list)


@dataclass(slots=True)
class QueryDebugInfo:
    normalized_query: str
    query_terms: list[str]
    candidate_count: int
    context_preview: str
