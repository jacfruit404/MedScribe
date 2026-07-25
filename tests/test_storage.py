from medscribe.schema import PatientInfo, StructuredRecord
from medscribe.storage import RecordStore


def test_save_and_get_roundtrip(tmp_path):
    store = RecordStore(db_path=tmp_path / "test.db")
    record = StructuredRecord(source_document="a.pdf", patient=PatientInfo(full_name="Jane Doe"))

    record_id = store.save(record)
    assert record_id

    fetched = store.get(record_id)
    assert fetched is not None
    assert fetched.patient.full_name == "Jane Doe"


def test_list_all_returns_saved_records(tmp_path):
    store = RecordStore(db_path=tmp_path / "test.db")
    store.save(StructuredRecord(source_document="a.pdf"))
    store.save(StructuredRecord(source_document="b.pdf"))

    all_records = store.list_all()
    assert len(all_records) == 2


def test_update_existing_record(tmp_path):
    store = RecordStore(db_path=tmp_path / "test.db")
    record = StructuredRecord(source_document="a.pdf", patient=PatientInfo(full_name="Jane"))
    record_id = store.save(record)

    record.patient.full_name = "Jane Updated"
    store.save(record)

    fetched = store.get(record_id)
    assert fetched.patient.full_name == "Jane Updated"
    assert len(store.list_all()) == 1


def test_delete_record(tmp_path):
    store = RecordStore(db_path=tmp_path / "test.db")
    record_id = store.save(StructuredRecord(source_document="a.pdf"))

    store.delete(record_id)
    assert store.get(record_id) is None
