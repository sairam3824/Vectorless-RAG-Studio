from __future__ import annotations

import json
from datetime import UTC, datetime

from app.core.config import Settings
from app.models.domain import ChunkRecord
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.tfidf import TFIDFRetriever
from app.utils.storage import SQLiteStore


class IndexManager:
    def __init__(self, settings: Settings, store: SQLiteStore) -> None:
        self.settings = settings
        self.store = store
        self.bm25_path = self.settings.index_dir / "bm25.pkl"
        self.tfidf_path = self.settings.index_dir / "tfidf.pkl"
        self.manifest_path = self.settings.index_dir / "manifest.json"

    def build(self) -> dict[str, int | str | bool]:
        chunks = self.store.list_chunks()
        if not chunks:
            raise ValueError("No chunks available. Upload documents before indexing.")

        bm25 = BM25Retriever.build(chunks)
        bm25.save(self.bm25_path)

        tfidf_enabled = True
        try:
            tfidf = TFIDFRetriever.build(chunks)
            tfidf.save(self.tfidf_path)
        except ValueError:
            if not self.settings.allow_index_without_tfidf:
                raise
            tfidf_enabled = False
            if self.tfidf_path.exists():
                self.tfidf_path.unlink()

        manifest = {
            "created_at": datetime.now(UTC).isoformat(),
            "document_count": self.store.document_count(),
            "chunk_count": len(chunks),
            "tfidf_enabled": tfidf_enabled,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    def load_retriever(self) -> HybridRetriever:
        if not self.bm25_path.exists():
            raise FileNotFoundError("BM25 index artifact not found. Run /index first.")

        chunks = self.store.list_chunks()
        if not chunks:
            raise FileNotFoundError("No chunks available in storage. Upload documents first.")

        bm25 = BM25Retriever.load(self.bm25_path)
        tfidf = TFIDFRetriever.load(self.tfidf_path) if self.tfidf_path.exists() else None
        return HybridRetriever(settings=self.settings, chunks=chunks, bm25=bm25, tfidf=tfidf)

    def index_exists(self) -> bool:
        return self.bm25_path.exists()
