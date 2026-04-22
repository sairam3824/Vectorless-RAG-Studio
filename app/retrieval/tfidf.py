from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.models.domain import ChunkRecord
from app.retrieval.preprocessing import tokenize


class TFIDFRetriever:
    def __init__(self, chunk_ids: list[str], vectorizer: TfidfVectorizer, matrix) -> None:
        self.chunk_ids = chunk_ids
        self.vectorizer = vectorizer
        self.matrix = matrix

    @classmethod
    def build(cls, chunks: list[ChunkRecord]) -> "TFIDFRetriever":
        vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 2),
        )
        matrix = vectorizer.fit_transform([chunk.text for chunk in chunks])
        return cls(chunk_ids=[chunk.id for chunk in chunks], vectorizer=vectorizer, matrix=matrix)

    def save(self, path: Path) -> None:
        with path.open("wb") as file_handle:
            pickle.dump(
                {"chunk_ids": self.chunk_ids, "vectorizer": self.vectorizer, "matrix": self.matrix},
                file_handle,
            )

    @classmethod
    def load(cls, path: Path) -> "TFIDFRetriever":
        with path.open("rb") as file_handle:
            data = pickle.load(file_handle)
        return cls(chunk_ids=data["chunk_ids"], vectorizer=data["vectorizer"], matrix=data["matrix"])

    def search(self, query: str, top_n: int | None = None) -> dict[str, float]:
        query_vector = self.vectorizer.transform([query])
        scores = (self.matrix @ query_vector.T).toarray().ravel()
        order = np.argsort(scores)[::-1]
        if top_n is not None:
            order = order[:top_n]
        return {self.chunk_ids[index]: float(scores[index]) for index in order if scores[index] > 0}
