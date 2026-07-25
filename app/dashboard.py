"""MedScribe review dashboard (Streamlit).

Run with:
    streamlit run app/dashboard.py

Flow: upload PDF/image -> OCR + LLM structuring runs -> review/edit
extracted fields in an editable table -> export as JSON / CSV, or
persist to the SQLite database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow running via `streamlit run app/dashboard.py` from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from medscribe.export import to_json
from medscribe.llm import AnthropicClient, OpenAIClient
from medscribe.pipeline import run_pipeline
from medscribe.schema import StructuredRecord
from medscribe.storage import RecordStore

st.set_page_config(page_title="MedScribe", layout="wide")

if "records" not in st.session_state:
    st.session_state.records: list[StructuredRecord] = []
if "ocr_debug" not in st.session_state:
    st.session_state.ocr_debug: dict[str, str] = {}


def get_client(provider: str, api_key: str):
    if provider == "Anthropic (Claude)":
        return AnthropicClient(api_key=api_key)
    return OpenAIClient(api_key=api_key)


st.title("MedScribe — AI Medical Document Assistant")
st.caption(
    "Research assistant for medical practices. OCR (Tesseract) + LLM "
    "structuring, with human-in-the-loop review before export."
)
st.warning(
    "⚠️ Research/demo tool only — not a medical device, not a substitute "
    "for clinical judgment. Verify all extracted fields before use. "
    "See README for PHI-handling guidance before using with real patient data.",
    icon="⚠️",
)

with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("LLM Provider", ["Anthropic (Claude)", "OpenAI"])
    default_env_key = "ANTHROPIC_API_KEY" if provider.startswith("Anthropic") else "OPENAI_API_KEY"
    api_key = st.text_input(
        "API Key",
        value=os.environ.get(default_env_key, ""),
        type="password",
        help=f"Defaults to the {default_env_key} environment variable if set.",
    )
    db_path = st.text_input("SQLite DB path", value="medscribe.db")
    st.divider()
    st.markdown(
        "**Tesseract required**: this app calls the `tesseract` binary. "
        "Install it separately (see README)."
    )

uploaded_files = st.file_uploader(
    "Upload scanned PDF or image (intake form, referral, lab report, etc.)",
    type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
    accept_multiple_files=True,
)

col_run, col_clear = st.columns([1, 1])
with col_run:
    run_clicked = st.button("Run OCR + Structuring", type="primary", disabled=not uploaded_files)
with col_clear:
    if st.button("Clear results"):
        st.session_state.records = []
        st.session_state.ocr_debug = {}
        st.rerun()

if run_clicked:
    if not api_key:
        st.error("Please provide an API key in the sidebar.")
    else:
        client = get_client(provider, api_key)
        store = RecordStore(db_path=db_path)
        progress = st.progress(0.0, text="Processing documents...")

        for i, uploaded in enumerate(uploaded_files):
            try:
                record, ocr_result = run_pipeline(
                    file_bytes=uploaded.getvalue(),
                    filename=uploaded.name,
                    llm_client=client,
                    store=store,
                )
                st.session_state.records.append(record)
                st.session_state.ocr_debug[record.record_id or uploaded.name] = ocr_result.full_text
            except Exception as exc:  # noqa: BLE001 - surface any failure to the user
                st.error(f"Failed to process {uploaded.name}: {exc}")
            progress.progress((i + 1) / len(uploaded_files))

        progress.empty()
        st.success(f"Processed {len(uploaded_files)} document(s).")

if st.session_state.records:
    st.subheader("Review & Edit Extracted Records")
    st.caption("Edit any cell to correct OCR/LLM mistakes before exporting.")

    df = pd.DataFrame([r.flat_dict() for r in st.session_state.records])
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")

    with st.expander("View raw OCR text per document (for auditing edits)"):
        for key, text in st.session_state.ocr_debug.items():
            st.text_area(key, text, height=150)

    st.subheader("Export")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download JSON",
            data=to_json(st.session_state.records),
            file_name="medscribe_records.json",
            mime="application/json",
        )
    with c2:
        st.download_button(
            "Download CSV",
            data=edited_df.to_csv(index=False),
            file_name="medscribe_records.csv",
            mime="text/csv",
        )

    st.caption(
        f"Records also persisted to SQLite at `{db_path}`. "
        "Use `medscribe.storage.RecordStore` to query them programmatically."
    )
else:
    st.info("Upload one or more documents and click **Run OCR + Structuring** to begin.")
