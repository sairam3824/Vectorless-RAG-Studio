from __future__ import annotations

from collections.abc import Iterable

from app.core.config import Settings
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.preprocessing import (
    exact_phrase_score,
    jaccard_similarity,
    keyword_overlap_score,
    normalize_query,
    title_match_score,
)
from app.retrieval.tfidf import TFIDFRetriever
from app.schemas.domain import RetrievalFilters, RetrievalUnit, RetrievedPassage


def _normalize_scores(scores: dict[str, float], candidate_ids: Iterable[str]) -> dict[str, float]:
    candidate_values = [scores.get(candidate_id, 0.0) for candidate_id in candidate_ids]
    if not candidate_values:
        return {}
    minimum = min(candidate_values)
    maximum = max(candidate_values)
    if maximum == minimum:
        if maximum <= 0:
            return {candidate_id: 0.0 for candidate_id in candidate_ids}
        return {candidate_id: 1.0 if scores.get(candidate_id, 0.0) > 0 else 0.0 for candidate_id in candidate_ids}
    return {
        candidate_id: (scores.get(candidate_id, 0.0) - minimum) / (maximum - minimum)
        for candidate_id in candidate_ids
    }


class HybridRetriever:
    def __init__(
        self,
        settings: Settings,
        units: list[RetrievalUnit],
        bm25: BM25Retriever,
        tfidf: TFIDFRetriever | None,
    ) -> None:
        self.settings = settings
        self.units = {unit.unit_id: unit for unit in units}
        self.bm25 = bm25
        self.tfidf = tfidf

    def search(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilters | None = None,
    ) -> tuple[list[RetrievedPassage], int]:
        candidate_limit = max(top_k * self.settings.retrieval_candidate_multiplier, top_k)
        bm25_scores = self.bm25.search(query, top_n=candidate_limit)
        tfidf_scores = self.tfidf.search(query, top_n=candidate_limit) if self.tfidf is not None else {}
        candidate_ids = list({*bm25_scores.keys(), *tfidf_scores.keys()})
        candidate_ids = [candidate_id for candidate_id in candidate_ids if self._matches_filters(self.units[candidate_id], filters)]

        normalized_bm25 = _normalize_scores(bm25_scores, candidate_ids)
        normalized_tfidf = _normalize_scores(tfidf_scores, candidate_ids)

        ranked: list[RetrievedPassage] = []
        for candidate_id in candidate_ids:
            unit = self.units[candidate_id]
            keyword_score, matched_terms = keyword_overlap_score(query, unit.text)
            title_score = title_match_score(query, " ".join(filter(None, [unit.title, unit.section_title, unit.heading_path, unit.filename])))
            exact_score = exact_phrase_score(query, unit.text, unit.title)
            filtered_boost = self.settings.document_filter_boost if filters and filters.document_ids else 0.0

            combined = (
                normalized_bm25.get(candidate_id, 0.0) * self.settings.bm25_weight
                + normalized_tfidf.get(candidate_id, 0.0) * self.settings.tfidf_weight
                + keyword_score * self.settings.keyword_weight
                + title_score * self.settings.title_weight
                + exact_score * self.settings.exact_match_weight
                + filtered_boost
            )

            if combined < self.settings.minimum_combined_score and not matched_terms:
                continue

            ranked.append(
                RetrievedPassage(
                    unit=unit,
                    score=combined,
                    bm25_score=bm25_scores.get(candidate_id, 0.0),
                    tfidf_score=tfidf_scores.get(candidate_id, 0.0),
                    keyword_score=keyword_score,
                    title_score=title_score,
                    exact_match_score=exact_score,
                    matched_terms=matched_terms,
                )
            )

        ranked.sort(key=lambda item: item.score, reverse=True)
        deduped = self._deduplicate(ranked)
        return deduped[:top_k], len(candidate_ids)

    def _matches_filters(self, unit: RetrievalUnit, filters: RetrievalFilters | None) -> bool:
        if filters is None:
            return True
        if filters.document_ids and unit.document_id not in filters.document_ids:
            return False
        if filters.filenames and unit.filename not in filters.filenames:
            return False
        if filters.file_types and unit.file_type not in filters.file_types:
            return False
        return True

    def _deduplicate(self, results: list[RetrievedPassage]) -> list[RetrievedPassage]:
        deduped: list[RetrievedPassage] = []
        for result in results:
            if any(
                existing.unit.document_id == result.unit.document_id
                and existing.unit.page_number == result.unit.page_number
                and jaccard_similarity(existing.unit.text, result.unit.text) >= self.settings.dedupe_similarity_threshold
                for existing in deduped
            ):
                continue
            deduped.append(result)
        return deduped

    @property
    def indexed_document_ids(self) -> list[str]:
        return sorted({unit.document_id for unit in self.units.values()})

    @property
    def normalized_manifest_query_hint(self) -> str:
        return normalize_query(" ".join(unit.title for unit in self.units.values()))
