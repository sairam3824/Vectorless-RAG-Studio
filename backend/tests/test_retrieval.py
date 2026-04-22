from __future__ import annotations

from app.core.config import Settings
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.tfidf import TFIDFRetriever
from app.schemas.domain import RetrievalFilters, RetrievalUnit


def build_units() -> list[RetrievalUnit]:
    return [
        RetrievalUnit(
            unit_id="doc-1-section-1",
            document_id="doc-1",
            filename="company_handbook.md",
            document_title="Company Handbook",
            file_type="md",
            unit_type="section",
            page_number=1,
            start_page=1,
            end_page=1,
            section_id="doc-1-section-1",
            section_title="Remote Operations",
            heading_level=2,
            heading_path="Company Handbook / Remote Operations",
            title="Remote Operations",
            text="Remote employees must acknowledge critical incidents within 15 minutes during on-call rotations.",
            snippet="Remote employees must acknowledge critical incidents within 15 minutes.",
        ),
        RetrievalUnit(
            unit_id="doc-2-section-1",
            document_id="doc-2",
            filename="product_notes.txt",
            document_title="Product Notes",
            file_type="txt",
            unit_type="section",
            page_number=1,
            start_page=1,
            end_page=1,
            section_id="doc-2-section-1",
            section_title="Enterprise Access",
            heading_level=1,
            heading_path="Product Notes / Enterprise Access",
            title="Enterprise Access",
            text="Single sign-on support is available on the enterprise plan only.",
            snippet="Single sign-on support is available on the enterprise plan only.",
        ),
        RetrievalUnit(
            unit_id="doc-2-page-1",
            document_id="doc-2",
            filename="product_notes.txt",
            document_title="Product Notes",
            file_type="txt",
            unit_type="page",
            page_number=1,
            start_page=1,
            end_page=1,
            section_id=None,
            section_title=None,
            heading_level=None,
            heading_path=None,
            title="Product Notes Overview",
            text="The analytics module exports CSV reports every morning at 06:00 UTC.",
            snippet="The analytics module exports CSV reports every morning at 06:00 UTC.",
        ),
    ]


def test_hybrid_retriever_prefers_matching_section() -> None:
    units = build_units()
    settings = Settings()
    retriever = HybridRetriever(
        settings=settings,
        units=units,
        bm25=BM25Retriever.build(units),
        tfidf=TFIDFRetriever.build(units),
    )

    results, candidate_count = retriever.search(
        query="How quickly should remote employees acknowledge a critical incident?",
        top_k=3,
    )

    assert candidate_count >= 1
    assert results[0].unit.filename == "company_handbook.md"
    assert results[0].unit.section_title == "Remote Operations"


def test_hybrid_retriever_respects_document_filters() -> None:
    units = build_units()
    settings = Settings()
    retriever = HybridRetriever(
        settings=settings,
        units=units,
        bm25=BM25Retriever.build(units),
        tfidf=TFIDFRetriever.build(units),
    )

    results, _ = retriever.search(
        query="Which plan includes single sign-on?",
        top_k=3,
        filters=RetrievalFilters(document_ids=["doc-2"]),
    )

    assert results
    assert all(result.unit.document_id == "doc-2" for result in results)
