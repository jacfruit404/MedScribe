"""LLM structuring module.

Takes raw OCR text and asks an LLM to extract it into the
`StructuredRecord` schema. Provider-agnostic: pass any callable that
implements `LLMClient.complete`, with built-in adapters for Anthropic
and OpenAI. This keeps the core pipeline testable without a live API
key (see tests/test_pipeline.py for a fake client example).
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

from .schema import StructuredRecord

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical records structuring assistant. \
You will be given raw OCR text extracted from a scanned medical document \
(intake form, referral letter, lab report, or clinical note). Extract the \
information into the JSON schema provided. Rules:

- Only extract information explicitly present in the text. Never invent or \
  infer clinical facts that are not stated.
- If a field is missing or illegible, leave it null (or an empty list).
- If OCR text looks garbled/ambiguous for a field, still fill your best \
  reading but lower `overall_confidence` accordingly.
- Return ONLY valid JSON matching the schema. No commentary.
"""

USER_PROMPT_TEMPLATE = """Schema (JSON):
{schema_json}

OCR text to structure:
\"\"\"
{ocr_text}
\"\"\"

Return the structured JSON now."""


class LLMClient(Protocol):
    """Minimal interface a structuring backend must implement."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


class AnthropicClient:
    """Adapter for the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        import anthropic  # local import: optional dependency

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if hasattr(block, "text")
        )


class OpenAIClient:
    """Adapter for the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        import openai  # local import: optional dependency

        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"


class StructuringError(RuntimeError):
    """Raised when the LLM response can't be parsed into a StructuredRecord."""


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from an LLM response,
    tolerating markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise StructuringError(f"No JSON object found in LLM response: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def structure_text(
    ocr_text: str,
    source_document: str,
    client: LLMClient,
    record_id: str | None = None,
) -> StructuredRecord:
    """Send OCR text to the LLM and parse the response into a StructuredRecord."""
    schema_json = json.dumps(StructuredRecord.model_json_schema(), indent=2)
    user_prompt = USER_PROMPT_TEMPLATE.format(schema_json=schema_json, ocr_text=ocr_text)

    raw_response = client.complete(SYSTEM_PROMPT, user_prompt)

    try:
        parsed = _extract_json(raw_response)
    except json.JSONDecodeError as exc:
        raise StructuringError(f"Failed to parse JSON from LLM response: {exc}") from exc

    # Always trust our own record of the source filename over anything
    # the LLM may have echoed back.
    parsed["source_document"] = source_document
    if record_id:
        parsed["record_id"] = record_id
    parsed["raw_ocr_text"] = ocr_text

    return StructuredRecord.model_validate(parsed)
