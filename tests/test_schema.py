from medscribe.schema import Diagnosis, Medication, PatientInfo, StructuredRecord, VisitInfo


def test_structured_record_defaults():
    record = StructuredRecord(source_document="scan.pdf")
    assert record.patient == PatientInfo()
    assert record.visit == VisitInfo()
    assert record.diagnoses == []
    assert record.medications == []
    assert record.overall_confidence == 1.0


def test_flat_dict_joins_lists():
    record = StructuredRecord(
        source_document="scan.pdf",
        patient=PatientInfo(full_name="Jane Doe"),
        diagnoses=[Diagnosis(description="Hypertension"), Diagnosis(description="Diabetes")],
        medications=[Medication(name="Metformin", dosage="500mg", frequency="daily")],
        allergies=["Penicillin", "Latex"],
    )
    flat = record.flat_dict()
    assert flat["patient_full_name"] == "Jane Doe"
    assert flat["diagnoses"] == "Hypertension; Diabetes"
    assert flat["medications"] == "Metformin 500mg daily"
    assert flat["allergies"] == "Penicillin; Latex"


def test_confidence_bounds_enforced():
    diag = Diagnosis(description="x", confidence=0.5)
    assert 0.0 <= diag.confidence <= 1.0
