#!/usr/bin/env python3
"""Prepare batch requests for missing high-frequency inflection words."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INFLECTION_DIR = DATA_DIR / "inflections"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
SOURCES_DIR = DATA_DIR / "sources" / "inflections"
DEFAULT_BATCH_DIR = SOURCES_DIR / "batches"
DEFAULT_MODEL = "gpt-4o-mini"
VERSION = "0.1"

SYSTEM_PROMPT = """You fill gaps in existing word-form datasets.
Return only valid compact JSON. Do not include markdown. Generate word entries
for the exact requested missing tokens only. Do not generate rules.
"""


def read_json(path: Path) -> Any:
    """Read JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_tokens(locale: str, limit: int) -> list[str]:
    """Load top frequency tokens for a locale, falling back to base locale."""

    path = FREQ_DIR / f"{locale}.txt"
    if not path.exists() and "-" in locale:
        path = FREQ_DIR / f"{locale.split('-', 1)[0]}.txt"
    if not path.exists():
        return []
    tokens: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not tokens and stripped.startswith("#"):
            continue
        tokens.append(stripped)
        if len(tokens) >= limit:
            break
    return tokens


def existing_words(locale: str) -> set[str]:
    """Return existing non-metadata word keys for a locale."""

    path = INFLECTION_DIR / locale / "words.json"
    if not path.exists():
        return set()
    data = read_json(path)
    if not isinstance(data, dict):
        return set()
    return {key for key in data if not key.startswith("_")}


def available_locales() -> list[str]:
    """Return locales with inflection directories."""

    if not INFLECTION_DIR.exists():
        return []
    return sorted(path.name for path in INFLECTION_DIR.iterdir() if path.is_dir())


def missing_tokens(locale: str, top_n: int, max_missing: int) -> list[dict[str, Any]]:
    """Return missing top-frequency tokens with priority metadata."""

    tokens = load_tokens(locale, top_n)
    existing = existing_words(locale)
    total = len(tokens)
    missing: list[dict[str, Any]] = []
    for rank, token in enumerate(tokens, start=1):
        if token in existing:
            continue
        priority = max(1, min(10, 10 - int(((rank - 1) / max(total, 1)) * 10)))
        missing.append({"token": token, "rank": rank, "priority": priority})
        if len(missing) >= max_missing:
            break
    return missing


def chunk(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    """Split items into chunks."""

    if size <= 0:
        return [items]
    return [items[index : index + size] for index in range(0, len(items), size)]


def user_prompt(locale: str, tokens: list[dict[str, Any]]) -> str:
    """Build prompt for one missing-token chunk."""

    payload = {
        "task": "Create word-form entries for missing high-frequency tokens.",
        "locale": locale,
        "missing_tokens": tokens,
        "requirements": [
            "Return JSON only with top-level words and rules objects.",
            "words must include _type='words', _locale, and _version='0.1'.",
            "rules must include _type='rules', _locale, _version='0.1', empty rules/tests arrays, substitutions object, and inflection_locations object.",
            "The words object must include exactly one non-underscore key per missing token.",
            "Each word key must be the exact token string.",
            "Each entry must include types, base, priority, and inflections.",
            "Use broad part-of-speech labels compatible with the demo runtime where possible: noun, verb, adjective, adverb, pronoun, determiner, preposition, conjunction, interjection, social, question, numeral, word.",
            "For function words or particles with no meaningful inflections, use inflections {base: token, regulars: ['base']}.",
            "For verbs/nouns/adjectives, include common forms only when high confidence.",
            "Do not add prose notes or placeholder keys.",
        ],
        "response_shape": {
            "words": {
                "_type": "words",
                "_locale": locale,
                "_version": VERSION,
                "<exact missing token>": {
                    "types": ["word"],
                    "base": "<base form>",
                    "priority": 10,
                    "inflections": {"base": "<token>", "regulars": ["base"]},
                },
            },
            "rules": {
                "_type": "rules",
                "_locale": locale,
                "_version": VERSION,
                "rules": [],
                "tests": [],
                "substitutions": {},
                "inflection_locations": {},
            },
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_request(locale: str, model: str, tokens: list[dict[str, Any]], index: int) -> dict[str, Any]:
    """Build one Batch API request."""

    return {
        "custom_id": f"inflections-{locale}-chunk-{index:03d}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(locale, tokens)},
            ],
        },
    }


def parse_locale_filter(value: str | None) -> list[str]:
    """Parse locales or use all available locales."""

    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return available_locales()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales", help="Comma-separated locale list; default all")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--top-n", type=int, default=100)
    parser.add_argument("--max-missing-per-locale", type=int, default=100)
    parser.add_argument("--chunk-size", type=int, default=25)
    parser.add_argument("--min-missing", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BATCH_DIR)
    return parser.parse_args()


def main() -> None:
    """Write missing-token batch JSONL."""

    args = parse_args()
    requests: list[dict[str, Any]] = []
    for locale in parse_locale_filter(args.locales):
        missing = missing_tokens(locale, args.top_n, args.max_missing_per_locale)
        if len(missing) < args.min_missing:
            continue
        for idx, items in enumerate(chunk(missing, args.chunk_size), start=1):
            requests.append(build_request(locale, args.model, items, idx))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"inflection_gap_words_{timestamp}.jsonl"
    out_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
        encoding="utf-8",
    )
    print(f"Wrote {len(requests)} gap-word batch requests to {out_path}")


if __name__ == "__main__":
    main()
