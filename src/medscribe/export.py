"""Export structured records to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json

from .schema import StructuredRecord


def to_json(records: list[StructuredRecord]) -> str:
    """Serialize a list of records to a pretty-printed JSON array."""
    return json.dumps([r.model_dump() for r in records], indent=2, default=str)


def to_csv(records: list[StructuredRecord]) -> str:
    """Serialize a list of records to a flat CSV string."""
    if not records:
        return ""

    rows = [r.flat_dict() for r in records]
    fieldnames = list(rows[0].keys())

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_json(records: list[StructuredRecord], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(to_json(records))


def write_csv(records: list[StructuredRecord], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(to_csv(records))
