from __future__ import annotations

import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.models.domain import ChunkRecord
from app.retrieval.preprocessing import tokenize


class BM25Retriever:
    def __init__(self, chunk_ids: list[str], tokenized_corpus: list[list[str]]) -> None:
        self.chunk_ids = chunk_ids
        self.tokenized_corpus = tokenized_corpus
        self.model = BM25Okapi(tokenized_corpus)

    @classmethod
    def build(cls, chunks: list[ChunkRecord]) -> "BM25Retriever":
        chunk_ids = [chunk.id for chunk in chunks]
        tokenized_corpus = [tokenize(chunk.text) for chunk in chunks]
        return cls(chunk_ids=chunk_ids, tokenized_corpus=tokenized_corpus)

    def save(self, path: Path) -> None:
        with path.open("wb") as file_handle:
            pickle.dump({"chunk_ids": self.chunk_ids, "tokenized_corpus": self.tokenized_corpus}, file_handle)

    @classmethod
    def load(cls, path: Path) -> "BM25Retriever":
        with path.open("rb") as file_handle:
            data = pickle.load(file_handle)
        return cls(chunk_ids=data["chunk_ids"], tokenized_corpus=data["tokenized_corpus"])

    def search(self, query: str, top_n: int | None = None) -> dict[str, float]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {}

        scores = self.model.get_scores(query_tokens)
        pairs = list(zip(self.chunk_ids, scores, strict=True))
        pairs.sort(key=lambda item: float(item[1]), reverse=True)
        if top_n is not None:
            pairs = pairs[:top_n]
        return {chunk_id: float(score) for chunk_id, score in pairs}
