from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.ingestion.document_parser import DocumentParser
from app.ingestion.section_extractor import SectionExtractor


def test_markdown_parser_extracts_sections(tmp_path: Path) -> None:
    source = tmp_path / "handbook.md"
    source.write_text(
        "\n".join(
            [
                "# Northstar Handbook",
                "",
                "## Remote Operations",
                "Remote employees on primary on-call must acknowledge critical incidents within 15 minutes.",
                "Escalations move to a backup engineer after 30 minutes.",
                "",
                "## Release Management",
                "Production deployments require automated tests, a release checklist, and an approver sign-off.",
                "",
                "## Customer Communications",
                "Postmortems for customer-visible incidents are published within three business days.",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings()
    parser = DocumentParser(settings=settings, section_extractor=SectionExtractor(settings))
    pages, sections, title, content_hash = parser.parse(
        document_id=str(uuid4()),
        filename=source.name,
        file_type="md",
        path=source,
    )

    assert len(pages) == 1
    assert title == "Northstar Handbook"
    assert content_hash
    assert [section.title for section in sections][:3] == [
        "Northstar Handbook",
        "Remote Operations",
        "Release Management",
    ]
    assert any(section.heading_path.endswith("Customer Communications") for section in sections)


def test_text_parser_creates_synthetic_pages(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    paragraph = "Lexical retrieval ranks pages and sections without relying on embeddings."
    source.write_text("\n\n".join([paragraph for _ in range(120)]), encoding="utf-8")

    settings = Settings()
    parser = DocumentParser(settings=settings, section_extractor=SectionExtractor(settings))
    pages, _, _, _ = parser.parse(
        document_id=str(uuid4()),
        filename=source.name,
        file_type="txt",
        path=source,
    )

    assert len(pages) >= 2
    assert all(page.text for page in pages)
