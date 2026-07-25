"""Command-line entry point for MedScribe.

Usage:
    medscribe process path/to/scan.pdf --provider anthropic --out results.json
    medscribe process path/to/scan.png --provider openai --csv results.csv
"""

from __future__ import annotations

import argparse
import os
import sys

from .export import write_csv, write_json
from .llm import AnthropicClient, OpenAIClient
from .pipeline import run_pipeline
from .storage import RecordStore


def _build_client(provider: str):
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.exit("ANTHROPIC_API_KEY environment variable is not set.")
        return AnthropicClient(api_key=api_key)
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            sys.exit("OPENAI_API_KEY environment variable is not set.")
        return OpenAIClient(api_key=api_key)
    sys.exit(f"Unknown provider: {provider}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="medscribe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Run OCR + LLM structuring on a file")
    process.add_argument("file", help="Path to a PDF or image file")
    process.add_argument(
        "--provider", choices=["anthropic", "openai"], default="anthropic"
    )
    process.add_argument("--db", default="medscribe.db", help="SQLite DB path")
    process.add_argument("--out", help="Write structured record(s) to a JSON file")
    process.add_argument("--csv", help="Write structured record(s) to a CSV file")

    args = parser.parse_args(argv)

    if args.command == "process":
        client = _build_client(args.provider)
        store = RecordStore(db_path=args.db)

        with open(args.file, "rb") as f:
            file_bytes = f.read()

        record, ocr_result = run_pipeline(
            file_bytes=file_bytes,
            filename=os.path.basename(args.file),
            llm_client=client,
            store=store,
        )

        print(f"Processed {args.file} -> record_id={record.record_id}")
        print(f"OCR mean confidence: {ocr_result.mean_confidence:.1f}")
        print(f"Overall record confidence: {record.overall_confidence:.2f}")

        if args.out:
            write_json([record], args.out)
            print(f"Wrote JSON to {args.out}")
        if args.csv:
            write_csv([record], args.csv)
            print(f"Wrote CSV to {args.csv}")


if __name__ == "__main__":
    main()
