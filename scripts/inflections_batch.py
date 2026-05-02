#!/usr/bin/env python3
"""Submit, inspect, and download inflection generation batch jobs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "data" / "sources" / "inflections"
BATCH_DIR = SOURCES_DIR / "batches"
RAW_RESULTS_DIR = SOURCES_DIR / "raw_results"
API_BASE = "https://api.openai.com/v1"


def require_api_key() -> str:
    """Return the OpenAI API key from the environment."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return api_key


def headers(api_key: str) -> dict[str, str]:
    """Build JSON API headers."""

    return {"Authorization": f"Bearer {api_key}"}


def api_error(response: requests.Response) -> str:
    """Return a useful API error message."""

    try:
        payload = response.json()
    except ValueError:
        return response.text
    return json.dumps(payload, ensure_ascii=False, indent=2)


def latest_batch_file() -> Path:
    """Return the most recently modified batch JSONL file."""

    candidates = sorted(
        BATCH_DIR.glob("*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No batch JSONL files found in {BATCH_DIR}")
    return candidates[0]


def write_json(path: Path, data: Any) -> None:
    """Write pretty JSON to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upload_file(api_key: str, batch_file: Path) -> dict[str, Any]:
    """Upload a JSONL file for Batch API use."""

    with batch_file.open("rb") as handle:
        response = requests.post(
            f"{API_BASE}/files",
            headers=headers(api_key),
            files={"file": (batch_file.name, handle, "application/jsonl")},
            data={"purpose": "batch"},
            timeout=120,
        )
    if not response.ok:
        raise RuntimeError(f"file upload failed: {api_error(response)}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("file upload returned an unexpected response")
    return payload


def create_batch(api_key: str, file_id: str, description: str) -> dict[str, Any]:
    """Create a Batch API job for an uploaded file."""

    response = requests.post(
        f"{API_BASE}/batches",
        headers={**headers(api_key), "Content-Type": "application/json"},
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": {
                "project": "worldalphabets-inflections",
                "description": description,
            },
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"batch create failed: {api_error(response)}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("batch create returned an unexpected response")
    return payload


def retrieve_batch(api_key: str, batch_id: str) -> dict[str, Any]:
    """Retrieve Batch API job metadata."""

    response = requests.get(
        f"{API_BASE}/batches/{batch_id}",
        headers=headers(api_key),
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"batch retrieve failed: {api_error(response)}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("batch retrieve returned an unexpected response")
    return payload


def download_file(api_key: str, file_id: str, output_path: Path) -> None:
    """Download file contents from OpenAI."""

    response = requests.get(
        f"{API_BASE}/files/{file_id}/content",
        headers=headers(api_key),
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"file download failed: {api_error(response)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)


def load_batch_id(value: str | None, batch_record: Path | None) -> str:
    """Resolve a batch ID from an argument or saved record."""

    if value:
        return value
    if batch_record is None:
        records = sorted(
            BATCH_DIR.glob("*.batch.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not records:
            raise FileNotFoundError("No saved batch records found")
        batch_record = records[0]
    data = json.loads(batch_record.read_text(encoding="utf-8"))
    batch_id = data.get("id")
    if not isinstance(batch_id, str):
        raise ValueError(f"{batch_record} does not contain a batch id")
    return batch_id


def submit(args: argparse.Namespace) -> None:
    """Submit a batch JSONL file."""

    api_key = require_api_key()
    batch_file = args.batch_file or latest_batch_file()
    upload = upload_file(api_key, batch_file)
    file_id = upload.get("id")
    if not isinstance(file_id, str):
        raise RuntimeError("uploaded file response did not include an id")
    batch = create_batch(api_key, file_id, args.description or batch_file.stem)
    out_path = batch_file.with_suffix(".batch.json")
    write_json(out_path, batch)
    print(f"Submitted {batch_file}")
    print(f"Batch ID: {batch.get('id')}")
    print(f"Status: {batch.get('status')}")
    print(f"Saved record: {out_path}")


def status(args: argparse.Namespace) -> None:
    """Print batch status."""

    api_key = require_api_key()
    batch_id = load_batch_id(args.batch_id, args.batch_record)
    batch = retrieve_batch(api_key, batch_id)
    print(json.dumps(batch, ensure_ascii=False, indent=2))


def download(args: argparse.Namespace) -> None:
    """Download completed batch outputs."""

    api_key = require_api_key()
    batch_id = load_batch_id(args.batch_id, args.batch_record)
    batch = retrieve_batch(api_key, batch_id)
    status_value = batch.get("status")
    if status_value != "completed":
        print(f"Batch {batch_id} is {status_value}; no completed output to download yet")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file_id = batch.get("output_file_id")
    error_file_id = batch.get("error_file_id")
    if isinstance(output_file_id, str):
        output_path = RAW_RESULTS_DIR / f"{batch_id}_{timestamp}_output.jsonl"
        download_file(api_key, output_file_id, output_path)
        print(f"Downloaded output: {output_path}")
    if isinstance(error_file_id, str):
        error_path = RAW_RESULTS_DIR / f"{batch_id}_{timestamp}_errors.jsonl"
        download_file(api_key, error_file_id, error_path)
        print(f"Downloaded errors: {error_path}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument("--batch-file", type=Path)
    submit_parser.add_argument("--description")
    submit_parser.set_defaults(func=submit)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--batch-id")
    status_parser.add_argument("--batch-record", type=Path)
    status_parser.set_defaults(func=status)

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--batch-id")
    download_parser.add_argument("--batch-record", type=Path)
    download_parser.set_defaults(func=download)

    return parser.parse_args()


def main() -> None:
    """Run a subcommand."""

    args = parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
