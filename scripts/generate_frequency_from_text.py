#!/usr/bin/env python3
"""Generate letter frequency data from sample texts."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List

SAMPLE_TEXT_URLS: Dict[str, str] = {
    "cs": "https://cs.wikipedia.org/wiki/%C4%8Ce%C5%A1tina?action=render",
}


def _fetch_text(url: str) -> str:
    with urllib.request.urlopen(url) as resp:  # nosec B310
        html = resp.read().decode("utf-8", errors="ignore")
    return re.sub(r"<[^>]+>", "", html)


def _letter_frequency(text: str, letters: List[str]) -> Dict[str, float]:
    counts = {ch: 0 for ch in letters}
    total = 0
    for ch in text:
        if ch in counts:
            counts[ch] += 1
            total += 1
    if total == 0:
        return {ch: 0.0 for ch in letters}
    return {ch: round(counts[ch] / total, 4) for ch in letters}


def main() -> None:
    alphabets_dir = Path("data/alphabets")
    index_path = Path("data/index.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))

    for code, url in SAMPLE_TEXT_URLS.items():
        json_file = alphabets_dir / f"{code}.json"
        if not json_file.exists():
            print(f"No alphabet for {code}, skipping")
            continue
        sample = _fetch_text(url)
        data = json.loads(json_file.read_text(encoding="utf-8"))
        letters = data["lowercase"]
        if all(ch.upper() == ch and ch.lower() != ch for ch in letters):
            sample = sample.upper()
        else:
            sample = sample.lower()
        freq = _letter_frequency(sample, letters)
        data["frequency"] = freq
        json_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for entry in index:
            if entry["language"] == code:
                entry["frequency-avail"] = sum(freq.values()) > 0
                break
        print(f"Updated frequency for {code}")

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
