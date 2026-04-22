from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.domain import ChunkRecord
from app.retrieval.preprocessing import tokenize


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}")


@dataclass(slots=True)
class SentenceSpan:
    text: str
    start: int
    end: int

    @property
    def word_count(self) -> int:
        return len(self.text.split())


class SentenceChunker:
    def __init__(self, chunk_size_words: int, chunk_overlap_words: int, snippet_chars: int = 200) -> None:
        self.chunk_size_words = chunk_size_words
        self.chunk_overlap_words = chunk_overlap_words
        self.snippet_chars = snippet_chars

    def split_sentences(self, text: str) -> list[SentenceSpan]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        sentences: list[SentenceSpan] = []
        cursor = 0
        for part in SENTENCE_BOUNDARY_RE.split(normalized):
            candidate = part.strip()
            if not candidate:
                continue
            start = normalized.find(candidate, cursor)
            end = start + len(candidate)
            cursor = end
            sentences.append(SentenceSpan(text=candidate, start=start, end=end))
        return sentences

    def chunk_document(self, text: str, document_id: str, filename: str, file_type: str, created_at: str) -> list[ChunkRecord]:
        sentences = self.split_sentences(text)
        if not sentences:
            return []

        chunks: list[ChunkRecord] = []
        current: list[SentenceSpan] = []
        current_words = 0

        for sentence in sentences:
            if current and current_words + sentence.word_count > self.chunk_size_words:
                chunks.append(self._build_chunk(current, document_id, filename, file_type, len(chunks), created_at))
                current = self._overlap_tail(current)
                current_words = sum(item.word_count for item in current)

            current.append(sentence)
            current_words += sentence.word_count

        if current:
            chunks.append(self._build_chunk(current, document_id, filename, file_type, len(chunks), created_at))

        return chunks

    def _overlap_tail(self, sentences: list[SentenceSpan]) -> list[SentenceSpan]:
        if self.chunk_overlap_words <= 0:
            return []

        overlap: list[SentenceSpan] = []
        total = 0
        for sentence in reversed(sentences):
            overlap.insert(0, sentence)
            total += sentence.word_count
            if total >= self.chunk_overlap_words:
                break
        return overlap

    def _build_chunk(
        self,
        sentences: list[SentenceSpan],
        document_id: str,
        filename: str,
        file_type: str,
        chunk_index: int,
        created_at: str,
    ) -> ChunkRecord:
        text = " ".join(sentence.text for sentence in sentences).strip()
        snippet = text[: self.snippet_chars].strip()
        if len(text) > self.snippet_chars:
            snippet += "..."

        return ChunkRecord(
            id=f"{document_id}-chunk-{chunk_index}",
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            chunk_index=chunk_index,
            text=text,
            token_count=len(tokenize(text)),
            char_start=sentences[0].start,
            char_end=sentences[-1].end,
            snippet=snippet,
            created_at=created_at,
        )
