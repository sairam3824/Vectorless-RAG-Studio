from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from app.schemas.domain import DocumentRecord, PageRecord, RetrievalUnit, SectionRecord


class SQLiteRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL UNIQUE,
                    file_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    page_count INTEGER NOT NULL,
                    section_count INTEGER NOT NULL,
                    indexing_status TEXT NOT NULL,
                    last_indexed_at TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    title TEXT,
                    text TEXT NOT NULL,
                    snippet TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    char_count INTEGER NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sections (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    normalized_title TEXT NOT NULL,
                    heading_level INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    start_page INTEGER NOT NULL,
                    end_page INTEGER NOT NULL,
                    parent_section_id TEXT,
                    heading_path TEXT NOT NULL,
                    text TEXT NOT NULL,
                    snippet TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sections_document_id ON sections(document_id)")

    def replace_document_bundle(
        self,
        document: DocumentRecord,
        pages: list[PageRecord],
        sections: list[SectionRecord],
    ) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM documents WHERE filename = ?", (document.filename,))
            connection.execute(
                """
                INSERT INTO documents (
                    id, filename, file_type, title, storage_path, content_hash, size_bytes,
                    page_count, section_count, indexing_status, last_indexed_at, error_message,
                    created_at, updated_at
                ) VALUES (
                    :id, :filename, :file_type, :title, :storage_path, :content_hash, :size_bytes,
                    :page_count, :section_count, :indexing_status, :last_indexed_at, :error_message,
                    :created_at, :updated_at
                )
                """,
                asdict(document),
            )
            connection.executemany(
                """
                INSERT INTO pages (
                    id, document_id, page_number, label, title, text, snippet, word_count, token_count, char_count
                ) VALUES (
                    :id, :document_id, :page_number, :label, :title, :text, :snippet, :word_count, :token_count, :char_count
                )
                """,
                [asdict(page) for page in pages],
            )
            connection.executemany(
                """
                INSERT INTO sections (
                    id, document_id, title, normalized_title, heading_level, page_number,
                    start_page, end_page, parent_section_id, heading_path, text, snippet,
                    word_count, token_count
                ) VALUES (
                    :id, :document_id, :title, :normalized_title, :heading_level, :page_number,
                    :start_page, :end_page, :parent_section_id, :heading_path, :text, :snippet,
                    :word_count, :token_count
                )
                """,
                [asdict(section) for section in sections],
            )

    def list_documents(self) -> list[DocumentRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, filename, file_type, title, storage_path, content_hash, size_bytes,
                       page_count, section_count, indexing_status, last_indexed_at, error_message,
                       created_at, updated_at
                FROM documents
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def list_document_ids(self) -> list[str]:
        return [document.id for document in self.list_documents()]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, filename, file_type, title, storage_path, content_hash, size_bytes,
                       page_count, section_count, indexing_status, last_indexed_at, error_message,
                       created_at, updated_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
        return DocumentRecord(**dict(row)) if row else None

    def get_document_by_filename(self, filename: str) -> DocumentRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, filename, file_type, title, storage_path, content_hash, size_bytes,
                       page_count, section_count, indexing_status, last_indexed_at, error_message,
                       created_at, updated_at
                FROM documents
                WHERE filename = ?
                """,
                (filename,),
            ).fetchone()
        return DocumentRecord(**dict(row)) if row else None

    def list_pages(self, document_id: str) -> list[PageRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, page_number, label, title, text, snippet, word_count, token_count, char_count
                FROM pages
                WHERE document_id = ?
                ORDER BY page_number ASC
                """,
                (document_id,),
            ).fetchall()
        return [PageRecord(**dict(row)) for row in rows]

    def list_sections(self, document_id: str) -> list[SectionRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, title, normalized_title, heading_level, page_number,
                       start_page, end_page, parent_section_id, heading_path, text, snippet,
                       word_count, token_count
                FROM sections
                WHERE document_id = ?
                ORDER BY start_page ASC, heading_level ASC, title ASC
                """,
                (document_id,),
            ).fetchall()
        return [SectionRecord(**dict(row)) for row in rows]

    def list_retrieval_units(self, document_ids: list[str] | None = None) -> list[RetrievalUnit]:
        document_filter = ""
        parameters: list[str] = []
        if document_ids:
            placeholders = ", ".join("?" for _ in document_ids)
            document_filter = f"WHERE d.id IN ({placeholders})"
            parameters.extend(document_ids)

        units: list[RetrievalUnit] = []
        with self.connect() as connection:
            page_rows = connection.execute(
                f"""
                SELECT
                    p.id AS unit_id,
                    d.id AS document_id,
                    d.filename AS filename,
                    d.title AS document_title,
                    d.file_type AS file_type,
                    'page' AS unit_type,
                    p.page_number AS page_number,
                    p.page_number AS start_page,
                    p.page_number AS end_page,
                    NULL AS section_id,
                    p.title AS section_title,
                    NULL AS heading_level,
                    NULL AS heading_path,
                    COALESCE(p.title, d.title, p.label) AS title,
                    p.text AS text,
                    p.snippet AS snippet
                FROM pages p
                JOIN documents d ON d.id = p.document_id
                {document_filter}
                ORDER BY d.filename ASC, p.page_number ASC
                """,
                parameters,
            ).fetchall()
            section_rows = connection.execute(
                f"""
                SELECT
                    s.id AS unit_id,
                    d.id AS document_id,
                    d.filename AS filename,
                    d.title AS document_title,
                    d.file_type AS file_type,
                    'section' AS unit_type,
                    s.page_number AS page_number,
                    s.start_page AS start_page,
                    s.end_page AS end_page,
                    s.id AS section_id,
                    s.title AS section_title,
                    s.heading_level AS heading_level,
                    s.heading_path AS heading_path,
                    s.title AS title,
                    s.text AS text,
                    s.snippet AS snippet
                FROM sections s
                JOIN documents d ON d.id = s.document_id
                {document_filter}
                ORDER BY d.filename ASC, s.start_page ASC, s.heading_level ASC
                """,
                parameters,
            ).fetchall()

        for row in [*section_rows, *page_rows]:
            units.append(RetrievalUnit(**dict(row)))
        return units

    def delete_document(self, document_id: str) -> DocumentRecord | None:
        existing = self.get_document(document_id)
        if not existing:
            return None
        with self.connect() as connection:
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return existing

    def set_all_documents_status(self, status: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE documents SET indexing_status = ?, error_message = NULL", (status,))

    def mark_documents_indexed(self, document_ids: list[str], indexed_at: str) -> None:
        if not document_ids:
            return
        placeholders = ", ".join("?" for _ in document_ids)
        with self.connect() as connection:
            connection.execute(
                f"""
                UPDATE documents
                SET indexing_status = 'indexed', last_indexed_at = ?, updated_at = ?, error_message = NULL
                WHERE id IN ({placeholders})
                """,
                [indexed_at, indexed_at, *document_ids],
            )

    def counts(self) -> tuple[int, int, int]:
        with self.connect() as connection:
            documents = int(connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"])
            pages = int(connection.execute("SELECT COUNT(*) AS count FROM pages").fetchone()["count"])
            sections = int(connection.execute("SELECT COUNT(*) AS count FROM sections").fetchone()["count"])
        return documents, pages, sections
