from __future__ import annotations

import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.domain import RetrievalUnit


class TFIDFRetriever:
    def __init__(self, unit_ids: list[str], vectorizer: TfidfVectorizer, matrix) -> None:
        self.unit_ids = unit_ids
        self.vectorizer = vectorizer
        self.matrix = matrix

    @classmethod
    def build(cls, units: list[RetrievalUnit]) -> "TFIDFRetriever":
        documents = [f"{unit.title}\n{unit.text}" for unit in units]
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(documents)
        return cls(unit_ids=[unit.unit_id for unit in units], vectorizer=vectorizer, matrix=matrix)

    def search(self, query: str, top_n: int = 20) -> dict[str, float]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).flatten()
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
    def load(cls, path: Path) -> "TFIDFRetriever":
        with path.open("rb") as handle:
            return pickle.load(handle)
