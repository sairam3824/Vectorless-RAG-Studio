from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.generation.llm_client import OpenAICompatibleGenerator
from app.ingestion.chunker import SentenceChunker
from app.ingestion.document_loader import DocumentIngestionService
from app.retrieval.indexer import IndexManager
from app.utils.storage import SQLiteStore


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = SQLiteStore(settings.sqlite_path)
    store.initialize()

    chunker = SentenceChunker(
        chunk_size_words=settings.chunk_size_words,
        chunk_overlap_words=settings.chunk_overlap_words,
        snippet_chars=settings.max_chunk_chars_for_snippet,
    )
    index_manager = IndexManager(settings=settings, store=store)
    generator = OpenAICompatibleGenerator(settings=settings)
    ingestion_service = DocumentIngestionService(settings=settings, store=store, chunker=chunker)

    app.state.settings = settings
    app.state.store = store
    app.state.chunker = chunker
    app.state.index_manager = index_manager
    app.state.generator = generator
    app.state.ingestion_service = ingestion_service
    app.state.retriever = None

    if index_manager.index_exists():
        try:
            app.state.retriever = index_manager.load_retriever()
            logger.info("Loaded retrieval artifacts from disk.")
        except FileNotFoundError:
            logger.warning("Index artifacts were partially missing. Rebuild the index.")

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.mount("/", StaticFiles(directory=settings.project_root / "app" / "frontend", html=True), name="frontend")
