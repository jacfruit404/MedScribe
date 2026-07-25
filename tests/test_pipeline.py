from unittest.mock import patch

from medscribe.ocr import OCRPage, OCRResult
from medscribe.pipeline import run_pipeline
from medscribe.storage import RecordStore


def test_run_pipeline_end_to_end(fake_llm_client, tmp_path):
    fake_ocr_result = OCRResult(
        source_name="intake.pdf",
        pages=[OCRPage(page_number=1, text="Patient: Jane Doe...", mean_confidence=88.0)],
    )

    with patch("medscribe.pipeline.extract_from_upload", return_value=fake_ocr_result):
        store = RecordStore(db_path=tmp_path / "test.db")
        record, ocr_result = run_pipeline(
            file_bytes=b"fake-pdf-bytes",
            filename="intake.pdf",
            llm_client=fake_llm_client,
            store=store,
        )

    assert record.record_id is not None
    assert record.patient.full_name == "Jane Doe"
    assert ocr_result.mean_confidence == 88.0
    # record_id should be persisted
    assert store.get(record.record_id) is not None


def test_run_pipeline_lowers_confidence_on_poor_ocr(fake_llm_client, tmp_path):
    fake_ocr_result = OCRResult(
        source_name="blurry.pdf",
        pages=[OCRPage(page_number=1, text="???", mean_confidence=20.0)],
    )

    with patch("medscribe.pipeline.extract_from_upload", return_value=fake_ocr_result):
        record, _ = run_pipeline(
            file_bytes=b"fake-pdf-bytes",
            filename="blurry.pdf",
            llm_client=fake_llm_client,
            store=None,
        )

    # LLM claimed 0.92 confidence, but OCR was only 20% -> should be capped down
    assert record.overall_confidence <= 0.2
