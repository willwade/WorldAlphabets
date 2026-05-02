#!/usr/bin/env python3
"""Prepare rules-only batch requests for existing inflection word data."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INFLECTION_DIR = DATA_DIR / "inflections"
SOURCES_DIR = DATA_DIR / "sources" / "inflections"
DEFAULT_BATCH_DIR = SOURCES_DIR / "batches"
DEFAULT_MODEL = "gpt-4o-mini"
VERSION = "0.1"


SYSTEM_PROMPT = """You generate executable word-form rule data.
Return only valid compact JSON. Do not include markdown or prose outside JSON.
Rules must follow the documented lookback/inflection/overrides shape, not prose
grammar notes. Prefer a few high-value rules over exhaustive grammar.
"""


def read_json(path: Path) -> Any:
    """Read a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def non_metadata_items(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return word entries, excluding metadata keys."""

    items: list[tuple[str, dict[str, Any]]] = []
    for word, entry in data.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        items.append((word, entry))
    return items


def summarize_words(locale: str, sample_size: int) -> dict[str, Any]:
    """Summarize a locale's word data for rules-only generation."""

    words_path = INFLECTION_DIR / locale / "words.json"
    data = read_json(words_path)
    if not isinstance(data, dict):
        raise ValueError(f"{words_path} must contain a JSON object")

    entries = non_metadata_items(data)
    entries.sort(
        key=lambda item: (
            -int(item[1].get("priority", 0)) if isinstance(item[1].get("priority"), int) else 0,
            item[0],
        )
    )

    type_counts: Counter[str] = Counter()
    inflection_counts: dict[str, Counter[str]] = defaultdict(Counter)
    samples: list[dict[str, Any]] = []

    for word, entry in entries:
        types = entry.get("types")
        type_list = [item for item in types if isinstance(item, str)] if isinstance(types, list) else []
        if not type_list:
            type_list = ["word"]
        for part in type_list:
            type_counts[part] += 1
        forms = entry.get("inflections")
        inflection_keys = []
        if isinstance(forms, dict):
            inflection_keys = [key for key in forms if key != "regulars"]
        for part in type_list:
            for key in inflection_keys:
                inflection_counts[part][key] += 1
        if len(samples) < sample_size:
            samples.append(
                {
                    "word": word,
                    "types": type_list,
                    "base": entry.get("base", word),
                    "priority": entry.get("priority"),
                    "inflection_keys": inflection_keys[:12],
                }
            )

    return {
        "locale": locale,
        "word_count": len(entries),
        "type_counts": dict(type_counts.most_common(20)),
        "inflection_keys_by_type": {
            part: dict(counter.most_common(20))
            for part, counter in inflection_counts.items()
        },
        "sample_words": samples,
    }


def user_prompt(locale: str, summary: dict[str, Any], max_rules: int) -> str:
    """Build a rules-only prompt."""

    payload = {
        "task": "Generate executable inflection rules for existing word-form data.",
        "locale": locale,
        "format_version": VERSION,
        "word_summary": summary,
        "requirements": [
            "Return one JSON object with a top-level rules object.",
            "rules._type must be 'rules', rules._locale must match locale, rules._version must be '0.1'.",
            "rules.rules must contain executable rule objects only.",
            "Each rule needs id, type, lookback, and inflection or overrides.",
            "Rule type should match a broad part of speech in word_summary.type_counts, or 'override'.",
            "Rule inflection values must come from word_summary.inflection_keys_by_type.",
            "Lookback items may use words, type, optional, condense, match, or non_match.",
            "Rules may include location using n, ne, e, se, s, sw, w, nw, or c.",
            "rules.tests must include at least one test per generated rule.",
            "Each test must be [pre_text, word, post_text, checks].",
            f"Generate at most {max_rules} high-confidence rules.",
            "If no high-confidence executable rules are appropriate, return empty rules and tests arrays.",
        ],
        "response_shape": {
            "rules": {
                "_type": "rules",
                "_locale": locale,
                "_version": VERSION,
                "rules": [
                    {
                        "id": "example_rule_id",
                        "type": "verb",
                        "lookback": [{"words": ["example"], "optional": False}],
                        "inflection": "example_inflection_key",
                        "location": "e",
                    }
                ],
                "tests": [
                    [
                        "example pre text",
                        "example_word",
                        "example post text",
                        {"rule_id": "example_rule_id", "inflection": "example_inflection_key"},
                    ]
                ],
                "substitutions": {},
                "inflection_locations": {},
            }
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def available_locales() -> list[str]:
    """Return locales with published words.json files."""

    if not INFLECTION_DIR.exists():
        return []
    return sorted(
        path.name for path in INFLECTION_DIR.iterdir() if (path / "words.json").exists()
    )


def has_tests(locale: str) -> bool:
    """Return True when a locale has tests.csv."""

    return (INFLECTION_DIR / locale / "tests.csv").exists()


def parse_locale_filter(value: str | None) -> list[str]:
    """Parse locale filter or use all available locales."""

    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return [locale for locale in available_locales() if has_tests(locale)]


def build_request(locale: str, model: str, sample_size: int, max_rules: int) -> dict[str, Any]:
    """Build one batch request line."""

    summary = summarize_words(locale, sample_size)
    return {
        "custom_id": f"inflection-rules-{locale}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(locale, summary, max_rules)},
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales", help="Comma-separated locale list; default all")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--max-rules", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BATCH_DIR)
    return parser.parse_args()


def main() -> None:
    """Write a rules-only batch JSONL file."""

    args = parse_args()
    locales = parse_locale_filter(args.locales)
    requests = [
        build_request(locale, args.model, args.sample_size, args.max_rules)
        for locale in locales
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"inflection_rules_{timestamp}.jsonl"
    out_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
        encoding="utf-8",
    )
    print(f"Wrote {len(requests)} rules-only batch requests to {out_path}")


if __name__ == "__main__":
    main()
