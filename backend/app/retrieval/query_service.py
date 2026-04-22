from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from app.generation.llm_client import LLMClient
from app.generation.prompting import build_context, build_messages
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.citation_builder import CitationBuilder
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.preprocessing import normalize_query, tokenize
from app.retrieval.tfidf import TFIDFRetriever
from app.schemas.api import QueryDebugResponse, QueryResponse, RetrievedPassageResponse, RetrievalSummaryResponse
from app.schemas.domain import QueryDebugInfo, RetrievalFilters
from app.storage.artifact_store import ArtifactStore
from app.storage.repository import SQLiteRepository


class QueryService:
    def __init__(
        self,
        settings: Settings,
        repository: SQLiteRepository,
        artifact_store: ArtifactStore,
        llm_client: LLMClient,
        citation_builder: CitationBuilder,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.artifact_store = artifact_store
        self.llm_client = llm_client
        self.citation_builder = citation_builder
        self._retriever: HybridRetriever | None = None
        self._loaded_manifest_path: Path | None = None

    def invalidate_cache(self) -> None:
        self._retriever = None
        self._loaded_manifest_path = None

    def query(
        self,
        question: str,
        top_k: int,
        filters: RetrievalFilters | None = None,
        include_debug: bool = True,
    ) -> QueryResponse:
        retriever = self._ensure_retriever()
        passages, candidate_count = retriever.search(question, top_k=top_k, filters=filters)
        citations = self.citation_builder.build(passages)
        context = build_context(passages)
        generation = self.llm_client.generate(
            question=question,
            messages=build_messages(question=question, context=context),
            citations=citations,
        )

        debug_info = QueryDebugInfo(
            normalized_query=normalize_query(question),
            query_terms=tokenize(question),
            candidate_count=candidate_count,
            context_preview=context,
        )
        return QueryResponse(
            question=question,
            answer=generation.answer,
            answer_status=generation.status,
            llm_used=generation.llm_used,
            citations=citations,
            retrieved_chunks=[
                RetrievedPassageResponse(
                    unit_id=passage.unit.unit_id,
                    document_id=passage.unit.document_id,
                    filename=passage.unit.filename,
                    document_title=passage.unit.document_title,
                    file_type=passage.unit.file_type,
                    unit_type=passage.unit.unit_type,
                    page_number=passage.unit.page_number,
                    start_page=passage.unit.start_page,
                    end_page=passage.unit.end_page,
                    section_title=passage.unit.section_title,
                    heading_level=passage.unit.heading_level,
                    heading_path=passage.unit.heading_path,
                    title=passage.unit.title,
                    snippet=passage.unit.snippet,
                    text=passage.unit.text,
                    score=passage.score,
                    bm25_score=passage.bm25_score,
                    tfidf_score=passage.tfidf_score,
                    keyword_score=passage.keyword_score,
                    title_score=passage.title_score,
                    exact_match_score=passage.exact_match_score,
                    matched_terms=passage.matched_terms,
                )
                for passage in passages
            ],
            retrieval_summary=RetrievalSummaryResponse(
                candidate_count=candidate_count,
                returned_count=len(passages),
                indexed_document_ids=retriever.indexed_document_ids,
                selected_document_ids=filters.document_ids if filters and filters.document_ids else retriever.indexed_document_ids,
            ),
            selected_document_ids=filters.document_ids if filters and filters.document_ids else retriever.indexed_document_ids,
            debug=QueryDebugResponse(**debug_info.__dict__) if include_debug else None,
        )

    def _ensure_retriever(self) -> HybridRetriever:
        manifest_path = self.artifact_store.manifest_path
        if not self.artifact_store.index_exists():
            raise FileNotFoundError("No retrieval artifacts found. Upload documents and run indexing first.")
        if self._retriever is not None and self._loaded_manifest_path == manifest_path:
            return self._retriever

        manifest = json.loads(self.artifact_store.manifest_path.read_text(encoding="utf-8"))
        document_ids = manifest.get("indexed_document_ids") or None
        units = self.repository.list_retrieval_units(document_ids=document_ids)
        bm25 = BM25Retriever.load(self.artifact_store.bm25_path)
        tfidf = TFIDFRetriever.load(self.artifact_store.tfidf_path) if self.artifact_store.tfidf_path.exists() else None
        self._retriever = HybridRetriever(settings=self.settings, units=units, bm25=bm25, tfidf=tfidf)
        self._loaded_manifest_path = manifest_path
        return self._retriever
