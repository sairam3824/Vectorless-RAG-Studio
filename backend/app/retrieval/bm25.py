from __future__ import annotations

import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.retrieval.preprocessing import tokenize
from app.schemas.domain import RetrievalUnit


class BM25Retriever:
    def __init__(self, unit_ids: list[str], tokenized_corpus: list[list[str]], model: BM25Okapi) -> None:
        self.unit_ids = unit_ids
        self.tokenized_corpus = tokenized_corpus
        self.model = model

    @classmethod
    def build(cls, units: list[RetrievalUnit]) -> "BM25Retriever":
        tokenized_corpus = [tokenize(f"{unit.title}\n{unit.text}") for unit in units]
        return cls(
            unit_ids=[unit.unit_id for unit in units],
            tokenized_corpus=tokenized_corpus,
            model=BM25Okapi(tokenized_corpus),
        )

    def search(self, query: str, top_n: int = 20) -> dict[str, float]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {}
        scores = self.model.get_scores(query_tokens)
        ranked = sorted(
            ((self.unit_ids[index], float(score)) for index, score in enumerate(scores) if score > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        return dict(ranked[:top_n])

    def save(self, path: Path) -> None:
        with path.open("wb") as handle:
            pickle.dump(self, handle)

    @classmethod
    def load(cls, path: Path) -> "BM25Retriever":
        with path.open("rb") as handle:
            return pickle.load(handle)
