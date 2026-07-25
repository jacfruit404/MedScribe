"""Shared test fixtures: a fake LLM client so tests don't need API keys."""

from __future__ import annotations

import json

import pytest


class FakeLLMClient:
    """A stand-in LLM client that returns a fixed, valid StructuredRecord JSON.

    Lets pipeline/dashboard logic be tested without network calls or API keys.
    """

    def __init__(self, response: dict | None = None):
        self.response = response or {
            "source_document": "placeholder.pdf",
            "patient": {
                "full_name": "Jane Doe",
                "date_of_birth": "1980-01-01",
                "patient_id": "12345",
                "sex": "F",
                "phone": None,
                "address": None,
            },
            "visit": {
                "visit_date": "2026-07-20",
                "provider_name": "Dr. Smith",
                "facility_name": "Riverside Clinic",
                "reason_for_visit": "Annual checkup",
            },
            "diagnoses": [{"description": "Hypertension", "icd10_code": "I10", "confidence": 0.9}],
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "daily", "confidence": 0.95}
            ],
            "allergies": ["Penicillin"],
            "notes": "Patient reports feeling well.",
            "overall_confidence": 0.92,
        }
        self.last_system_prompt: str | None = None
        self.last_user_prompt: str | None = None

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return json.dumps(self.response)


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()
