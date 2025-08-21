#!/usr/bin/env python3
"""Update letter frequency data using Simia unigrams dataset."""
from __future__ import annotations

import json
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict

UNIGRAMS_URL = "http://simia.net/letters/unigrams.zip"
UNIGRAMS_ZIP = Path("external/unigrams/unigrams.zip")
UNIGRAMS_DIR = UNIGRAMS_ZIP.parent


def _download_unigrams() -> None:
    """Download the unigrams dataset if not present."""
    if UNIGRAMS_ZIP.exists():
        return
    UNIGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(UNIGRAMS_URL) as resp:  # nosec B310
        UNIGRAMS_ZIP.write_bytes(resp.read())


def _load_unigram_freq(code: str) -> Dict[str, float] | None:
    """Return frequency mapping for ``code`` from the unigrams dataset."""
    path = UNIGRAMS_DIR / f"unigrams-{code}.txt"
    if not path.exists():
        return None
    counts: Dict[str, int] = {}
    total = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            char, count = line.split()
        except ValueError:
            continue
        counts[char] = int(count)
        total += int(count)
    if total == 0:
        return None
    return {ch: round(c / total, 4) for ch, c in counts.items()}


def main() -> None:
    _download_unigrams()
    with zipfile.ZipFile(UNIGRAMS_ZIP) as zf:
        zf.extractall(UNIGRAMS_DIR)

    alphabets_dir = Path("data/alphabets")
    for json_file in alphabets_dir.glob("*.json"):
        code = json_file.stem
        freq = _load_unigram_freq(code)
        if freq is None:
            print(f"No unigram data for {code}, skipping")
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        data["frequency"] = {ch: freq.get(ch, 0.0) for ch in data["lowercase"]}
        json_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Updated frequencies for {code}")


if __name__ == "__main__":
    main()
