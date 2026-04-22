from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from app.models.domain import ChunkRecord, DocumentRecord


class SQLiteStore:
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
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    char_start INTEGER NOT NULL,
                    char_end INTEGER NOT NULL,
                    snippet TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_filename ON chunks(filename)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_file_type ON chunks(file_type)"
            )

    def replace_document(self, document: DocumentRecord, chunks: list[ChunkRecord]) -> None:
        with self.connect() as connection:
            existing_ids = connection.execute(
                "SELECT id FROM documents WHERE filename = ?", (document.filename,)
            ).fetchall()
            for row in existing_ids:
                connection.execute("DELETE FROM documents WHERE id = ?", (row["id"],))

            document_payload = asdict(document)
            connection.execute(
                """
                INSERT INTO documents (
                    id, filename, file_type, original_path, content_hash, size_bytes, created_at
                ) VALUES (
                    :id, :filename, :file_type, :original_path, :content_hash, :size_bytes, :created_at
                )
                """,
                document_payload,
            )

            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, filename, file_type, chunk_index, text,
                    token_count, char_start, char_end, snippet, created_at
                ) VALUES (
                    :id, :document_id, :filename, :file_type, :chunk_index, :text,
                    :token_count, :char_start, :char_end, :snippet, :created_at
                )
                """,
                [asdict(chunk) for chunk in chunks],
            )

    def list_documents(self) -> list[DocumentRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, filename, file_type, original_path, content_hash, size_bytes, created_at
                FROM documents
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def list_chunks(self) -> list[ChunkRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, document_id, filename, file_type, chunk_index, text,
                       token_count, char_start, char_end, snippet, created_at
                FROM chunks
                ORDER BY filename ASC, chunk_index ASC
                """
            ).fetchall()
        return [ChunkRecord(**dict(row)) for row in rows]

    def document_count(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        return int(row["count"])

    def chunk_count(self) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()
        return int(row["count"])
