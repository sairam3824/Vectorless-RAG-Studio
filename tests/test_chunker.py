from app.ingestion.chunker import SentenceChunker


def test_sentence_chunker_creates_overlap() -> None:
    text = (
        "Alpha introduces the product. "
        "Bravo explains authentication. "
        "Charlie covers deployment checklists. "
        "Delta documents rollback steps. "
        "Echo lists support contacts."
    )

    chunker = SentenceChunker(chunk_size_words=7, chunk_overlap_words=3, snippet_chars=80)
    chunks = chunker.chunk_document(
        text=text,
        document_id="doc-1",
        filename="guide.md",
        file_type="md",
        created_at="2026-01-01T00:00:00+00:00",
    )

    assert len(chunks) >= 2
    assert "deployment checklists" in chunks[1].text.lower() or "authentication" in chunks[1].text.lower()
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
