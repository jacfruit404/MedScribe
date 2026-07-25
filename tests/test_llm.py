import pytest

from medscribe.llm import StructuringError, _extract_json, structure_text


def test_structure_text_happy_path(fake_llm_client):
    record = structure_text(
        ocr_text="Patient: Jane Doe, DOB 1980-01-01...",
        source_document="intake.pdf",
        client=fake_llm_client,
    )
    assert record.patient.full_name == "Jane Doe"
    assert record.source_document == "intake.pdf"
    assert record.raw_ocr_text.startswith("Patient: Jane Doe")
    assert len(record.diagnoses) == 1
    assert record.diagnoses[0].icd10_code == "I10"


def test_structure_text_sets_record_id(fake_llm_client):
    record = structure_text(
        ocr_text="...", source_document="x.pdf", client=fake_llm_client, record_id="abc-123"
    )
    assert record.record_id == "abc-123"


def test_extract_json_handles_markdown_fence():
    text = '```json\n{"a": 1}\n```'
    assert _extract_json(text) == {"a": 1}


def test_extract_json_raises_on_garbage():
    with pytest.raises(StructuringError):
        _extract_json("not json at all")
