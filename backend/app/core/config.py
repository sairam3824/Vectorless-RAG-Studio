from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PageIndex-Inspired Vectorless RAG"
    log_level: str = "INFO"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 45.0
    openai_temperature: float = 0.1

    chunk_preview_chars: int = 280
    synthetic_page_words: int = 700
    retrieval_top_k_default: int = 6
    retrieval_candidate_multiplier: int = 10
    minimum_combined_score: float = 0.08
    dedupe_similarity_threshold: float = 0.9

    bm25_weight: float = 0.42
    tfidf_weight: float = 0.28
    keyword_weight: float = 0.14
    title_weight: float = 0.1
    exact_match_weight: float = 0.04
    document_filter_boost: float = 0.02

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_dir(self) -> Path:
        return self.backend_root / "data"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "rag.sqlite3"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
