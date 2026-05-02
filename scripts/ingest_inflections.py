#!/usr/bin/env python3
"""Ingest completed inflection batch JSONL results into published data files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "data" / "sources" / "inflections"
RAW_RESULTS_DIR = SOURCES_DIR / "raw_results"
DEFAULT_DATA_DIR = ROOT / "data" / "inflections"
VERSION = "0.1"


@dataclass
class IngestReport:
    """Track ingestion outcomes."""

    written: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def latest_result_file() -> Path:
    """Return the most recently modified raw batch output file."""

    candidates = sorted(
        RAW_RESULTS_DIR.glob("*_output.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No raw output JSONL files found in {RAW_RESULTS_DIR}")
    return candidates[0]


def locale_from_custom_id(custom_id: str) -> str | None:
    """Extract a locale from a custom_id such as inflections-en-GB."""

    chunk_match = re.fullmatch(r"inflections-(.+)-chunk-\d+", custom_id)
    if chunk_match:
        return chunk_match.group(1)

    match = re.fullmatch(r"inflections-(.+)", custom_id)
    return match.group(1) if match else None


def parse_message_content(content: str) -> dict[str, Any]:
    """Parse model message content as JSON."""

    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("message content must be a JSON object")
    return data


def extract_payload(line_data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Extract locale and generated payload from one Batch API result line."""

    custom_id = line_data.get("custom_id")
    if not isinstance(custom_id, str):
        raise ValueError("missing custom_id")
    locale = locale_from_custom_id(custom_id)
    if locale is None:
        raise ValueError(f"unexpected custom_id {custom_id!r}")

    response = line_data.get("response")
    if not isinstance(response, dict):
        raise ValueError(f"{custom_id}: missing response object")
    status_code = response.get("status_code")
    if status_code != 200:
        raise ValueError(f"{custom_id}: status_code was {status_code}")

    body = response.get("body")
    if not isinstance(body, dict):
        raise ValueError(f"{custom_id}: missing response body")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError(f"{custom_id}: missing choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError(f"{custom_id}: first choice must be an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError(f"{custom_id}: missing message")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"{custom_id}: missing message content")

    return locale, parse_message_content(content)


def ensure_metadata(data: dict[str, Any], data_type: str, locale: str) -> dict[str, Any]:
    """Ensure required top-level metadata fields are present and correct."""

    data["_type"] = data_type
    data["_locale"] = locale
    data.setdefault("_version", VERSION)
    return data


