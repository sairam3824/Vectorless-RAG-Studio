from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from app.core.config import Settings
from app.ingestion.chunker import SentenceChunker
from app.models.domain import ChunkRecord, DocumentRecord
from app.utils.storage import SQLiteStore


logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


@dataclass(slots=True)
class IngestionResult:
    documents: list[DocumentRecord]
    chunks: list[ChunkRecord]
    skipped: list[dict[str, str]]


class DocumentIngestionService:
    def __init__(self, settings: Settings, store: SQLiteStore, chunker: SentenceChunker) -> None:
        self.settings = settings
        self.store = store
        self.chunker = chunker

    async def ingest_uploads(self, files: list[UploadFile]) -> IngestionResult:
        documents: list[DocumentRecord] = []
        all_chunks: list[ChunkRecord] = []
        skipped: list[dict[str, str]] = []

        if not files:
            raise HTTPException(status_code=400, detail="No files were uploaded.")

        for upload in files:
            filename = Path(upload.filename or "").name
            suffix = Path(filename).suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                skipped.append(
                    {
                        "filename": filename or "unknown",
                        "reason": f"Unsupported file type. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                    }
                )
                continue

            stored_path = self.settings.upload_dir / filename
            content = await upload.read()
            if not content:
                skipped.append({"filename": filename, "reason": "Uploaded file was empty."})
                continue

            stored_path.write_bytes(content)
            logger.info("Saved upload to %s", stored_path)

            text = self._extract_text(stored_path, suffix)
            if not text.strip():
                skipped.append({"filename": filename, "reason": "No extractable text found."})
                continue

            content_hash = hashlib.sha256(content).hexdigest()
            created_at = datetime.now(UTC).isoformat()
            document_id = str(uuid4())
            document = DocumentRecord(
                id=document_id,
                filename=filename,
                file_type=suffix.lstrip("."),
                original_path=str(stored_path),
                content_hash=content_hash,
                size_bytes=len(content),
                created_at=created_at,
            )
            chunks = self.chunker.chunk_document(
                text=text,
                document_id=document_id,
                filename=filename,
                file_type=document.file_type,
                created_at=created_at,
            )

            if not chunks:
                skipped.append({"filename": filename, "reason": "The file produced no usable chunks."})
                continue

            self.store.replace_document(document, chunks)
            documents.append(document)
            all_chunks.extend(chunks)

        return IngestionResult(documents=documents, chunks=all_chunks, skipped=skipped)

    def _extract_text(self, file_path: Path, suffix: str) -> str:
        if suffix in {".txt", ".md"}:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            return self._extract_pdf_text(file_path)
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    def _extract_pdf_text(self, file_path: Path) -> str:
        try:
            reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(page.strip() for page in pages if page.strip())
        except Exception as exc:  # pragma: no cover - defensive branch
            logger.exception("Failed to parse PDF %s", file_path)
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {file_path.name}") from exc
