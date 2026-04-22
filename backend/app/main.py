from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.generation.llm_client import LLMClient
from app.ingestion.document_parser import DocumentParser
from app.ingestion.section_extractor import SectionExtractor
from app.retrieval.citation_builder import CitationBuilder
from app.retrieval.page_indexer import PageIndexer
from app.retrieval.query_service import QueryService
from app.storage.artifact_store import ArtifactStore
from app.storage.repository import SQLiteRepository


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    repository = SQLiteRepository(settings.sqlite_path)
    repository.initialize()
    artifact_store = ArtifactStore(settings)
    parser = DocumentParser(settings=settings, section_extractor=SectionExtractor(settings))
    page_indexer = PageIndexer(repository=repository)
    llm_client = LLMClient(settings=settings)
    citation_builder = CitationBuilder(settings=settings)
    query_service = QueryService(
        settings=settings,
        repository=repository,
        artifact_store=artifact_store,
        llm_client=llm_client,
        citation_builder=citation_builder,
    )

    app.state.settings = settings
    app.state.repository = repository
    app.state.artifact_store = artifact_store
    app.state.parser = parser
    app.state.page_indexer = page_indexer
    app.state.query_service = query_service
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
