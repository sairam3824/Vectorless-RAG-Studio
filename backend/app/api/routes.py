from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Body, File, HTTPException, Request, UploadFile
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.tfidf import TFIDFRetriever
from app.schemas.api import (
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentSummaryResponse,
    HealthResponse,
    IndexRequest,
    IndexResponse,
    PageResponse,
    QueryRequest,
    QueryResponse,
    SectionResponse,
    UploadDocumentSummary,
    UploadResponse,
    UploadSkip,
)
from app.schemas.domain import DocumentRecord, RetrievalFilters
from app.utils.time import utc_now


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    repository = request.app.state.repository
    artifact_store = request.app.state.artifact_store
    documents, pages, sections = repository.counts()
    return HealthResponse(
        status="ok",
        documents=documents,
        pages=pages,
        sections=sections,
        index_ready=artifact_store.index_exists(),
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(request: Request, files: list[UploadFile] = File(...)) -> UploadResponse:
    repository = request.app.state.repository
    parser = request.app.state.parser
    artifact_store = request.app.state.artifact_store
    settings = request.app.state.settings

    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    uploaded: list[UploadDocumentSummary] = []
    skipped: list[UploadSkip] = []
    changed_documents = False

    for upload in files:
        filename = Path(upload.filename or "").name
        if not filename:
            skipped.append(UploadSkip(filename="unknown", reason="Uploaded file did not include a filename."))
            continue

        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix not in {"pdf", "txt", "md"}:
            skipped.append(
                UploadSkip(
                    filename=filename,
                    reason="Unsupported file type. Allowed types are PDF, TXT, and MD.",
                )
            )
            continue

        payload = await upload.read()
        if not payload:
            skipped.append(UploadSkip(filename=filename, reason="Uploaded file was empty."))
            continue

        existing = repository.get_document_by_filename(filename)
        document_id = str(uuid4())
        stored_path = settings.upload_dir / f"{document_id}-{filename}"
        stored_path.write_bytes(payload)
        created_at = utc_now()

        try:
            pages, sections, title, content_hash = parser.parse(
                document_id=document_id,
                filename=filename,
                file_type=suffix,
                path=stored_path,
            )
        except ValueError as exc:
            stored_path.unlink(missing_ok=True)
            skipped.append(UploadSkip(filename=filename, reason=str(exc)))
            continue

        document = DocumentRecord(
            id=document_id,
            filename=filename,
            file_type=suffix,
            title=title,
            storage_path=str(stored_path),
            content_hash=content_hash,
            size_bytes=len(payload),
            page_count=len(pages),
            section_count=len(sections),
            indexing_status="uploaded",
            last_indexed_at=None,
            error_message=None,
            created_at=created_at,
            updated_at=created_at,
        )
        repository.replace_document_bundle(document=document, pages=pages, sections=sections)
        if existing is not None:
            Path(existing.storage_path).unlink(missing_ok=True)
        uploaded.append(
            UploadDocumentSummary(
                document_id=document.id,
                filename=document.filename,
                file_type=document.file_type,
                page_count=document.page_count,
                section_count=document.section_count,
                indexing_status=document.indexing_status,
            )
        )
        changed_documents = True

    if changed_documents:
        artifact_store.clear()
        request.app.state.query_service.invalidate_cache()
    return UploadResponse(documents=uploaded, skipped=skipped, total_uploaded=len(uploaded))


@router.post("/index", response_model=IndexResponse)
def build_index(request: Request, payload: IndexRequest = Body(default_factory=IndexRequest)) -> IndexResponse:
    repository = request.app.state.repository
    artifact_store = request.app.state.artifact_store
    page_indexer = request.app.state.page_indexer
    query_service = request.app.state.query_service

    available_ids = set(repository.list_document_ids())
    selected_ids = [document_id for document_id in (payload.document_ids or repository.list_document_ids()) if document_id in available_ids]
    if not selected_ids:
        raise HTTPException(status_code=400, detail="No documents are available to index.")

    units = page_indexer.build_units(document_ids=selected_ids)
    if not units:
        raise HTTPException(status_code=400, detail="The selected documents do not have indexable pages or sections.")

    artifact_store.clear()
    bm25 = BM25Retriever.build(units)
    bm25.save(artifact_store.bm25_path)

    tfidf_enabled = True
    try:
        tfidf = TFIDFRetriever.build(units)
        tfidf.save(artifact_store.tfidf_path)
    except ValueError:
        tfidf_enabled = False

    created_at = utc_now()
    repository.set_all_documents_status("uploaded")
    repository.mark_documents_indexed(document_ids=selected_ids, indexed_at=created_at)

    page_count = sum(1 for unit in units if unit.unit_type == "page")
    section_count = sum(1 for unit in units if unit.unit_type == "section")
    manifest = {
        "created_at": created_at,
        "indexed_document_ids": selected_ids,
        "document_count": len(selected_ids),
        "page_count": page_count,
        "section_count": section_count,
        "retrieval_unit_count": len(units),
        "tfidf_enabled": tfidf_enabled,
    }
    artifact_store.write_manifest(json.dumps(manifest, indent=2))
    query_service.invalidate_cache()

    return IndexResponse(
        message="Structured lexical index built successfully.",
        indexed_document_ids=selected_ids,
        document_count=len(selected_ids),
        page_count=page_count,
        section_count=section_count,
        retrieval_unit_count=len(units),
        tfidf_enabled=tfidf_enabled,
        created_at=created_at,
    )


@router.post("/query", response_model=QueryResponse)
def query_documents(request: Request, payload: QueryRequest) -> QueryResponse:
    query_service = request.app.state.query_service
    try:
        return query_service.query(
            question=payload.question,
            top_k=payload.top_k,
            filters=RetrievalFilters(
                document_ids=payload.selected_document_ids,
                filenames=payload.selected_filenames,
                file_types=payload.selected_file_types,
            ),
            include_debug=payload.include_debug,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/documents", response_model=list[DocumentSummaryResponse])
def list_documents(request: Request) -> list[DocumentSummaryResponse]:
    repository = request.app.state.repository
    return [DocumentSummaryResponse(**document.__dict__) for document in repository.list_documents()]


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(request: Request, document_id: str) -> DocumentDetailResponse:
    repository = request.app.state.repository
    document = repository.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    pages = [PageResponse(**page.__dict__) for page in repository.list_pages(document_id)]
    sections = [SectionResponse(**section.__dict__) for section in repository.list_sections(document_id)]
    return DocumentDetailResponse(**document.__dict__, pages=pages, sections=sections)


@router.get("/documents/{document_id}/sections", response_model=list[SectionResponse])
def get_document_sections(request: Request, document_id: str) -> list[SectionResponse]:
    repository = request.app.state.repository
    if repository.get_document(document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return [SectionResponse(**section.__dict__) for section in repository.list_sections(document_id)]


@router.get("/documents/{document_id}/pages", response_model=list[PageResponse])
def get_document_pages(request: Request, document_id: str) -> list[PageResponse]:
    repository = request.app.state.repository
    if repository.get_document(document_id) is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return [PageResponse(**page.__dict__) for page in repository.list_pages(document_id)]


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(request: Request, document_id: str) -> DeleteDocumentResponse:
    repository = request.app.state.repository
    artifact_store = request.app.state.artifact_store
    query_service = request.app.state.query_service
    deleted = repository.delete_document(document_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    Path(deleted.storage_path).unlink(missing_ok=True)
    artifact_store.clear()
    query_service.invalidate_cache()
    return DeleteDocumentResponse(message="Document deleted and index invalidated.", deleted_document_id=document_id)
