#!/usr/bin/env python3
"""Generate letter frequency data from sample texts.

Downloads random Wikipedia articles to approximate letter frequencies for
languages missing corpus statistics. Articles shorter than a minimum length
are ignored. Provide language codes on the command line to restrict
processing; otherwise all languages without frequency data are updated.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import time
import urllib.request
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError, URLError

import langcodes

MIN_SAMPLE_CHARS = 2000
MAX_ATTEMPTS = 5
USER_AGENT = "WorldAlphabets frequency bot (https://github.com/nmslib/WorldAlphabets)"


def _wiki_subdomain(code: str) -> str:
    """Return the Wikipedia subdomain for a language code."""
    try:
        lang = langcodes.Language.get(code)
    except langcodes.LanguageTagError:
        return code
    sub = lang.language or code
    if len(sub) == 3 and len(code) < 3:
        sub = code
    return sub


def _random_article_url(code: str) -> str:
    sub = _wiki_subdomain(code)
    return f"https://{sub}.wikipedia.org/wiki/Special:Random?action=render"


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:  # nosec B310
        html = resp.read().decode("utf-8", errors="ignore")
    return re.sub(r"<[^>]+>", "", html)


def _sample_text(code: str) -> str | None:
    delay = 1.0
    for _ in range(MAX_ATTEMPTS):
        url = _random_article_url(code)
        try:
            sample = _fetch_text(url)
        except HTTPError as exc:  # pragma: no cover - network errors
            if exc.code == 429:
                print(
                    f"Rate limited fetching sample for {code}, sleeping {delay:.1f}s"
                )
                time.sleep(delay)
                delay *= 2
                continue
            print(f"Failed to fetch sample for {code}: HTTP {exc.code}")
            return None
        except URLError as exc:  # pragma: no cover - network errors
            if isinstance(exc.reason, socket.gaierror):
                print(f"No Wikipedia for {code}, skipping")
                return None
            print(f"Failed to fetch sample for {code}: {exc}")
            time.sleep(delay)
            delay *= 2
            continue
        if len(sample) >= MIN_SAMPLE_CHARS:
            return sample
        print(f"Sample for {code} too short ({len(sample)} chars), retrying")
        time.sleep(delay)
        delay *= 2
    return None


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "codes",
        nargs="*",
        help="language codes to process (default: all missing frequency data)",
    )
    args = parser.parse_args()

    alphabets_dir = Path("data/alphabets")
    index_path = Path("data/index.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))

    codes = args.codes or [
        entry["language"] for entry in index if not entry.get("frequency-avail")
    ]

    for code in codes:
        json_file = alphabets_dir / f"{code}.json"
        if not json_file.exists():
            print(f"No alphabet for {code}, skipping")
            continue
        sample = _sample_text(code)
        if sample is None:
            print(f"Could not find suitable sample for {code}, skipping")
            continue
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
