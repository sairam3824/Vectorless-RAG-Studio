from __future__ import annotations

from pathlib import Path

from app.core.config import Settings


class ArtifactStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bm25_path = self.settings.index_dir / "bm25.pkl"
        self.tfidf_path = self.settings.index_dir / "tfidf.pkl"
        self.manifest_path = self.settings.index_dir / "manifest.json"

    def index_exists(self) -> bool:
        return self.bm25_path.exists() and self.manifest_path.exists()

    def clear(self) -> None:
        for path in [self.bm25_path, self.tfidf_path, self.manifest_path]:
            if path.exists():
                path.unlink()

    def write_manifest(self, payload: str) -> None:
        self.manifest_path.write_text(payload, encoding="utf-8")
