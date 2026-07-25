# MedScribe

An open-source AI research assistant for medical practices. Upload a scanned
PDF or image, extract text with Tesseract OCR, structure it into clean
fields with an LLM, review/correct mistakes in a dashboard, and export to
JSON, CSV, or a database.

```
User uploads PDF/image scan
        │
        ▼
   OCR (Tesseract)  ──────────► raw text
        │
        ▼
LLM structures information  ──► StructuredRecord (patient, visit,
        │                       diagnoses, medications, allergies...)
        ▼
Results appear in a dashboard (Streamlit)
        │
        ▼
User reviews & edits mistakes
        │
        ▼
Export as JSON / CSV / SQLite database
```

> **⚠️ Disclaimer — read before using with real patient data**
> This is a research/demo tool, not a certified medical device, and it is
> not a substitute for clinical judgment. OCR and LLM extraction can and
> will make mistakes — every field must be reviewed by a qualified person
> before being used clinically or entered into a record system. This
> project does not provide HIPAA compliance out of the box: if you plan to
> process real Protected Health Information (PHI), you are responsible for
> your own risk assessment, BAAs with any third-party LLM provider you
> use, encryption at rest/in transit, and access controls. See
> [Handling PHI](#handling-phi) below.

## Features

- **OCR** on scanned PDFs and images via [Tesseract](https://github.com/tesseract-ocr/tesseract) (through `pytesseract` + `pdf2image`)
- **LLM structuring** into a typed schema (patient info, visit info, diagnoses, medications, allergies, notes) — pluggable between Anthropic and OpenAI
- **Confidence scoring** that combines OCR confidence with LLM-reported confidence, so low-quality scans are flagged for review
- **Review dashboard** (Streamlit) with an editable table for human-in-the-loop correction
- **Export** to JSON, CSV, or a local SQLite database
- **CLI** for batch/scripted processing without the dashboard

## Quick start

### 1. Install system dependencies

```bash
# macOS
brew install tesseract poppler

# Debian/Ubuntu
sudo apt-get install tesseract-ocr poppler-utils
```

### 2. Install the Python package

```bash
git clone https://github.com/<your-org>/medscribe.git
cd medscribe
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dashboard,anthropic,openai]"
```

### 3. Set an API key

```bash
cp .env.example .env
# edit .env and add ANTHROPIC_API_KEY or OPENAI_API_KEY
export $(grep -v '^#' .env | xargs)
```

### 4. Run the dashboard

```bash
streamlit run app/dashboard.py
```

Upload a scanned document, click **Run OCR + Structuring**, review/edit the
extracted fields, then export as JSON or CSV.

### Or use the CLI

```bash
medscribe process path/to/scan.pdf --provider anthropic --out record.json --csv record.csv
```

## Project layout

```
medscribe/
├── src/medscribe/
│   ├── ocr.py          # Tesseract-based OCR (PDF + image input)
│   ├── llm.py          # LLM structuring (Anthropic / OpenAI adapters)
│   ├── schema.py        # Pydantic schema for structured records
│   ├── storage.py       # SQLite persistence
│   ├── export.py        # JSON / CSV export
│   ├── pipeline.py      # Orchestrates OCR -> LLM -> storage
│   └── cli.py            # `medscribe process ...` command
├── app/dashboard.py      # Streamlit review dashboard
├── tests/                # pytest suite (LLM calls are mocked)
└── .github/workflows/ci.yml
```

## Extending the schema

`src/medscribe/schema.py` defines a generic clinical schema (patient info,
visit info, diagnoses, medications, allergies, notes). If your practice
uses specific document types (e.g., referral letters, lab panels, insurance
forms), add fields there and adjust the prompt in `llm.py` accordingly —
the LLM is instructed to only extract what's explicitly present in the OCR
text, never to infer clinical facts.

## Handling PHI

This project stores whatever you give it, including the raw OCR text, in a
local SQLite file by default. Before using it with real patient data:

- Run it on infrastructure you control; don't send PHI to any LLM API
  without a Business Associate Agreement (BAA) in place with that provider.
- Encrypt the SQLite file / database at rest, and restrict filesystem
  access to the dashboard host.
- Turn on audit logging for who accessed/edited which records (not
  included in this MVP — see [Contributing](CONTRIBUTING.md)).
- Have a retention/deletion policy; `RecordStore.delete()` is provided but
  not automated.

## Testing

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

The test suite uses a `FakeLLMClient` fixture, so it runs without any API
keys or a real Tesseract install for the pipeline logic; OCR-dependent
paths are mocked at the module boundary.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
