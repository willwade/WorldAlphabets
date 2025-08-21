#!/usr/bin/env python3
"""Generate alphabets for languages with Simia unigrams but no JSON file."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

from generate_alphabet_from_locale import (
    UNIGRAMS_DIR,
    _download_unigrams,
    generate_alphabet,
)


ALPHABETS_DIR = Path("data/alphabets")


def _missing_codes() -> list[str]:
    """Return language codes present in unigrams but missing in alphabets."""
    _download_unigrams()
    codes: list[str] = []
    for path in UNIGRAMS_DIR.glob("unigrams-*.txt"):
        m = re.match(r"unigrams-(.+)\.txt", path.name)
        if m:
            codes.append(m.group(1))
    existing = {p.stem for p in ALPHABETS_DIR.glob("*.json")}
    return sorted(set(codes) - existing)


def generate_all(limit: int | None = None) -> None:
    """Generate alphabets for all missing codes up to ``limit``."""
    codes = _missing_codes()
    if limit is not None:
        codes = codes[:limit]
    for code in codes:
        try:
            generate_alphabet(code, code)
        except Exception as exc:  # pragma: no cover - diagnostic output
            print(f"Skipped {code}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, help="only generate this many codes"
    )
    args = parser.parse_args()
    generate_all(args.limit)


if __name__ == "__main__":
    main()