def normalize_payload(locale: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Normalize and return words/rules objects from a model payload."""

    words = payload.get("words")
    rules = payload.get("rules")
    if not isinstance(words, dict):
        raise ValueError(f"{locale}: payload missing object words")
    if not isinstance(rules, dict):
        raise ValueError(f"{locale}: payload missing object rules")

    ensure_metadata(words, "words", locale)
    normalize_words(words)
    ensure_metadata(rules, "rules", locale)
    normalize_rules(rules)
    rules.setdefault("substitutions", {})
    normalize_inflection_locations(rules)
    return words, rules


def normalize_inflections(value: Any) -> dict[str, Any]:
    """Normalize common model inflection variants into an object."""

    if isinstance(value, dict):
        value.setdefault("regulars", [])
        return value
    if isinstance(value, list):
        result: dict[str, Any] = {"regulars": []}
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                key = item.get("type") or item.get("inflection") or item.get("name")
                form = item.get("form") or item.get("value") or item.get("word")
                if isinstance(key, str) and isinstance(form, str):
                    result[key] = form
                else:
                    result[f"generated_{index}"] = item
            elif isinstance(item, str):
                result.setdefault("regulars", []).append(item)
        return result
    return {"regulars": []}


def normalize_words(words: dict[str, Any]) -> None:
    """Normalize word entries into the documented shape."""

    for word, entry in list(words.items()):
        if word.startswith("_"):
            continue
        if not isinstance(entry, dict):
            words[word] = {
                "types": ["word"],
                "base": word,
                "inflections": {"regulars": []},
            }
            continue
        types = entry.get("types")
        if isinstance(types, str):
            entry["types"] = [types]
        elif not isinstance(types, list):
            entry["types"] = ["word"]
        entry.setdefault("base", word)
        entry["inflections"] = normalize_inflections(entry.get("inflections"))


def is_executable_rule(rule: Any) -> bool:
    """Return True when a generated rule has the documented executable shape."""

    if not isinstance(rule, dict):
        return False
    if not isinstance(rule.get("id"), str) or not rule["id"]:
        return False
    if not isinstance(rule.get("type"), str) or not rule["type"]:
        return False
    if "overrides" in rule:
        return isinstance(rule["overrides"], dict)
    return isinstance(rule.get("inflection"), str) and bool(rule["inflection"])


def normalize_rules(rules: dict[str, Any]) -> None:
    """Keep executable rules and preserve other model notes under metadata."""

    raw_rules = rules.get("rules", [])
    if not isinstance(raw_rules, list):
        rules["_generated_rule_notes"] = raw_rules
        rules["rules"] = []
    else:
        executable = [rule for rule in raw_rules if is_executable_rule(rule)]
        notes = [rule for rule in raw_rules if not is_executable_rule(rule)]
        rules["rules"] = executable
        if notes:
            rules["_generated_rule_notes"] = notes

    raw_tests = rules.get("tests", [])
    if not isinstance(raw_tests, list):
        rules["_generated_test_notes"] = raw_tests
        rules["tests"] = []
    else:
        tests = [test for test in raw_tests if isinstance(test, list) and len(test) >= 3]
        notes = [test for test in raw_tests if not (isinstance(test, list) and len(test) >= 3)]
        rules["tests"] = tests
        if notes:
            rules["_generated_test_notes"] = notes


def normalize_inflection_locations(rules: dict[str, Any]) -> None:
    """Keep valid inflection_locations and preserve invalid notes."""

    raw_locations = rules.get("inflection_locations", {})
    if not isinstance(raw_locations, dict):
        rules["_generated_inflection_location_notes"] = raw_locations
        rules["inflection_locations"] = {}
        return

    valid: dict[str, Any] = {}
    notes: dict[str, Any] = {}
    for part, criteria in raw_locations.items():
        if isinstance(criteria, list) and all(isinstance(item, dict) for item in criteria):
            valid[part] = criteria
        elif criteria:
            notes[part] = criteria
    rules["inflection_locations"] = valid
    if notes:
        rules["_generated_inflection_location_notes"] = notes


def write_locale(
    data_dir: Path,
    locale: str,
    words: dict[str, Any],
    rules: dict[str, Any],
    overwrite: bool,
    merge_existing: bool = False,
) -> bool:
    """Write one locale's words/rules files. Return True when written."""

    locale_dir = data_dir / locale
    words_path = locale_dir / "words.json"
    rules_path = locale_dir / "rules.json"
    if merge_existing:
        existing_words = {}
        existing_rules = {}
        if words_path.exists():
            loaded_words = json.loads(words_path.read_text(encoding="utf-8"))
            if isinstance(loaded_words, dict):
                existing_words = loaded_words
        if rules_path.exists():
            loaded_rules = json.loads(rules_path.read_text(encoding="utf-8"))
            if isinstance(loaded_rules, dict):
                existing_rules = loaded_rules
        for word, entry in words.items():
            if word.startswith("_"):
                existing_words.setdefault(word, entry)
            elif word not in existing_words:
                existing_words[word] = entry
        words = existing_words or words
        rules = merge_rules(existing_rules, rules) if existing_rules else rules
    elif not overwrite and (words_path.exists() or rules_path.exists()):
        return False
    locale_dir.mkdir(parents=True, exist_ok=True)
    words_path.write_text(
        json.dumps(words, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rules_path.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return True


def merge_unique_list(existing: list[Any], incoming: list[Any]) -> list[Any]:
    """Append unique JSON-serializable values while preserving order."""

    seen = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in existing}
    merged = list(existing)
    for item in incoming:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def merge_rules(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge rule payloads from multiple chunks."""

    merged = dict(existing)
    for key, value in incoming.items():
        if key.startswith("_") and key not in {"_generated_rule_notes", "_generated_test_notes"}:
            merged[key] = value

    for key in ["rules", "tests"]:
        existing_list = merged.get(key, [])
        incoming_list = incoming.get(key, [])
        if isinstance(existing_list, list) and isinstance(incoming_list, list):
            merged[key] = merge_unique_list(existing_list, incoming_list)

    for key in [
        "_generated_rule_notes",
        "_generated_test_notes",
        "_generated_inflection_location_notes",
    ]:
        existing_list = merged.get(key, [])
        incoming_list = incoming.get(key, [])
        if not isinstance(existing_list, list):
            existing_list = [existing_list]
        if not isinstance(incoming_list, list):
            incoming_list = [incoming_list]
        if incoming_list:
            merged[key] = merge_unique_list(existing_list, incoming_list)

    existing_locations = merged.get("inflection_locations", {})
    incoming_locations = incoming.get("inflection_locations", {})
    if isinstance(existing_locations, dict) and isinstance(incoming_locations, dict):
        locations = dict(existing_locations)
        for part, criteria in incoming_locations.items():
            if not isinstance(criteria, list):
                continue
            current = locations.get(part, [])
            if not isinstance(current, list):
                current = []
            locations[part] = merge_unique_list(current, criteria)
        merged["inflection_locations"] = locations

    merged.setdefault("substitutions", existing.get("substitutions", {}))
    return merged


def merge_payload(
    collected: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    locale: str,
    words: dict[str, Any],
    rules: dict[str, Any],
) -> None:
    """Merge one locale payload into collected data."""

    if locale not in collected:
        collected[locale] = (words, rules)
        return

    existing_words, existing_rules = collected[locale]
    for word, entry in words.items():
        if word.startswith("_"):
            existing_words[word] = entry
        elif word not in existing_words:
            existing_words[word] = entry
    collected[locale] = (existing_words, merge_rules(existing_rules, rules))


def ingest_file(
    input_file: Path,
    data_dir: Path,
    overwrite: bool,
    merge_existing: bool = False,
) -> IngestReport:
    """Ingest a batch output JSONL file."""

    report = IngestReport()
    collected: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line_no, line in enumerate(input_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            line_data = json.loads(line)
            if not isinstance(line_data, dict):
                raise ValueError("line must be a JSON object")
            locale, payload = extract_payload(line_data)
            words, rules = normalize_payload(locale, payload)
            merge_payload(collected, locale, words, rules)
        except Exception as exc:
            report.errors.append(f"line {line_no}: {exc}")
    for locale, (words, rules) in sorted(collected.items()):
        if write_locale(data_dir, locale, words, rules, overwrite, merge_existing):
            report.written.append(locale)
        else:
            report.skipped.append(locale)
    return report


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Raw output JSONL file")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge generated entries into existing locale files instead of replacing them",
    )
    parser.add_argument(
        "--allow-errors",
        action="store_true",
        help="Write valid locales even when some result lines fail",
    )
    return parser.parse_args()


def main() -> None:
    """Run ingestion."""

    args = parse_args()
    input_file = args.input or latest_result_file()
    report = ingest_file(
        input_file,
        args.data_dir,
        overwrite=args.overwrite,
        merge_existing=args.merge_existing,
    )
    print(f"Ingested {input_file}")
    print(f"Written: {len(report.written)}")
    if report.skipped:
        print(f"Skipped existing: {len(report.skipped)}")
    for error in report.errors:
        print(f"error: {error}")
    if report.errors and not args.allow_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
