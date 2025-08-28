#!/usr/bin/env python3
"""Generate alphabet JSON files from CLDR exemplar data.

Letter frequencies come from the Simia dataset when available and fall back
to OpenSubtitles word frequencies otherwise.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from urllib.error import HTTPError

import langcodes
import requests

try:  # optional dependency for locale-aware sorting
    from icu import Collator, Locale  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional import
    Collator = None  # type: ignore[misc]
    Locale = None  # type: ignore[misc]

UNIGRAMS_URL = "http://simia.net/letters/unigrams.zip"
UNIGRAMS_ZIP = Path("external/unigrams/unigrams.zip")
UNIGRAMS_DIR = UNIGRAMS_ZIP.parent


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

CLDR_BASE = (
    "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json"
)


USER_AGENT = (
    "WorldAlphabets frequency bot (https://github.com/nmslib/WorldAlphabets)"
)


def _fetch_available_locales() -> Set[str]:
    """Return locales present in the CLDR core dataset."""
    url = f"{CLDR_BASE}/cldr-core/availableLocales.json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()["availableLocales"]["full"]
    return set(data)


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
    return {ch: round(counts[norm_map[ch]] / total, 4) for ch in letters}


def _parse_exemplars(text: str) -> list[str]:
    """Extract single-letter tokens from CLDR exemplar string."""
    letters: list[str] = []
    for token in text.strip("[]").split():
        if token.startswith("{") and token.endswith("}"):
            token = token[1:-1]
        for ch in token:
            ch = unicodedata.normalize("NFC", ch)
            if unicodedata.category(ch).startswith("L"):
                letters.append(ch)
    return letters


def build_alphabet(language: str, script: str) -> None:
    """Write alphabet JSON for ``language`` and ``script``."""
    locale = f"{language}-{script}"
    url = f"{CLDR_BASE}/cldr-misc-full/main/{locale}/characters.json"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        default_script = langcodes.get(language).maximize().script
        if script != default_script:
            raise ValueError(f"No CLDR data for {language}-{script}")
        locale = language
        url = f"{CLDR_BASE}/cldr-misc-full/main/{locale}/characters.json"
        resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        raise ValueError(f"No CLDR data for {language}-{script}")
    resp.raise_for_status()
    data = resp.json()["main"][locale]["characters"]
    exemplar = data["exemplarCharacters"]
    letters = set(_parse_exemplars(exemplar))
    if not letters:
        raise ValueError(f"No exemplar data for {locale}")
    has_case = any(ch.lower() != ch.upper() for ch in letters)
    if has_case:
        upper = {ch.upper() for ch in letters}
        lower = {ch.lower() for ch in upper}
    else:
        upper = lower = letters
    index = data.get("index")
    if index:
        order = {ch: i for i, ch in enumerate(_parse_exemplars(index))}

        def sort_key(ch: str) -> tuple[int, str]:
            return (order.get(ch, len(order)), ch)

        upper_sorted = sorted(upper, key=sort_key)
        lower_sorted = sorted(lower, key=sort_key)
        alphabetical = upper_sorted
    else:
        upper_sorted = _sort_letters(upper, locale)
        lower_sorted = _sort_letters(lower, locale)
        alphabetical = upper_sorted
    _download_unigrams()
    counts = _load_counts(language)
    total = sum(counts.get(ch, 0) for ch in lower_sorted)
    if total:
        freq = {
            ch: round(counts.get(ch, 0) / total, 4) for ch in lower_sorted
        }
    else:
        osfreq = _opensubtitles_frequency(language, lower_sorted)
        freq = osfreq if osfreq is not None else {ch: 0.0 for ch in lower_sorted}
    lang = langcodes.get(language)
    result: Dict[str, object] = {
        "language": lang.language_name(),
        "iso639_3": lang.to_alpha3(),
        "alphabetical": alphabetical,
        "uppercase": upper_sorted,
        "lowercase": lower_sorted,
        "frequency": freq,
        "script": script,
    }
    alpha2 = lang.language
    if alpha2 and len(alpha2) == 2:
        result["iso639_1"] = alpha2
    out_path = Path("data/alphabets") / f"{language}-{script}.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        if "hello_how_are_you" in existing:
            result["hello_how_are_you"] = existing["hello_how_are_you"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", nargs="?", help="ISO 639 code")
    parser.add_argument("script", nargs="?", help="ISO 15924 code")
    parser.add_argument(
        "--manifest",
        help="JSON file mapping languages to list of script codes",
    )
    args = parser.parse_args()
    if args.manifest:
        mapping = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        available = _fetch_available_locales()
        for lang, scripts in mapping.items():
            default_script = langcodes.get(lang).maximize().script
            for sc in scripts:
                locale = f"{lang}-{sc}"
                if locale not in available:
                    if lang not in available or sc != default_script:
                        print(f"No CLDR data for {locale}, skipping")
                        continue
                try:
                    build_alphabet(lang, sc)
                except Exception as exc:  # pragma: no cover - diagnostic output
                    print(f"Skipped {lang}-{sc}: {exc}")
    else:
        if not args.language or not args.script:
            parser.error("language and script required when not using --manifest")
        build_alphabet(args.language, args.script)


if __name__ == "__main__":
    main()
