"""Lightweight persistence layer for structured records.

Uses SQLite by default (zero-config, file-based) so the MVP runs
without any external database. The record itself is stored as JSON
in a single column plus a few indexed columns for querying, which
keeps this adaptable to schema changes without migrations.

Swap `db_path=":memory:"` for tests, or point at a real file for
the dashboard to persist across sessions.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from .schema import StructuredRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY,
    source_document TEXT NOT NULL,
    patient_full_name TEXT,
    visit_date TEXT,
    overall_confidence REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    data_json TEXT NOT NULL
);
"""


class RecordStore:
    """A tiny SQLite-backed store for StructuredRecord objects."""

    def __init__(self, db_path: str | Path = "medscribe.db"):
        self.db_path = str(db_path)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save(self, record: StructuredRecord) -> str:
        """Insert or update a record. Returns the record_id."""
        if not record.record_id:
            record.record_id = str(uuid.uuid4())

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO records
                    (record_id, source_document, patient_full_name, visit_date,
                     overall_confidence, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_id) DO UPDATE SET
                    source_document=excluded.source_document,
                    patient_full_name=excluded.patient_full_name,
                    visit_date=excluded.visit_date,
                    overall_confidence=excluded.overall_confidence,
                    data_json=excluded.data_json
                """,
                (
                    record.record_id,
                    record.source_document,
                    record.patient.full_name,
                    record.visit.visit_date,
                    record.overall_confidence,
                    record.model_dump_json(),
                ),
            )
        return record.record_id

    def get(self, record_id: str) -> StructuredRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data_json FROM records WHERE record_id = ?", (record_id,)
            ).fetchone()
        if row is None:
            return None
        return StructuredRecord.model_validate(json.loads(row[0]))

    def list_all(self) -> list[StructuredRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data_json FROM records ORDER BY created_at DESC"
            ).fetchall()
        return [StructuredRecord.model_validate(json.loads(r[0])) for r in rows]

    def delete(self, record_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM records WHERE record_id = ?", (record_id,))
