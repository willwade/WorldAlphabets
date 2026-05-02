#!/usr/bin/env python3
"""Prepare tests-first batch requests for inflection rule development."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INFLECTION_DIR = DATA_DIR / "inflections"
SOURCES_DIR = DATA_DIR / "sources" / "inflections"
DEFAULT_BATCH_DIR = SOURCES_DIR / "batches"
DEFAULT_MODEL = "gpt-4o-mini"
TESTS_CSV_HEADER = ["rule_id", "inflection", "pre_words", "test_word", "updated_words"]


SYSTEM_PROMPT = """You generate inflection-rule test suites.
Return only valid compact JSON. Do not include markdown. The output must be a
JSON object with a tests array. Do not return CSV text.
"""


def read_json(path: Path) -> Any:
    """Read JSON from a file."""

    return json.loads(path.read_text(encoding="utf-8"))


def read_text_if_exists(path: Path, limit_chars: int) -> str:
    """Read text if a file exists, truncated to limit_chars."""

    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:limit_chars]


def read_test_examples(limit: int) -> list[dict[str, str]]:
    """Read English tests.csv rows as examples for other locales."""

    path = INFLECTION_DIR / "en" / "tests.csv"
    examples: list[dict[str, str]] = []
    if not path.exists():
        return examples
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            examples.append({key: row.get(key, "") for key in TESTS_CSV_HEADER})
            if len(examples) >= limit:
                break
    return examples


def example_rows_as_arrays(limit: int) -> list[list[Any]]:
    """Return English test examples in rules.json test-array shape."""

    rows: list[list[Any]] = []
    for row in read_test_examples(limit):
        test: list[Any] = [row["pre_words"], row["test_word"], row["updated_words"]]
        checks: dict[str, str] = {}
        if row.get("rule_id"):
            checks["rule_id"] = row["rule_id"]
        if row.get("inflection"):
            checks["inflection"] = row["inflection"]
        if checks:
            test.append(checks)
        rows.append(test)
    return rows


def summarize_locale(locale: str, sample_size: int) -> dict[str, Any]:
    """Summarize word/rule data for test generation."""

    words_path = INFLECTION_DIR / locale / "words.json"
    rules_path = INFLECTION_DIR / locale / "rules.json"
    words = read_json(words_path)
    rules = read_json(rules_path)
    if not isinstance(words, dict):
        raise ValueError(f"{words_path} must be a JSON object")
    if not isinstance(rules, dict):
        raise ValueError(f"{rules_path} must be a JSON object")

    sample_words = []
    for word, entry in words.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        forms = entry.get("inflections")
        sample_words.append(
            {
                "word": word,
                "types": entry.get("types", []),
                "base": entry.get("base", word),
                "priority": entry.get("priority"),
                "inflection_keys": list(forms.keys())[:8] if isinstance(forms, dict) else [],
            }
        )
        if len(sample_words) >= sample_size:
            break

    rule_summaries = []
    raw_rules = rules.get("rules", [])
    if isinstance(raw_rules, list):
        for rule in raw_rules:
            if not isinstance(rule, dict):
                continue
            rule_summaries.append(
                {
                    "id": rule.get("id"),
                    "type": rule.get("type"),
                    "inflection": rule.get("inflection"),
                    "overrides": rule.get("overrides"),
                    "lookback": rule.get("lookback"),
                }
            )
    return {
        "locale": locale,
        "sample_words": sample_words,
        "rules": rule_summaries,
    }


def user_prompt(locale: str, row_count: int, sample_size: int) -> str:
    """Build one tests-first prompt."""

    payload = {
        "task": "Generate a comprehensive inflection test suite for this locale.",
        "locale": locale,
        "target_row_count": row_count,
        "locale_summary": summarize_locale(locale, sample_size),
        "english_pattern_examples": example_rows_as_arrays(80),
        "requirements": [
            "Return JSON only: {\"tests\": [[pre_words, test_word, updated_words, checks], ...]}.",
            "Each test must be an array with 3 or 4 items.",
            "The optional checks object may include rule_id and inflection.",
            "Rows should exercise every executable rule, plus no_rule negative cases.",
            "At least 70 percent of rows should expect an actual rule_id, not no_rule.",
            "Use no_rule only for clear negative regression cases that prevent over-inflection.",
            "Include common pronoun, noun, verb, auxiliary, negation, and preposition contexts where appropriate for the locale.",
            "Use words and inflection keys that exist in locale_summary.",
            "The updated_words value should be the expected full phrase after applying the word/rule.",
            "Make this useful for automated regression testing, not just examples.",
            "Avoid English words unless the locale itself uses them.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def available_locales() -> list[str]:
    """Return locales with word and rule data."""

    if not INFLECTION_DIR.exists():
        return []
    return sorted(
        path.name
        for path in INFLECTION_DIR.iterdir()
        if (path / "words.json").exists() and (path / "rules.json").exists()
    )


def parse_locale_filter(value: str | None) -> list[str]:
    """Parse locale filter or use all available locales except en."""

    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return [locale for locale in available_locales() if locale != "en"]


def build_request(locale: str, model: str, row_count: int, sample_size: int) -> dict[str, Any]:
    """Build one batch request line."""

    return {
        "custom_id": f"inflection-tests-{locale}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(locale, row_count, sample_size)},
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales", help="Comma-separated locale list; default all non-en")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--row-count", type=int, default=150)
    parser.add_argument("--sample-size", type=int, default=80)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BATCH_DIR)
    return parser.parse_args()


def main() -> None:
    """Write a tests-first batch JSONL file."""

    args = parse_args()
    locales = parse_locale_filter(args.locales)
    requests = [build_request(locale, args.model, args.row_count, args.sample_size) for locale in locales]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"inflection_tests_{timestamp}.jsonl"
    out_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
        encoding="utf-8",
    )
    print(f"Wrote {len(requests)} tests-first batch requests to {out_path}")


if __name__ == "__main__":
    main()
