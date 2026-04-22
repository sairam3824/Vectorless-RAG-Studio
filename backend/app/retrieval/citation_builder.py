from __future__ import annotations

from app.core.config import Settings
from app.schemas.api import CitationResponse
from app.schemas.domain import RetrievedPassage
from app.utils.text import preview


class CitationBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build(self, passages: list[RetrievedPassage]) -> list[CitationResponse]:
        citations: list[CitationResponse] = []
        for passage in passages:
            unit = passage.unit
            citations.append(
                CitationResponse(
                    document_id=unit.document_id,
                    filename=unit.filename,
                    page_number=unit.page_number,
                    section_title=unit.section_title,
                    heading_path=unit.heading_path,
                    snippet=preview(unit.snippet or unit.text, self.settings.chunk_preview_chars),
                    unit_type=unit.unit_type,
                    unit_id=unit.unit_id,
                )
            )
        return citations
