#!/usr/bin/env python3
"""Ingest rules-only batch output into existing inflection rules files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .ingest_inflections import normalize_inflection_locations, normalize_rules
except ImportError:  # pragma: no cover - supports direct script execution
    from ingest_inflections import (  # type: ignore[import-not-found,no-redef]
        normalize_inflection_locations,
        normalize_rules,
    )


ROOT = Path(__file__).resolve().parents[1]
INFLECTION_DIR = ROOT / "data" / "inflections"
RAW_RESULTS_DIR = ROOT / "data" / "sources" / "inflections" / "raw_results"
VERSION = "0.1"


def latest_rules_output() -> Path:
    """Return most recent raw output JSONL file."""

    candidates = sorted(
        RAW_RESULTS_DIR.glob("*_output.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No output JSONL files found in {RAW_RESULTS_DIR}")
    return candidates[0]


def locale_from_custom_id(custom_id: str) -> str | None:
    """Extract locale from rules-only custom ID."""

    match = re.fullmatch(r"inflection-rules-(.+)", custom_id)
    return match.group(1) if match else None


def extract_rules(line_data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Extract locale and rules payload from one batch result line."""

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
        raise ValueError(f"{custom_id}: content must be object")
    rules = payload.get("rules", payload)
    if not isinstance(rules, dict):
        raise ValueError(f"{custom_id}: rules must be object")
    rules["_type"] = "rules"
    rules["_locale"] = locale
    rules.setdefault("_version", VERSION)
    rules.setdefault("substitutions", {})
    normalize_rules(rules)
    normalize_inflection_locations(rules)
    return locale, rules


def merge_existing(existing: dict[str, Any], incoming: dict[str, Any], replace: bool) -> dict[str, Any]:
    """Merge or replace rule sections."""

    if replace:
        merged = dict(existing)
        for key in ["rules", "tests", "inflection_locations", "substitutions"]:
            merged[key] = incoming.get(key, [] if key in {"rules", "tests"} else {})
        merged["_type"] = "rules"
        merged["_locale"] = incoming["_locale"]
        merged["_version"] = incoming.get("_version", VERSION)
        return merged

    merged = dict(existing)
    for key in ["rules", "tests"]:
        current = merged.get(key, [])
        new = incoming.get(key, [])
        if isinstance(current, list) and isinstance(new, list):
            merged[key] = current + new
    locations = merged.get("inflection_locations", {})
    incoming_locations = incoming.get("inflection_locations", {})
    if isinstance(locations, dict) and isinstance(incoming_locations, dict):
        locations.update(incoming_locations)
        merged["inflection_locations"] = locations
    return merged


def write_rules(locale: str, rules: dict[str, Any], replace: bool) -> None:
    """Write one locale's rules.json."""

    path = INFLECTION_DIR / locale / "rules.json"
    existing: dict[str, Any] = {}
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            existing = loaded
    merged = merge_existing(existing, rules, replace=replace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ingest(path: Path, replace: bool, allow_errors: bool) -> None:
    """Ingest a raw output file."""

    written = 0
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError("line must be object")
            locale, rules = extract_rules(data)
            write_rules(locale, rules, replace=replace)
            written += 1
        except Exception as exc:
            errors.append(f"line {line_no}: {exc}")
    print(f"Ingested rules from {path}; written {written}")
    for error in errors:
        print(f"error: {error}")
    if errors and not allow_errors:
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--append", action="store_true", help="Append instead of replace")
    parser.add_argument("--allow-errors", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run ingestion."""

    args = parse_args()
    ingest(args.input or latest_rules_output(), replace=not args.append, allow_errors=args.allow_errors)


if __name__ == "__main__":
    main()
