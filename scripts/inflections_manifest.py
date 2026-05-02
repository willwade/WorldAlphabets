#!/usr/bin/env python3
"""Build a manifest of locales eligible for inflection data generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INDEX_PATH = DATA_DIR / "index.json"
FREQ_DIR = DATA_DIR / "freq" / "top1000"
OUT_DIR = DATA_DIR / "sources" / "inflections"
DEFAULT_OUT = OUT_DIR / "manifest.json"

VERSION = "0.1"

PRIORITY_LOCALES = [
    "en",
    "en-GB",
    "en-CA",
    "en-AU",
    "en-NZ",
    "en-ZA",
    "es",
    "es-419",
    "eu",
    "ca",
    "fr",
    "fr-CA",
    "pt",
    "pt-BR",
    "de",
    "nl",
    "nl-BE",
    "da",
    "no",
    "sv",
    "fo",
    "af",
    "ru",
    "uk",
    "pl",
    "cs",
    "sk",
    "sl",
    "hr",
    "ar",
    "he",
    "fi",
    "cy",
]


@dataclass(frozen=True)
class FrequencyInfo:
    """Frequency-list metadata for one source locale."""

    locale: str
    token_count: int
    mode: str


def read_json(path: Path) -> Any:
    """Read JSON from a file."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_index() -> dict[str, dict[str, Any]]:
    """Load language index entries keyed by language code."""

    entries = read_json(INDEX_PATH)
    if not isinstance(entries, list):
        raise ValueError(f"{INDEX_PATH} must contain a JSON array")

    by_language: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        language = entry.get("language")
        if isinstance(language, str) and language not in by_language:
            by_language[language] = entry
    return by_language


def load_frequency_infos() -> dict[str, FrequencyInfo]:
    """Load available top-token list metadata."""

    infos: dict[str, FrequencyInfo] = {}
    if not FREQ_DIR.exists():
        return infos

    for path in sorted(FREQ_DIR.glob("*.txt")):
        mode = "word"
        token_count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if token_count == 0 and stripped.startswith("#"):
                if "bigram" in stripped.lower():
                    mode = "bigram"
                continue
            token_count += 1
        infos[path.stem] = FrequencyInfo(
            locale=path.stem,
            token_count=token_count,
            mode=mode,
        )
    return infos


def base_locale(locale: str) -> str:
    """Return the base language portion of a locale."""

    return locale.split("-", 1)[0]


def resolve_source_locale(
    locale: str,
    frequency_infos: dict[str, FrequencyInfo],
) -> str | None:
    """Resolve which frequency list should seed generation for a locale."""

    if locale in frequency_infos:
        return locale
    base = base_locale(locale)
    if base in frequency_infos:
        return base
    return None


def infer_base_locale(locale: str, source_locale: str | None) -> str | None:
    """Return a base locale when a target should inherit from another locale."""

    base = base_locale(locale)
    if locale != base and source_locale == base:
        return base
    return None


def build_target(
    locale: str,
    priority_batch: int,
    index: dict[str, dict[str, Any]],
    frequency_infos: dict[str, FrequencyInfo],
) -> dict[str, Any]:
    """Build one manifest target entry."""

    language = base_locale(locale)
    entry = index.get(language, {})
    source_locale = resolve_source_locale(locale, frequency_infos)
    freq_info = frequency_infos.get(source_locale or "")

    return {
        "locale": locale,
        "language": language,
        "name": entry.get("name"),
        "script": entry.get("script"),
        "iso639_1": entry.get("iso639_1"),
        "iso639_3": entry.get("iso639_3"),
        "source_locale": source_locale,
        "base_locale": infer_base_locale(locale, source_locale),
        "priority_batch": priority_batch,
        "has_frequency": freq_info is not None,
        "frequency_mode": freq_info.mode if freq_info else None,
        "token_count": freq_info.token_count if freq_info else 0,
        "words": f"{locale}/words.json",
        "rules": f"{locale}/rules.json",
    }


def build_manifest(include_all_frequency: bool = True) -> dict[str, Any]:
    """Build the complete inflections generation manifest."""

    index = load_index()
    frequency_infos = load_frequency_infos()
    locales: dict[str, int] = {locale: 1 for locale in PRIORITY_LOCALES}

    if include_all_frequency:
        for locale in frequency_infos:
            locales.setdefault(locale, 2)

    targets = [
        build_target(locale, batch, index, frequency_infos)
        for locale, batch in sorted(locales.items())
    ]

    return {
        "_type": "inflection_manifest",
        "_version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "priority_locale_count": len(PRIORITY_LOCALES),
        "target_count": len(targets),
        "targets": targets,
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--priority-only",
        action="store_true",
        help="Only include first-batch priority locales",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output manifest path (default: {DEFAULT_OUT})",
    )
    return parser.parse_args()


def main() -> None:
    """Build and write the manifest."""

    args = parse_args()
    manifest = build_manifest(include_all_frequency=not args.priority_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    targets = manifest["target_count"]
    print(f"Wrote {targets} inflection targets to {args.output}")


if __name__ == "__main__":
    main()
