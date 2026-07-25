import json

from medscribe.export import to_csv, to_json
from medscribe.schema import PatientInfo, StructuredRecord


def make_record(name: str) -> StructuredRecord:
    return StructuredRecord(source_document=f"{name}.pdf", patient=PatientInfo(full_name=name))


def test_to_json_roundtrip():
    records = [make_record("Jane"), make_record("John")]
    output = to_json(records)
    parsed = json.loads(output)
    assert len(parsed) == 2
    assert parsed[0]["patient"]["full_name"] == "Jane"


def test_to_csv_has_header_and_rows():
    records = [make_record("Jane"), make_record("John")]
    output = to_csv(records)
    lines = output.strip().splitlines()
    assert len(lines) == 3  # header + 2 rows
    assert "patient_full_name" in lines[0]


def test_to_csv_empty_list():
    assert to_csv([]) == ""
