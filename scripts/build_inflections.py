#!/usr/bin/env python3
"""Prepare batch requests for inflection data generation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
SOURCES_DIR = DATA_DIR / "sources" / "inflections"
DEFAULT_MANIFEST = SOURCES_DIR / "manifest.json"
DEFAULT_BATCH_DIR = SOURCES_DIR / "batches"

DEFAULT_MODEL = "gpt-4o-mini"
VERSION = "0.1"


SYSTEM_PROMPT = """You generate language-neutral word-form datasets.
Return only valid JSON. Do not include markdown, comments, or explanations.
Use the requested JSON object shape exactly. Keep grammatical labels
language-neutral where appropriate, but make them internally consistent.
Prefer common, clinically and practically useful forms over exhaustive grammar.
"""


def read_json(path: Path) -> Any:
    """Read a JSON file."""

    return json.loads(path.read_text(encoding="utf-8"))


def priority_for_rank(rank: int, total: int) -> int:
    """Map a 1-based frequency rank to a 1-10 priority score."""

    if total <= 1:
        return 10
    score = 10 - int(((rank - 1) / total) * 10)
    return max(1, min(10, score))


def load_tokens(source_locale: str, limit: int) -> list[dict[str, Any]]:
    """Load ranked tokens for a source locale."""

    path = FREQ_DIR / f"{source_locale}.txt"
    if not path.exists():
        return []

    raw_tokens: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not raw_tokens and stripped.startswith("#"):
            continue
        raw_tokens.append(stripped)
        if len(raw_tokens) >= limit:
            break

    total = len(raw_tokens)
    return [
        {
            "token": token,
            "rank": rank,
            "priority": priority_for_rank(rank, total),
        }
        for rank, token in enumerate(raw_tokens, start=1)
    ]


def compact_target(target: dict[str, Any]) -> dict[str, Any]:
    """Return target metadata useful to the model."""

    keys = [
        "locale",
        "language",
        "name",
        "script",
        "iso639_1",
        "iso639_3",
        "source_locale",
        "base_locale",
        "frequency_mode",
    ]
    return {key: target.get(key) for key in keys}


def user_prompt(
    target: dict[str, Any],
    tokens: list[dict[str, Any]],
    chunk_index: int,
    chunk_count: int,
) -> str:
    """Build the user prompt for one locale."""

    payload = {
        "task": "Generate word forms and inflection rules for this locale.",
        "format_version": VERSION,
        "locale_metadata": compact_target(target),
        "chunk": {
            "index": chunk_index,
            "count": chunk_count,
            "rules_required": chunk_index == 0,
        },
        "ranked_tokens": tokens,
        "requirements": [
            "Return one JSON object with top-level keys words and rules.",
            "Keep the response compact; do not add explanatory prose.",
            "Generate word entries only for ranked_tokens in this chunk.",
            "The words object must include exactly one non-underscore key per ranked token.",
            "Each word key must be the exact ranked_tokens token string.",
            "Do not include placeholder keys such as example_word.",
            "words must have _type='words', _locale, and _version.",
            "rules must have _type='rules', _locale, and _version.",
            "Each word entry must include types and inflections.",
            "Include base and priority for every word.",
            "Include antonyms only when obvious and useful.",
            "Include examples only for the highest-priority 10 words in the whole locale.",
            "Use priority values from ranked_tokens where possible.",
            "Mark regular inflections in inflections.regulars when applicable.",
            "Only chunk index 0 should generate locale-level rules.",
            "For other chunks, rules.rules and rules.tests should be empty arrays.",
            "Rules must use executable lookback/inflection/overrides shape, not prose notes.",
            "Rules must include tests for every generated executable rule.",
            "Use cardinal locations n, ne, e, se, s, sw, w, nw, c only.",
            "Avoid exhaustive rare morphology; prioritize useful common forms.",
        ],
        "response_shape": {
            "words": {
                "_type": "words",
                "_locale": target["locale"],
                "_version": VERSION,
                "<exact token from ranked_tokens>": {
                    "types": ["verb"],
                    "base": "<base form>",
                    "priority": 10,
                    "antonyms": [],
                    "examples": [],
                    "inflections": {"regulars": []},
                },
            },
            "rules": {
                "_type": "rules",
                "_locale": target["locale"],
                "_version": VERSION,
                "rules": [],
                "tests": [],
                "substitutions": {},
                "inflection_locations": {},
            },
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_request(
    target: dict[str, Any],
    model: str,
    tokens: list[dict[str, Any]],
    chunk_index: int,
    chunk_count: int,
) -> dict[str, Any] | None:
    """Build one batch request line for a target locale."""

    if not tokens:
        return None

    locale = target["locale"]
    custom_id = f"inflections-{locale}"
    if chunk_count > 1:
        custom_id = f"inflections-{locale}-chunk-{chunk_index + 1:03d}"
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": user_prompt(target, tokens, chunk_index, chunk_count),
                },
            ],
        },
    }


def chunk_tokens(
    tokens: list[dict[str, Any]],
    chunk_size: int,
) -> list[list[dict[str, Any]]]:
    """Split tokens into bounded chunks."""

    if chunk_size <= 0 or len(tokens) <= chunk_size:
        return [tokens]
    return [tokens[index : index + chunk_size] for index in range(0, len(tokens), chunk_size)]


def build_requests_for_target(
    target: dict[str, Any],
    model: str,
    top_n: int,
    chunk_size: int,
) -> list[dict[str, Any]]:
    """Build one or more request lines for a target locale."""

    source_locale = target.get("source_locale")
    if not isinstance(source_locale, str):
        return []
    tokens = load_tokens(source_locale, top_n)
    chunks = chunk_tokens(tokens, chunk_size)
    requests = []
    for chunk_index, token_chunk in enumerate(chunks):
        request = build_request(target, model, token_chunk, chunk_index, len(chunks))
        if request is not None:
            requests.append(request)
    return requests


def select_targets(
    manifest: dict[str, Any],
    locales: set[str] | None,
    priority_batch: int | None,
) -> list[dict[str, Any]]:
    """Select manifest targets for this build."""

    targets = manifest.get("targets")
    if not isinstance(targets, list):
        raise ValueError("manifest must contain a targets array")

    selected: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict):
            continue
        locale = target.get("locale")
        if not isinstance(locale, str):
            continue
        if locales is not None and locale not in locales:
            continue
        if priority_batch is not None:
            if target.get("priority_batch") != priority_batch:
                continue
        selected.append(target)
    return selected


def parse_locale_filter(value: str | None) -> set[str] | None:
    """Parse a comma-separated locale filter."""

    if value is None:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--top-n", type=int, default=500)
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Maximum tokens per generation request; 0 disables chunking",
    )
    parser.add_argument("--locales", help="Comma-separated locale filter")
    parser.add_argument("--priority-batch", type=int, default=1)
    parser.add_argument(
        "--all-batches",
        action="store_true",
        help="Ignore --priority-batch and include every eligible target",
    )
    return parser.parse_args()


def main() -> None:
    """Prepare batch requests."""

    args = parse_args()
    manifest = read_json(args.manifest)
    priority_batch = None if args.all_batches else args.priority_batch
    selected = select_targets(
        manifest,
        locales=parse_locale_filter(args.locales),
        priority_batch=priority_batch,
    )

    requests: list[dict[str, Any]] = []
    for target in selected:
        requests.extend(
            build_requests_for_target(target, args.model, args.top_n, args.chunk_size)
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / f"inflections_{timestamp}.jsonl"
    out_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests),
        encoding="utf-8",
    )
    print(f"Wrote {len(requests)} batch requests to {out_path}")


if __name__ == "__main__":
    main()
