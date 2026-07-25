# Contributing to MedScribe

Thanks for your interest in improving MedScribe. This is an early-stage
project, so there's a lot of room to shape it.

## Getting set up

```bash
git clone <your-fork-url>
cd medscribe
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,dashboard,anthropic,openai]"
```

You'll also need system-level dependencies for OCR:

- **Tesseract OCR**: `brew install tesseract` (macOS) / `apt install tesseract-ocr` (Debian/Ubuntu)
- **Poppler** (for PDF rasterization): `brew install poppler` (macOS) / `apt install poppler-utils` (Debian/Ubuntu)

## Running tests

```bash
pytest
ruff check .
```

Tests use a `FakeLLMClient` (see `tests/conftest.py`) so the suite runs
without any API keys. OCR-path tests mock `extract_from_upload` rather than
depending on the real Tesseract binary, to keep CI fast and deterministic.

## Areas that need help

- Additional document-type prompts/schemas (referral letters, lab panels, insurance forms)
- Better preprocessing for noisy scans (deskew, adaptive threshold via OpenCV)
- A FastAPI backend as an alternative to the Streamlit dashboard
- FHIR-compatible export format
- Local/offline LLM backend (e.g., via Ollama) for on-prem deployments

## Pull requests

1. Fork, branch off `main`, keep changes focused.
2. Add or update tests for any behavior change.
3. Run `pytest` and `ruff check .` before opening a PR.
4. Describe what changed and why in the PR description.

## Reporting issues

Please include: what you ran, what you expected, what happened, and
(if relevant) a redacted sample of the OCR text or error traceback.
**Never attach real patient data to an issue or PR.**
