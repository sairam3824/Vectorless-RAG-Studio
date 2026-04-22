from __future__ import annotations

from app.schemas.domain import RetrievalUnit
from app.storage.repository import SQLiteRepository


class PageIndexer:
    def __init__(self, repository: SQLiteRepository) -> None:
        self.repository = repository

    def build_units(self, document_ids: list[str] | None = None) -> list[RetrievalUnit]:
        return self.repository.list_retrieval_units(document_ids=document_ids)
