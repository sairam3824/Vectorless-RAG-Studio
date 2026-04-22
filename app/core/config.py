from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "RAG Without Vector DB")
    app_env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    upload_dir: Path = PROJECT_ROOT / "data" / "uploads"
    index_dir: Path = PROJECT_ROOT / "data" / "index"
    sqlite_path: Path = PROJECT_ROOT / "data" / "rag.sqlite3"

    chunk_size_words: int = int(os.getenv("CHUNK_SIZE_WORDS", "180"))
    chunk_overlap_words: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "45"))
    max_chunk_chars_for_snippet: int = int(os.getenv("MAX_CHUNK_SNIPPET_CHARS", "200"))

    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
    candidate_multiplier: int = int(os.getenv("CANDIDATE_MULTIPLIER", "6"))
    bm25_weight: float = float(os.getenv("BM25_WEIGHT", "0.55"))
    tfidf_weight: float = float(os.getenv("TFIDF_WEIGHT", "0.30"))
    keyword_weight: float = float(os.getenv("KEYWORD_WEIGHT", "0.15"))
    reranker_weight: float = float(os.getenv("RERANKER_WEIGHT", "0.15"))
    dedupe_similarity_threshold: float = float(os.getenv("DEDUPE_SIMILARITY_THRESHOLD", "0.82"))

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    openai_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    allow_index_without_tfidf: bool = _as_bool(os.getenv("ALLOW_INDEX_WITHOUT_TFIDF"), True)

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.upload_dir, self.index_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
