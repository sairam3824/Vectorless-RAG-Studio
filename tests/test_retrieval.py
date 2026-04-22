from app.core.config import get_settings
from app.models.domain import ChunkRecord, RetrievalFilters
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.tfidf import TFIDFRetriever


def _chunk(chunk_id: str, filename: str, file_type: str, text: str) -> ChunkRecord:
    return ChunkRecord(
        id=chunk_id,
        document_id=filename,
        filename=filename,
        file_type=file_type,
        chunk_index=0,
        text=text,
        token_count=len(text.split()),
        char_start=0,
        char_end=len(text),
        snippet=text[:80],
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_hybrid_retrieval_prefers_relevant_chunk() -> None:
    chunks = [
        _chunk("a-0", "security.md", "md", "The security policy requires MFA for every admin account."),
        _chunk("b-0", "billing.txt", "txt", "Invoices are issued on the first business day of each month."),
        _chunk("c-0", "ops.txt", "txt", "Deployments use blue green rollouts with health checks."),
    ]
    settings = get_settings()
    retriever = HybridRetriever(
        settings=settings,
        chunks=chunks,
        bm25=BM25Retriever.build(chunks),
        tfidf=TFIDFRetriever.build(chunks),
    )

    results = retriever.search("How are deployments rolled out?", top_k=2)

    assert results
    assert results[0].chunk.filename == "ops.txt"


def test_hybrid_retrieval_respects_metadata_filters() -> None:
    chunks = [
        _chunk("a-0", "one.txt", "txt", "API keys rotate every 30 days."),
        _chunk("b-0", "two.md", "md", "API keys rotate every 60 days in staging."),
    ]
    settings = get_settings()
    retriever = HybridRetriever(
        settings=settings,
        chunks=chunks,
        bm25=BM25Retriever.build(chunks),
        tfidf=TFIDFRetriever.build(chunks),
    )

    results = retriever.search(
        "When do API keys rotate?",
        top_k=5,
        filters=RetrievalFilters(filename="two.md"),
    )

    assert len(results) == 1
    assert results[0].chunk.filename == "two.md"
