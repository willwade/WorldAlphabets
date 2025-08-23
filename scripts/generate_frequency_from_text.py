#!/usr/bin/env python3
"""Generate letter frequency data from sample texts.

Downloads sample text to approximate letter frequencies for languages missing
corpus statistics. By default it pulls random Wikipedia articles, but it can
also query the Google Books Ngram API for supported languages or consume word
frequency lists from the OpenSubtitles project. Articles shorter than a
minimum length are ignored. Provide language codes on the command line to
restrict processing; otherwise all languages without frequency data are
updated.
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError

import langcodes
import unicodedata

MIN_SAMPLE_CHARS = 2000
MAX_ATTEMPTS = 5
USER_AGENT = "WorldAlphabets frequency bot (https://github.com/nmslib/WorldAlphabets)"
SOURCE_CHOICES = ("wikipedia", "gbooks", "opensubtitles")


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
    norm_map = {ch: unicodedata.normalize("NFKC", ch) for ch in letters}
    unique_letters: List[str] = []
    for norm in norm_map.values():
        if norm not in unique_letters:
            unique_letters.append(norm)
    counts = {ch: 0 for ch in unique_letters}
    total = 0
    for ch in unicodedata.normalize("NFKC", text):
        if ch in counts:
            counts[ch] += 1
            total += 1
    if total == 0:
        return {ch: 0.0 for ch in letters}
    return {
        ch: round(counts[norm_map[ch]] / total, 4)
        for ch in letters
    }


def _gbooks_frequency(code: str, letters: List[str]) -> Optional[Dict[str, float]]:
    norm_map = {ch: unicodedata.normalize("NFKC", ch) for ch in letters}
    unique_letters: List[str] = []
    for norm in norm_map.values():
        if norm not in unique_letters:
            unique_letters.append(norm)
    content = ",".join(unique_letters)
    params = urllib.parse.urlencode(
        {
            "content": content,
            "year_start": 2000,
            "year_end": 2019,
            "corpus": code,
            "smoothing": 0,
            "case_insensitive": "true",
        }
    )
    url = f"https://books.google.com/ngrams/interactive_chart?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
            html = resp.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:  # pragma: no cover - network errors
        if exc.code == 404:
            print(f"No Google Books corpus for {code}, skipping")
        else:
            print(
                f"Failed to fetch Google Books data for {code}: HTTP {exc.code}"
            )
        return None
    match = re.search(
        r'<script id="ngrams-data" type="application/json">([^<]+)</script>',
        html,
    )
    if not match:
        print(f"No frequency data in Google Books response for {code}")
        return None
    data = json.loads(match.group(1))
    freqs_norm = {}
    for entry in data:
        if entry.get("type") not in {"CASE_INSENSITIVE", "NGRAM"}:
            continue
        letter = entry["ngram"].split(" (All)")[0]
        if letter in unique_letters:
            series = entry["timeseries"]
            freqs_norm[letter] = sum(series) / len(series)
    if not freqs_norm:
        print(f"No frequency data from Google Books for {code}")
        return None
    total = sum(freqs_norm.values())
    return {
        ch: round(freqs_norm.get(norm_map[ch], 0.0) / total, 4) for ch in letters
    }


def _opensubtitles_frequency(
    code: str, letters: List[str]
) -> Optional[Dict[str, float]]:
    base = _wiki_subdomain(code)
    url = (
        "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/"
        f"content/2018/{base}/{base}_50k.txt"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req) as resp:  # nosec B310
            text = resp.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:  # pragma: no cover - network errors
        if exc.code == 404:
            print(f"No OpenSubtitles data for {code}, skipping")
        else:
            print(
                f"Failed to fetch OpenSubtitles data for {code}: HTTP {exc.code}"
            )
        return None
    norm_map = {ch: unicodedata.normalize("NFKC", ch) for ch in letters}
    counts = {norm: 0 for norm in set(norm_map.values())}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        word, freq_str = parts
        try:
            freq = int(freq_str)
        except ValueError:
            continue
        if all(ch.upper() == ch and ch.lower() != ch for ch in letters):
            word = word.upper()
        else:
            word = word.lower()
        word = unicodedata.normalize("NFKC", word)
        for ch in word:
            if ch in counts:
                counts[ch] += freq
    total = sum(counts.values())
    if total == 0:
        return {ch: 0.0 for ch in letters}
    return {
        ch: round(counts[norm_map[ch]] / total, 4)
        for ch in letters
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "codes",
        nargs="*",
        help="language codes to process (default: all missing frequency data)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="process all languages regardless of existing data",
    )
    parser.add_argument(
        "--source",
        choices=list(SOURCE_CHOICES),
        default=SOURCE_CHOICES[0],
        help=(
            "text source for frequency estimation ("
            + ", ".join(SOURCE_CHOICES)
            + ")"
        ),
    )
    args = parser.parse_args()

    alphabets_dir = Path("data/alphabets")
    index_path = Path("data/index.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))

    if args.all:
        codes = [entry["language"] for entry in index]
    elif args.codes:
        codes = args.codes
    else:
        codes = [
            entry["language"] for entry in index if not entry.get("frequency-avail")
        ]

    for code in codes:
        json_file = alphabets_dir / f"{code}.json"
        if not json_file.exists():
            print(f"No alphabet for {code}, skipping")
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        letters = data["lowercase"]
        if args.source == "wikipedia":
            sample = _sample_text(code)
            if sample is None:
                print(f"Could not find suitable sample for {code}, skipping")
                continue
            if all(ch.upper() == ch and ch.lower() != ch for ch in letters):
                sample = sample.upper()
            else:
                sample = sample.lower()
            freq = _letter_frequency(sample, letters)
        elif args.source == "gbooks":
            gfreq = _gbooks_frequency(code, letters)
            if gfreq is None:
                print(f"Could not fetch Google Books sample for {code}, skipping")
                continue
            freq = gfreq
        else:
            osfreq = _opensubtitles_frequency(code, letters)
            if osfreq is None:
                print(
                    f"Could not fetch OpenSubtitles data for {code}, skipping"
                )
                continue
            freq = osfreq
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
