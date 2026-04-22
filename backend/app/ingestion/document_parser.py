from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from pypdf import PdfReader

from app.core.config import Settings
from app.ingestion.section_extractor import SectionExtractor
from app.retrieval.preprocessing import tokenize
from app.schemas.domain import PageRecord, SectionRecord
from app.utils.text import normalize_block, normalize_line, preview, stem_filename


logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = {"pdf", "txt", "md"}


class DocumentParser:
    def __init__(self, settings: Settings, section_extractor: SectionExtractor) -> None:
        self.settings = settings
        self.section_extractor = section_extractor

    def parse(self, document_id: str, filename: str, file_type: str, path: Path) -> tuple[list[PageRecord], list[SectionRecord], str, str]:
        if file_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}")

        pages = self._parse_pdf(document_id, path) if file_type == "pdf" else self._parse_text_like(document_id, path)
        if not pages:
            raise ValueError("No extractable text found in the uploaded document.")

        sections = self.section_extractor.extract(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            pages=pages,
        )
        title = self._infer_title(filename=filename, pages=pages, sections=sections)
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        return pages, sections, title, content_hash

    def _parse_pdf(self, document_id: str, path: Path) -> list[PageRecord]:
        try:
            reader = PdfReader(str(path))
        except Exception as exc:  # pragma: no cover - defensive branch
            logger.exception("Failed to open PDF %s", path)
            raise ValueError(f"Failed to parse PDF: {path.name}") from exc

        pages: list[PageRecord] = []
        for index, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            text = normalize_block(raw_text)
            if not text:
                continue
            title = self._page_title(text)
            pages.append(
                PageRecord(
                    id=f"{document_id}-page-{index}",
                    document_id=document_id,
                    page_number=index,
                    label=f"Page {index}",
                    title=title,
                    text=text,
                    snippet=preview(text, self.settings.chunk_preview_chars),
                    word_count=len(text.split()),
                    token_count=len(tokenize(text)),
                    char_count=len(text),
                )
            )
        return pages

    def _parse_text_like(self, document_id: str, path: Path) -> list[PageRecord]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        normalized = normalize_block(text)
        if not normalized:
            return []

        if "\f" in text:
            raw_pages = [normalize_block(part) for part in text.split("\f")]
            page_texts = [part for part in raw_pages if part]
        else:
            page_texts = self._paginate_text(normalized)

        pages: list[PageRecord] = []
        for index, page_text in enumerate(page_texts, start=1):
            pages.append(
                PageRecord(
                    id=f"{document_id}-page-{index}",
                    document_id=document_id,
                    page_number=index,
                    label=f"Page {index}",
                    title=self._page_title(page_text),
                    text=page_text,
                    snippet=preview(page_text, self.settings.chunk_preview_chars),
                    word_count=len(page_text.split()),
                    token_count=len(tokenize(page_text)),
                    char_count=len(page_text),
                )
            )
        return pages

    def _paginate_text(self, text: str) -> list[str]:
        paragraphs = [block.strip() for block in text.split("\n\n") if block.strip()]
        pages: list[str] = []
        current: list[str] = []
        current_words = 0
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            if current and current_words + paragraph_words > self.settings.synthetic_page_words:
                pages.append("\n\n".join(current))
                current = []
                current_words = 0
            current.append(paragraph)
            current_words += paragraph_words
        if current:
            pages.append("\n\n".join(current))
        return pages or [text]

    def _page_title(self, text: str) -> str | None:
        for line in text.splitlines():
            candidate = normalize_line(line)
            if len(candidate.split()) <= 12 and len(candidate) <= 90:
                if candidate.startswith("#"):
                    return candidate.lstrip("#").strip()
                if candidate.isupper() or candidate.istitle():
                    return candidate
        return None

    def _infer_title(self, filename: str, pages: list[PageRecord], sections: list[SectionRecord]) -> str:
        if sections:
            first_title = sections[0].title.strip()
            if first_title and first_title.lower() != "overview":
                return first_title
        if pages and pages[0].title:
            return pages[0].title
        return stem_filename(filename).title() or filename
