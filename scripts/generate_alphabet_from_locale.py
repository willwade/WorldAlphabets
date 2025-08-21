#!/usr/bin/env python3
"""Generate an alphabet JSON file from ICU locale exemplar data.

The script uses the CLDR exemplar character set for a locale to derive the
canonical alphabet and optionally maps frequencies from the Simia unigrams
corpus when available.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Dict, Iterable
import urllib.request
import zipfile

try:  # optional dependency
    from icu import (  # type: ignore[import-not-found]
        Collator,
        Locale,
        LocaleData,
        ULocaleDataExemplarSetType,
    )
except Exception:  # pragma: no cover - optional import
    Collator = None  # type: ignore[misc]
    Locale = None  # type: ignore[misc]
    LocaleData = None  # type: ignore[misc]
    ULocaleDataExemplarSetType = None  # type: ignore[misc]

UNIGRAMS_URL = "http://simia.net/letters/unigrams.zip"
UNIGRAMS_ZIP = Path("external/unigrams/unigrams.zip")
UNIGRAMS_DIR = UNIGRAMS_ZIP.parent
ALPHABETS_DIR = Path("data/alphabets")


def _download_unigrams() -> None:
    """Download and extract the unigrams dataset if needed."""
    if UNIGRAMS_ZIP.exists():
        return
    UNIGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(UNIGRAMS_URL) as resp:  # nosec B310
        UNIGRAMS_ZIP.write_bytes(resp.read())
    with zipfile.ZipFile(UNIGRAMS_ZIP) as zf:
        zf.extractall(UNIGRAMS_DIR)


def _load_counts(code: str) -> Dict[str, int]:
    """Load character counts for ``code`` from unigrams file."""
    path = UNIGRAMS_DIR / f"unigrams-{code}.txt"
    if not path.exists():
        return {}
    counts: Dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            char, count = line.split()
        except ValueError:
            continue
        counts[char] = int(count)
    return counts


def _sort_letters(letters: Iterable[str], locale: str | None) -> list[str]:
    """Return ``letters`` sorted with optional locale aware rules."""
    if Collator and locale:
        try:
            collator = Collator.createInstance(Locale(locale))
            return sorted(letters, key=collator.getSortKey)
        except Exception:  # pragma: no cover - fallback to default sort
            pass
    return sorted(letters)


def generate_alphabet(code: str, locale: str | None = None, set_type: str = "index") -> None:
    """Create alphabet JSON for ``code`` using ICU exemplar characters."""
    if LocaleData is None or ULocaleDataExemplarSetType is None:
        raise ImportError("PyICU is required for this script")

    locale = locale or code
    ld = LocaleData(locale)
    exemplar_type = {
        "standard": 0,
        "index": ULocaleDataExemplarSetType.ES_INDEX,
        "auxiliary": ULocaleDataExemplarSetType.ES_AUXILIARY,
    }.get(set_type, ULocaleDataExemplarSetType.ES_INDEX)
    letters = {
        ch
        for ch in ld.getExemplarSet(exemplar_type)
        if unicodedata.category(ch).startswith("L")
    }

    has_case = any(ch.upper() != ch.lower() for ch in letters)
    if has_case:
        alphabetical = _sort_letters({ch.upper() for ch in letters}, locale)
        upper = set(alphabetical)
        lower = {ch.lower() for ch in upper}
    else:
        alphabetical = _sort_letters(letters, locale)
        upper = lower = set(alphabetical)

    _download_unigrams()
    counts = _load_counts(code)
    total = sum(counts.get(ch, 0) for ch in lower)
    if total > 0:
        freq = {ch: round(counts.get(ch, 0) / total, 4) for ch in lower}
    else:
        freq = {ch: 0.0 for ch in lower}

    data = {
        "alphabetical": alphabetical,
        "uppercase": _sort_letters(upper, locale),
        "lowercase": _sort_letters(lower, locale),
        "frequency": freq,
    }
    ALPHABETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ALPHABETS_DIR / f"{code}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", help="language code e.g. 'am'")
    parser.add_argument("--locale", help="ICU locale for sorting", dest="locale")
    parser.add_argument(
        "--set-type",
        choices=["standard", "index", "auxiliary"],
        default="index",
        help="exemplar character set to use",
    )
    args = parser.parse_args()
    generate_alphabet(args.code, args.locale, args.set_type)


if __name__ == "__main__":
    main()
