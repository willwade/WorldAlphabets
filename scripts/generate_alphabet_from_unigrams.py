#!/usr/bin/env python3
"""Generate an alphabet JSON file from Simia unigrams data."""
from __future__ import annotations

import argparse
import json
import langcodes
import unicodedata
from pathlib import Path
from typing import Dict, Iterable
import urllib.request
import zipfile

try:  # optional dependency
    from icu import Collator, Locale  # type: ignore
except Exception:  # pragma: no cover - optional import
    Collator = None  # type: ignore[misc]
    Locale = None  # type: ignore[misc]

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


def _sort_letters(letters: Iterable[str], locale: str | None) -> list[str]:
    """Return ``letters`` sorted with optional locale aware rules."""
    if Collator and locale:
        try:
            collator = Collator.createInstance(Locale(locale))
            return sorted(letters, key=collator.getSortKey)
        except Exception:  # pragma: no cover - fallback to default sort
            pass
    return sorted(letters)


def _load_counts(code: str) -> Dict[str, int]:
    """Load character counts for ``code`` from unigrams file."""
    path = UNIGRAMS_DIR / f"unigrams-{code}.txt"
    if not path.exists():
        msg = f"No unigrams data for {code}"
        raise FileNotFoundError(msg)
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


def generate_alphabet(
    code: str, locale: str | None = None, block: str | None = None
) -> None:
    """Create alphabet JSON for ``code`` using unigrams data."""
    _download_unigrams()
    counts = _load_counts(code)
    lang = langcodes.get(code)
    letters = {
        ch
        for ch in counts
        if unicodedata.category(ch).startswith("L")
        and (block is None or block.upper() in unicodedata.name(ch, ""))
    }
    upper = {ch for ch in letters if ch.upper() != ch.lower() and ch == ch.upper()}
    lower = {ch for ch in letters if ch.upper() != ch.lower() and ch == ch.lower()}
    if not upper and not lower:
        # caseless script
        sorted_letters = _sort_letters(letters, locale)
        upper = lower = set(sorted_letters)
        alphabetical = sorted_letters
    else:
        alphabetical = _sort_letters({ch.upper() for ch in letters}, locale)
        upper = set(alphabetical)
        lower = {ch.lower() for ch in upper}
    total = sum(counts[ch] for ch in letters)
    freq = {ch: round(counts.get(ch, 0) / total, 4) for ch in lower}
    data = {
        "language": lang.language_name(),
        "iso639_3": lang.to_alpha3(),
        "alphabetical": alphabetical,
        "uppercase": _sort_letters(upper, locale),
        "lowercase": _sort_letters(lower, locale),
        "frequency": freq,
    }
    alpha2 = lang.language
    if alpha2 and len(alpha2) == 2:
        data["iso639_1"] = alpha2
    ALPHABETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ALPHABETS_DIR / f"{code}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", help="language code e.g. 'am'")
    parser.add_argument("--locale", help="ICU locale for sorting", dest="locale")
    parser.add_argument(
        "--block",
        help="Unicode block name substring for filtering (e.g. 'Ethiopic')",
        dest="block",
    )
    args = parser.parse_args()
    generate_alphabet(args.code, args.locale, args.block)


if __name__ == "__main__":
    main()
