#!/usr/bin/env python3
"""Ingest tests-first batch output into locale tests.csv files."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .sync_inflection_tests import sync_locale
except ImportError:  # pragma: no cover - supports direct script execution
    from sync_inflection_tests import sync_locale  # type: ignore[import-not-found,no-redef]


ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"
RAW_RESULTS_DIR = ROOT / "data" / "sources" / "inflections" / "raw_results"
TESTS_CSV_HEADER = ["rule_id", "inflection", "pre_words", "test_word", "updated_words"]


def latest_output() -> Path:
    """Return most recent raw batch output file."""

    candidates = sorted(
        RAW_RESULTS_DIR.glob("*_output.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No output JSONL files found in {RAW_RESULTS_DIR}")
    return candidates[0]


def locale_from_custom_id(custom_id: str) -> str | None:
    """Extract locale from tests custom ID."""

    match = re.fullmatch(r"inflection-tests-(.+)", custom_id)
    return match.group(1) if match else None


def normalize_csv(text: str) -> str:
    """Normalize and validate generated tests CSV text."""

    handle = io.StringIO(text)
    reader = csv.DictReader(handle)
    if reader.fieldnames != TESTS_CSV_HEADER:
        raise ValueError(f"tests_csv header must be {TESTS_CSV_HEADER}")

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TESTS_CSV_HEADER, lineterminator="\n")
    writer.writeheader()
    rows = 0
    for row in reader:
        cleaned = {key: (row.get(key) or "").strip() for key in TESTS_CSV_HEADER}
        if not cleaned["test_word"] or not cleaned["updated_words"]:
            continue
        writer.writerow(cleaned)
        rows += 1
    if rows == 0:
        raise ValueError("tests_csv did not contain any usable rows")
    return out.getvalue()


def tests_array_to_csv(tests: list[Any]) -> str:
    """Convert generated JSON tests into normalized tests.csv content."""

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TESTS_CSV_HEADER, lineterminator="\n")
    writer.writeheader()
    rows = 0
    for item in tests:
        if not isinstance(item, list) or len(item) < 3:
            continue
        pre_words = str(item[0] or "").strip()
        test_word = str(item[1] or "").strip()
        updated_words = str(item[2] or "").strip()
        if not test_word or not updated_words:
            continue
        checks = item[3] if len(item) > 3 and isinstance(item[3], dict) else {}
        writer.writerow(
            {
                "rule_id": str(checks.get("rule_id", "")).strip(),
                "inflection": str(checks.get("inflection", "")).strip(),
                "pre_words": pre_words,
                "test_word": test_word,
                "updated_words": updated_words,
            }
        )
        rows += 1
    if rows == 0:
        raise ValueError("tests array did not contain any usable rows")
    return out.getvalue()


def no_rule_ratio(csv_text: str) -> float:
    """Return the fraction of tests marked as no_rule."""

    reader = csv.DictReader(io.StringIO(csv_text))
    total = 0
    no_rule = 0
    for row in reader:
        total += 1
        if (row.get("rule_id") or "").strip() == "no_rule":
            no_rule += 1
    return no_rule / total if total else 0.0


def extract_tests(line_data: dict[str, Any]) -> tuple[str, str]:
    """Extract locale and normalized tests.csv from one result line."""

    custom_id = line_data.get("custom_id")
    if not isinstance(custom_id, str):
        raise ValueError("missing custom_id")
    locale = locale_from_custom_id(custom_id)
    if locale is None:
        raise ValueError(f"unexpected custom_id {custom_id!r}")
    response = line_data.get("response")
    if not isinstance(response, dict) or response.get("status_code") != 200:
        raise ValueError(f"{custom_id}: non-200 response")
    body = response.get("body")
    if not isinstance(body, dict):
        raise ValueError(f"{custom_id}: missing body")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError(f"{custom_id}: missing choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError(f"{custom_id}: missing content")
    payload = json.loads(message["content"])
    if not isinstance(payload, dict):
        raise ValueError(f"{custom_id}: payload must be an object")
    tests = payload.get("tests")
    if isinstance(tests, list):
        return locale, tests_array_to_csv(tests)
    tests_csv = payload.get("tests_csv")
    if isinstance(tests_csv, str):
        return locale, normalize_csv(tests_csv)
    raise ValueError(f"{custom_id}: payload must contain tests array")


def ingest(path: Path, allow_errors: bool, max_no_rule_ratio: float) -> None:
    """Ingest generated tests."""

    written = 0
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError("line must be object")
            locale, tests_csv = extract_tests(data)
            ratio = no_rule_ratio(tests_csv)
            if ratio > max_no_rule_ratio:
                raise ValueError(
                    f"{locale}: no_rule ratio {ratio:.1%} exceeds "
                    f"{max_no_rule_ratio:.1%}"
                )
            out_path = INFLECTION_DIR / locale / "tests.csv"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(tests_csv, encoding="utf-8")
            sync_locale(out_path.parent)
            written += 1
        except Exception as exc:
            errors.append(f"line {line_no}: {exc}")
    print(f"Ingested tests from {path}; written {written}")
    for error in errors:
        print(f"error: {error}")
    if errors and not allow_errors:
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--allow-errors", action="store_true")
    parser.add_argument("--max-no-rule-ratio", type=float, default=0.35)
    return parser.parse_args()


def main() -> None:
    """Run ingestion."""

    args = parse_args()
    ingest(
        args.input or latest_output(),
        allow_errors=args.allow_errors,
        max_no_rule_ratio=args.max_no_rule_ratio,
    )


if __name__ == "__main__":
    main()
