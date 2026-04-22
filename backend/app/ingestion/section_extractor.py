from __future__ import annotations

import re

from app.core.config import Settings
from app.retrieval.preprocessing import tokenize
from app.schemas.domain import PageRecord, SectionRecord
from app.utils.text import normalize_line, preview, stem_filename


MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
NUMBERED_HEADING_RE = re.compile(r"^(?:\d+(?:\.\d+){0,3}|[A-Z])[\.\)]?\s+.+$")


class SectionExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract(self, document_id: str, filename: str, file_type: str, pages: list[PageRecord]) -> list[SectionRecord]:
        flattened: list[tuple[int, str]] = []
        for page in pages:
            lines = [normalize_line(line) for line in page.text.splitlines()]
            for line in lines:
                if line:
                    flattened.append((page.page_number, line))

        if not flattened:
            return []

        headings: list[tuple[int, int, str, int]] = []
        for index, (page_number, line) in enumerate(flattened):
            heading = self._detect_heading(line=line, file_type=file_type)
            if heading is not None:
                headings.append((index, page_number, heading[0], heading[1]))

        if not headings:
            return self._fallback_sections(document_id=document_id, filename=filename, pages=pages)

        sections: list[SectionRecord] = []
        stack: list[tuple[int, str, str]] = []

        if headings[0][0] > 0:
            preface_lines = [line for _, line in flattened[: headings[0][0]]]
            preface_text = "\n".join(preface_lines).strip()
            if preface_text:
                section_id = f"{document_id}-section-1"
                title = "Overview"
                sections.append(
                    SectionRecord(
                        id=section_id,
                        document_id=document_id,
                        title=title,
                        normalized_title=title.lower(),
                        heading_level=1,
                        page_number=1,
                        start_page=1,
                        end_page=max(1, flattened[headings[0][0] - 1][0]),
                        parent_section_id=None,
                        heading_path=title,
                        text=preface_text,
                        snippet=preview(preface_text, self.settings.chunk_preview_chars),
                        word_count=len(preface_text.split()),
                        token_count=len(tokenize(preface_text)),
                    )
                )

        next_index = len(sections) + 1
        for heading_idx, (start_offset, start_page, title, level) in enumerate(headings):
            end_offset = headings[heading_idx + 1][0] if heading_idx + 1 < len(headings) else len(flattened)
            body_lines = [line for _, line in flattened[start_offset + 1 : end_offset]]
            body_text = "\n".join(body_lines).strip()
            text = "\n".join(filter(None, [title, body_text])).strip()
            if not text:
                continue

            while stack and stack[-1][0] >= level:
                stack.pop()

            parent_section_id = stack[-1][1] if stack else None
            path_parts = [item[2] for item in stack] + [title]
            section_id = f"{document_id}-section-{next_index}"
            section = SectionRecord(
                id=section_id,
                document_id=document_id,
                title=title,
                normalized_title=title.lower(),
                heading_level=level,
                page_number=start_page,
                start_page=start_page,
                end_page=flattened[end_offset - 1][0],
                parent_section_id=parent_section_id,
                heading_path=" / ".join(path_parts),
                text=text,
                snippet=preview(body_text or title, self.settings.chunk_preview_chars),
                word_count=len(text.split()),
                token_count=len(tokenize(text)),
            )
            sections.append(section)
            stack.append((level, section.id, title))
            next_index += 1

        return sections or self._fallback_sections(document_id=document_id, filename=filename, pages=pages)

    def _fallback_sections(self, document_id: str, filename: str, pages: list[PageRecord]) -> list[SectionRecord]:
        base_title = stem_filename(filename).title() or filename
        sections: list[SectionRecord] = []
        for page in pages:
            title = page.title or f"{base_title} Page {page.page_number}"
            sections.append(
                SectionRecord(
                    id=f"{document_id}-section-{page.page_number}",
                    document_id=document_id,
                    title=title,
                    normalized_title=title.lower(),
                    heading_level=1,
                    page_number=page.page_number,
                    start_page=page.page_number,
                    end_page=page.page_number,
                    parent_section_id=None,
                    heading_path=title,
                    text=page.text,
                    snippet=page.snippet,
                    word_count=page.word_count,
                    token_count=page.token_count,
                )
            )
        return sections

    def _detect_heading(self, line: str, file_type: str) -> tuple[str, int] | None:
        markdown_match = MARKDOWN_HEADING_RE.match(line)
        if markdown_match:
            hashes, title = markdown_match.groups()
            return normalize_line(title), len(hashes)

        if len(line) > 96 or len(line.split()) > 12 or line.endswith((".", "?", "!", ":")):
            return None

        if NUMBERED_HEADING_RE.match(line):
            number_token = line.split()[0]
            level = min(number_token.count(".") + 1, 4)
            return line, level

        alpha_words = [word for word in line.split() if any(char.isalpha() for char in word)]
        if len(alpha_words) < 2:
            return None

        uppercase_ratio = sum(word.isupper() for word in alpha_words) / len(alpha_words)
        title_case_ratio = sum(word[:1].isupper() for word in alpha_words) / len(alpha_words)
        if uppercase_ratio >= 0.8 or title_case_ratio >= 0.9:
            return line, 2 if file_type == "pdf" else 1

        return None
