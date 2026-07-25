"""Structured data models for extracted medical record information.

These schemas are intentionally generic (not tied to a specific EHR
vendor). They cover common fields found on intake forms, referral
letters, lab reports, and clinical notes. Extend as needed for your
practice's document types.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Medication(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Diagnosis(BaseModel):
    description: str
    icd10_code: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class PatientInfo(BaseModel):
    full_name: str | None = None
    date_of_birth: str | None = None
    patient_id: str | None = None
    sex: str | None = None
    phone: str | None = None
    address: str | None = None


class VisitInfo(BaseModel):
    visit_date: str | None = None
    provider_name: str | None = None
    facility_name: str | None = None
    reason_for_visit: str | None = None


class StructuredRecord(BaseModel):
    """The full structured output produced by the LLM structuring step."""

    record_id: str | None = None
    source_document: str
    patient: PatientInfo = Field(default_factory=PatientInfo)
    visit: VisitInfo = Field(default_factory=VisitInfo)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    notes: str | None = None
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_ocr_text: str | None = Field(
        default=None,
        description="Original OCR text, kept for auditing / manual correction.",
    )

    def flat_dict(self) -> dict:
        """Flatten nested fields into a single-level dict for CSV export."""
        return {
            "record_id": self.record_id,
            "source_document": self.source_document,
            "patient_full_name": self.patient.full_name,
            "patient_dob": self.patient.date_of_birth,
            "patient_id": self.patient.patient_id,
            "patient_sex": self.patient.sex,
            "patient_phone": self.patient.phone,
            "patient_address": self.patient.address,
            "visit_date": self.visit.visit_date,
            "provider_name": self.visit.provider_name,
            "facility_name": self.visit.facility_name,
            "reason_for_visit": self.visit.reason_for_visit,
            "diagnoses": "; ".join(d.description for d in self.diagnoses),
            "medications": "; ".join(
                f"{m.name} {m.dosage or ''} {m.frequency or ''}".strip()
                for m in self.medications
            ),
            "allergies": "; ".join(self.allergies),
            "notes": self.notes,
            "overall_confidence": self.overall_confidence,
        }
