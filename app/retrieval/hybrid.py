from __future__ import annotations

from collections.abc import Iterable

from app.core.config import Settings
from app.models.domain import ChunkRecord, RetrievalFilters, RetrievalResult
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.preprocessing import jaccard_similarity, keyword_overlap_score, tokenize
from app.retrieval.tfidf import TFIDFRetriever


def _normalize_scores(scores: dict[str, float], candidate_ids: Iterable[str]) -> dict[str, float]:
    candidate_values = [scores.get(chunk_id, 0.0) for chunk_id in candidate_ids]
    if not candidate_values:
        return {}

    minimum = min(candidate_values)
    maximum = max(candidate_values)
    if maximum == minimum:
        if maximum <= 0:
            return {chunk_id: 0.0 for chunk_id in candidate_ids}
        return {chunk_id: 1.0 if scores.get(chunk_id, 0.0) > 0 else 0.0 for chunk_id in candidate_ids}

    return {
        chunk_id: (scores.get(chunk_id, 0.0) - minimum) / (maximum - minimum)
        for chunk_id in candidate_ids
    }


def _rerank_score(query: str, text: str) -> float:
    query_terms = tokenize(query)
    text_terms = tokenize(text)
    if not query_terms or not text_terms:
        return 0.0

    exact_phrase_bonus = 1.0 if " ".join(query_terms) in " ".join(text_terms) else 0.0
    coverage = sum(1 for term in query_terms if term in text_terms) / len(query_terms)
    density = coverage / max(len(text_terms) / 100, 1)
    return min(1.0, coverage + density + exact_phrase_bonus * 0.2)


class HybridRetriever:
    def __init__(
        self,
        settings: Settings,
        chunks: list[ChunkRecord],
        bm25: BM25Retriever,
        tfidf: TFIDFRetriever | None = None,
    ) -> None:
        self.settings = settings
        self.chunks_by_id = {chunk.id: chunk for chunk in chunks}
        self.bm25 = bm25
        self.tfidf = tfidf

    def search(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilters | None = None,
        use_tfidf: bool = True,
        use_reranker: bool = True,
    ) -> list[RetrievalResult]:
        candidate_pool = max(top_k * self.settings.candidate_multiplier, top_k)
        bm25_scores = self.bm25.search(query, top_n=candidate_pool)
        tfidf_scores = (
            self.tfidf.search(query, top_n=candidate_pool)
            if use_tfidf and self.tfidf is not None
            else {}
        )

        candidate_ids = list({*bm25_scores.keys(), *tfidf_scores.keys()})
        candidate_ids = [chunk_id for chunk_id in candidate_ids if self._matches_filters(self.chunks_by_id[chunk_id], filters)]

        normalized_bm25 = _normalize_scores(bm25_scores, candidate_ids)
        normalized_tfidf = _normalize_scores(tfidf_scores, candidate_ids)

        ranked: list[RetrievalResult] = []
        for chunk_id in candidate_ids:
            chunk = self.chunks_by_id[chunk_id]
            keyword_score = keyword_overlap_score(query, chunk.text)
            rerank_score = _rerank_score(query, chunk.text) if use_reranker else 0.0

            score = (
                normalized_bm25.get(chunk_id, 0.0) * self.settings.bm25_weight
                + normalized_tfidf.get(chunk_id, 0.0) * self.settings.tfidf_weight
                + keyword_score * self.settings.keyword_weight
                + rerank_score * self.settings.reranker_weight
            )

            ranked.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    bm25_score=bm25_scores.get(chunk_id, 0.0),
                    tfidf_score=tfidf_scores.get(chunk_id, 0.0),
                    keyword_score=keyword_score,
                    rerank_score=rerank_score,
                )
            )

        ranked.sort(key=lambda result: result.score, reverse=True)
        return self._deduplicate(ranked)[:top_k]

    def _matches_filters(self, chunk: ChunkRecord, filters: RetrievalFilters | None) -> bool:
        if filters is None:
            return True
        if filters.filename and chunk.filename != filters.filename:
            return False
        if filters.file_type and chunk.file_type != filters.file_type:
            return False
        return True

    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        deduped: list[RetrievalResult] = []
        for result in results:
            if any(
                result.chunk.document_id == existing.chunk.document_id
                and jaccard_similarity(result.chunk.text, existing.chunk.text) >= self.settings.dedupe_similarity_threshold
                for existing in deduped
            ):
                continue
            deduped.append(result)
        return deduped
