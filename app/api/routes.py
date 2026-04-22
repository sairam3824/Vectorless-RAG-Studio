from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.schemas import (
    CitationModel,
    HealthResponse,
    IndexResponse,
    IngestResponse,
    IngestedDocumentModel,
    QueryRequest,
    QueryResponse,
    RetrievedChunkModel,
)
from app.models.domain import RetrievalFilters


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    store = request.app.state.store
    index_manager = request.app.state.index_manager
    return HealthResponse(
        status="ok",
        documents=store.document_count(),
        chunks=store.chunk_count(),
        index_ready=index_manager.index_exists(),
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: Request, files: list[UploadFile] = File(...)) -> IngestResponse:
    ingestion_service = request.app.state.ingestion_service
    result = await ingestion_service.ingest_uploads(files)

    chunk_counts = Counter(chunk.document_id for chunk in result.chunks)
    ingested_documents = [
        IngestedDocumentModel(
            document_id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            chunk_count=chunk_counts.get(document.id, 0),
            size_bytes=document.size_bytes,
        )
        for document in result.documents
    ]
    return IngestResponse(
        ingested_documents=ingested_documents,
        total_documents=len(result.documents),
        total_chunks=len(result.chunks),
        skipped=result.skipped,
    )


@router.post("/index", response_model=IndexResponse)
def build_index(request: Request) -> IndexResponse:
    index_manager = request.app.state.index_manager
    try:
        manifest = index_manager.build()
        request.app.state.retriever = index_manager.load_retriever()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return IndexResponse(
        message="Index built successfully.",
        document_count=int(manifest["document_count"]),
        chunk_count=int(manifest["chunk_count"]),
        tfidf_enabled=bool(manifest["tfidf_enabled"]),
        created_at=str(manifest["created_at"]),
    )


@router.post("/query", response_model=QueryResponse)
def query_documents(request: Request, payload: QueryRequest) -> QueryResponse:
    retriever = request.app.state.retriever
    if retriever is None:
        try:
            retriever = request.app.state.index_manager.load_retriever()
            request.app.state.retriever = retriever
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    filters = None
    if payload.filters is not None:
        filters = RetrievalFilters(
            filename=payload.filters.filename,
            file_type=payload.filters.file_type,
        )

    results = retriever.search(
        query=payload.question,
        top_k=payload.top_k,
        filters=filters,
        use_tfidf=payload.use_tfidf,
        use_reranker=payload.use_reranker,
    )

    generator = request.app.state.generator
    answer = generator.generate_answer(payload.question, results)
    citations = [
        CitationModel(
            filename=result.chunk.filename,
            chunk_id=result.chunk.id,
            snippet=result.chunk.snippet,
        )
        for result in results
    ]
    retrieved_chunks = [
        RetrievedChunkModel(
            chunk_id=result.chunk.id,
            filename=result.chunk.filename,
            file_type=result.chunk.file_type,
            score=result.score,
            bm25_score=result.bm25_score,
            tfidf_score=result.tfidf_score,
            keyword_score=result.keyword_score,
            rerank_score=result.rerank_score,
            snippet=result.chunk.snippet,
            text=result.chunk.text,
        )
        for result in results
    ]

    return QueryResponse(answer=answer, citations=citations, retrieved_chunks=retrieved_chunks)
