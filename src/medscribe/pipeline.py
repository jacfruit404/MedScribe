"""End-to-end pipeline: upload bytes -> OCR -> LLM structuring -> storage.

This module wires the individual steps together so both the CLI and
the dashboard call one function instead of duplicating orchestration
logic.
"""

from __future__ import annotations

import logging

from .llm import LLMClient, structure_text
from .ocr import OCRResult, extract_from_upload
from .schema import StructuredRecord
from .storage import RecordStore

logger = logging.getLogger(__name__)


def run_pipeline(
    file_bytes: bytes,
    filename: str,
    llm_client: LLMClient,
    store: RecordStore | None = None,
) -> tuple[StructuredRecord, OCRResult]:
    """Run the full OCR -> LLM structuring pipeline on an uploaded file.

    Returns the structured record and the raw OCR result (useful for
    displaying OCR confidence / raw text alongside the structured
    fields in the dashboard). If `store` is provided, the record is
    persisted and its `record_id` is set.
    """
    logger.info("Running OCR on %s", filename)
    ocr_result = extract_from_upload(file_bytes, filename)

    logger.info("Structuring OCR text via LLM for %s", filename)
    record = structure_text(
        ocr_text=ocr_result.full_text,
        source_document=filename,
        client=llm_client,
    )

    # If OCR confidence was low, reflect that in the overall record
    # confidence even if the LLM was confident about its reading.
    record.overall_confidence = min(
        record.overall_confidence, max(ocr_result.mean_confidence / 100.0, 0.01)
    )

    if store is not None:
        store.save(record)

    return record, ocr_result
