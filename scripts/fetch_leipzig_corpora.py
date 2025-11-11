#!/usr/bin/env python3
"""Report Leipzig coverage gaps and download corpora for missing languages."""

from __future__ import annotations

import argparse
import json
import tarfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Any

import requests
from bs4 import BeautifulSoup, Tag

# Shared user agent with other Leipzig integrations
USER_AGENT = "WorldAlphabets/1.0 (https://github.com/willwade/WorldAlphabets)"

DATA_DIR = Path("data")
LANG_INDEX_PATH = DATA_DIR / "index.json"
DEFAULT_WORD_DIR = Path("leipzig_output/words")
DEFAULT_CHAR_DIR = Path("leipzig_output/chars")
DEFAULT_JSON_DIR = Path("leipzig_output/json")
DEFAULT_CORPUS_ID = "eng_news_2024"
TOP_WORD_DIR = DATA_DIR / "freq" / "top1000"


@dataclass(slots=True)
class LanguageEntry:
    """Language entry from ``data/index.json``."""

    code: str
    script: str | None
    name: str
    iso639_3: str | None
    has_word_frequency: bool
    source_file: str | None
    word_frequency_tokens: int | None


@dataclass(slots=True)
class CorpusListing:
    """Available corpora for a Leipzig language."""

    language_name: str
    corpora: List[str]


@dataclass(slots=True)
class CorpusResult:
    """Parsed word and character frequency data for a corpus."""

    corpus_id: str
    words: List[str]
    word_counts: List[tuple[str, int]]
    char_counts: List[tuple[str, int]]


def count_word_frequency_tokens(code: str) -> int | None:
    """Return the number of tokens in ``data/freq/top1000/<code>.txt``."""

    if not code:
        return None
    path = TOP_WORD_DIR / f"{code}.txt"
    if not path.exists():
        return None
    tokens = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                tokens += 1
    return tokens


def _string_attr(element: Tag, attribute: str) -> str | None:
    value: Any | None = element.get(attribute)
    if isinstance(value, list):
        return value[0] if value else None
    if isinstance(value, str):
        return value
    return None


class LeipzigClient:
    """Helper for scraping the Leipzig corpus catalogue and downloads."""

    catalogue_url = (
        "https://corpora.wortschatz-leipzig.de/en/webservice/loadCorpusSelection"
    )
    download_base = "https://downloads.wortschatz-leipzig.de/corpora"

    def __init__(self) -> None:
        self._catalogue: Dict[str, CorpusListing] | None = None

    def catalogue(self) -> Dict[str, CorpusListing]:
        if self._catalogue is None:
            params = {"corpusId": DEFAULT_CORPUS_ID, "word": ""}
            resp = requests.get(
                self.catalogue_url,
                params=params,
                timeout=60,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            self._catalogue = self._parse_catalogue(resp.text)
        return self._catalogue

    @staticmethod
    def _parse_catalogue(html: str) -> Dict[str, CorpusListing]:
        soup = BeautifulSoup(html, "html.parser")
        result: Dict[str, CorpusListing] = {}
        for anchor in soup.select("a[data-lang-id]"):
            lang_id = _string_attr(anchor, "data-lang-id")
            if not lang_id:
                continue
            parent_li = anchor.find_parent("li")
            corpora: List[str] = []
            if parent_li is not None:
                for link in parent_li.select("a[data-corpus-id]"):
                    corpus_id = _string_attr(link, "data-corpus-id")
                    if corpus_id and corpus_id not in corpora:
                        corpora.append(corpus_id)
            else:
                corpus_id = _string_attr(anchor, "data-corpus-id")
                if corpus_id:
                    corpora.append(corpus_id)
            name = _string_attr(anchor, "data-corpus-name-en") or anchor.get_text(strip=True)
            result[lang_id] = CorpusListing(language_name=name, corpora=corpora)
        return result

    def choose_corpus(self, corpora: Sequence[str]) -> str | None:
        if not corpora:
            return None
        priority = [
            "_community_",
            "_news_",
            "_mixed_",
            "_web_",
            "_newscrawl_",
            "_wikipedia_",
        ]
        for token in priority:
            for corpus_id in corpora:
                if token in corpus_id:
                    return corpus_id
        return corpora[0]

    def download_corpus(self, corpus_id: str, dest: Path) -> Path:
        dest.mkdir(parents=True, exist_ok=True)
        archive_path = dest / f"{corpus_id}.tar.gz"
        if archive_path.exists():
            return archive_path
        url = f"{self.download_base}/{corpus_id}.tar.gz"
        with requests.get(
            url, stream=True, timeout=120, headers={"User-Agent": USER_AGENT}
        ) as resp:
            resp.raise_for_status()
            with archive_path.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        fh.write(chunk)
        return archive_path

    @staticmethod
    def extract_words(archive_path: Path, limit: int) -> CorpusResult:
        with tarfile.open(archive_path, "r:gz") as tar:
            word_member = next(
                (
                    member
                    for member in tar.getmembers()
                    if member.name.endswith("-words.txt")
                ),
                None,
            )
            if word_member is None:
                raise RuntimeError(
                    f"Could not locate word list inside {archive_path.name}"
                )
            handle = tar.extractfile(word_member)
            if handle is None:
                raise RuntimeError(
                    f"Failed to extract word list from {archive_path.name}"
                )
            words: List[str] = []
            word_counts: List[tuple[str, int]] = []
            char_counter: Counter[str] = Counter()
            for raw_line in handle:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 4:
                    continue
                token = parts[1].strip()
                try:
                    freq = int(parts[3])
                except ValueError:
                    continue
                if token:
                    if len(words) < limit:
                        words.append(token)
                        word_counts.append((token, freq))
                    for char in token:
                        char_counter[char] += freq
            char_counts = char_counter.most_common()
            return CorpusResult(
                corpus_id=word_member.name.split("/")[0],
                words=words,
                word_counts=word_counts,
                char_counts=char_counts,
            )


def load_language_entries(index_path: Path) -> List[LanguageEntry]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries: List[LanguageEntry] = []
    for item in data:
        tokens = count_word_frequency_tokens(item.get("language", ""))
        entries.append(
            LanguageEntry(
                code=item.get("language", ""),
                script=item.get("script"),
                name=item.get("name", ""),
                iso639_3=item.get("iso639_3"),
                has_word_frequency=bool(item.get("hasWordFrequency")),
                source_file=item.get("file"),
                word_frequency_tokens=tokens,
            )
        )
    return entries


def missing_word_languages(
    entries: Iterable[LanguageEntry], min_words: int
) -> List[LanguageEntry]:
    missing: Dict[str, LanguageEntry] = {}
    for entry in entries:
        tokens = entry.word_frequency_tokens
        has_full_coverage = tokens is not None and tokens >= min_words
        if has_full_coverage:
            continue
        key = entry.iso639_3 or entry.code
        if key not in missing:
            missing[key] = entry
    return sorted(missing.values(), key=lambda item: item.code)


def print_report(
    entries: Sequence[LanguageEntry],
    catalogue: Dict[str, CorpusListing],
    min_words: int,
) -> None:
    print(
        "Languages missing word frequency data "
        f"(expecting at least {min_words} tokens):"
    )
    for entry in entries:
        iso3 = entry.iso639_3 or "unknown"
        listing = catalogue.get(iso3)
        corp_summary = "no Leipzig corpora"
        if listing:
            corp_summary = f"{len(listing.corpora)} Leipzig corpora"
        tokens = entry.word_frequency_tokens
        if tokens is None or tokens == 0:
            coverage = "no existing list"
        else:
            coverage = f"{tokens} tokens"
        print(
            f"- {entry.code} ({entry.name}) [{iso3}] -> {coverage}; {corp_summary}"
        )


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def write_word_list(path: Path, words: Sequence[str]) -> None:
    content = "\n".join(words) + "\n"
    path.write_text(content, encoding="utf-8")


def write_char_counts(path: Path, counts: Sequence[tuple[str, int]]) -> None:
    payload = [
        {"character": char, "count": count}
        for char, count in counts
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_json_summary(path: Path, entry: LanguageEntry, result: CorpusResult) -> None:
    data = {
        "language": entry.code,
        "script": entry.script,
        "name": entry.name,
        "iso639_3": entry.iso639_3,
        "corpus_id": result.corpus_id,
        "word_tokens": [token for token, _ in result.word_counts],
        "word_counts": [
            {"token": token, "count": count} for token, count in result.word_counts
        ],
        "char_counts": [
            {"character": char, "count": count} for char, count in result.char_counts
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_targets(
    all_entries: Sequence[LanguageEntry],
    codes: Sequence[str] | None,
    include_missing: bool,
    min_words: int,
) -> List[LanguageEntry]:
    entries_by_code: Dict[str, LanguageEntry] = {}
    entries_by_iso3: Dict[str, LanguageEntry] = {}
    for entry in all_entries:
        if entry.code:
            entries_by_code[entry.code] = entry
        if entry.iso639_3:
            entries_by_iso3[entry.iso639_3] = entry
    targets: Dict[str, LanguageEntry] = {}
    if include_missing:
        for entry in missing_word_languages(all_entries, min_words):
            key = entry.iso639_3 or entry.code
            targets[key] = entry
    if codes:
        for code in codes:
            normalized = code.strip()
            candidate = entries_by_code.get(normalized)
            if candidate is None:
                candidate = entries_by_iso3.get(normalized)
            if candidate is None:
                print(f"Warning: Could not find language entry for '{code}'")
                continue
            entry = candidate
            key = entry.iso639_3 or entry.code
            targets[key] = entry
    return sorted(targets.values(), key=lambda item: item.code)


def fetch_command(args: argparse.Namespace) -> None:
    entries = load_language_entries(LANG_INDEX_PATH)
    target_entries = resolve_targets(
        entries, args.langs, args.all_missing, args.min_words
    )
    if not target_entries:
        print("No target languages selected")
        return

    client = LeipzigClient()
    catalogue = client.catalogue()
    ensure_dirs(args.word_output_dir, args.char_output_dir, args.json_output_dir)
    cache_dir = args.cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    for entry in target_entries:
        iso3 = entry.iso639_3
        if not iso3:
            print(f"Skipping {entry.code}: missing ISO 639-3 code")
            continue
        listing = catalogue.get(iso3)
        if listing is None:
            print(f"No Leipzig corpora found for {entry.code} ({iso3})")
            continue
        corpus_id = client.choose_corpus(listing.corpora)
        if corpus_id is None:
            print(f"No usable corpus choice for {entry.code} ({iso3})")
            continue
        try:
            archive = client.download_corpus(corpus_id, cache_dir)
            result = client.extract_words(archive, args.limit)
        except requests.HTTPError as exc:
            print(f"HTTP error for {entry.code} ({corpus_id}): {exc}")
            continue
        except Exception as exc:  # pragma: no cover - unexpected IO issues
            print(f"Failed to process {entry.code} ({corpus_id}): {exc}")
            continue

        word_path = args.word_output_dir / f"{entry.code}.txt"
        char_path = args.char_output_dir / f"{entry.code}.json"
        summary_path = args.json_output_dir / f"{entry.code}.json"

        if args.skip_existing and word_path.exists() and char_path.exists() and summary_path.exists():
            print(f"Skipping {entry.code}: outputs already exist")
            continue

        word_tokens = [token for token, _ in result.word_counts][: args.limit]
        write_word_list(word_path, word_tokens)
        write_char_counts(char_path, result.char_counts)
        write_json_summary(summary_path, entry, result)
        print(
            f"Wrote {entry.code}: {len(word_tokens)} words from {result.corpus_id}"
        )


def report_command(args: argparse.Namespace) -> None:
    entries = load_language_entries(LANG_INDEX_PATH)
    missing = missing_word_languages(entries, args.min_words)
    client = LeipzigClient()
    catalogue = client.catalogue() if args.show_sources else {}
    print_report(missing, catalogue, args.min_words)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report", help="List languages missing Leipzig-derived word frequencies"
    )
    report_parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Include the count of available Leipzig corpora for each language.",
    )
    report_parser.add_argument(
        "--min-words",
        type=int,
        default=1000,
        help="Minimum number of tokens required to consider coverage complete.",
    )
    report_parser.set_defaults(func=report_command)

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Download corpora for languages and emit word/character frequency files.",
    )
    fetch_parser.add_argument(
        "--langs",
        type=lambda value: [item.strip() for item in value.split(",") if item.strip()],
        help="Comma-separated ISO 639-1/2/3 codes to fetch.",
    )
    fetch_parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Fetch corpora for every language currently missing word frequency data.",
    )
    fetch_parser.add_argument(
        "--limit", type=int, default=1000, help="Number of top words to export."
    )
    fetch_parser.add_argument(
        "--min-words",
        type=int,
        default=1000,
        help=(
            "Treat languages with fewer than this many existing tokens as missing "
            "when using --all-missing."
        ),
    )
    fetch_parser.add_argument(
        "--word-output-dir",
        type=Path,
        default=DEFAULT_WORD_DIR,
        help="Directory for plain word lists (default: leipzig_output/words).",
    )
    fetch_parser.add_argument(
        "--char-output-dir",
        type=Path,
        default=DEFAULT_CHAR_DIR,
        help="Directory for character frequency JSON (default: leipzig_output/chars).",
    )
    fetch_parser.add_argument(
        "--json-output-dir",
        type=Path,
        default=DEFAULT_JSON_DIR,
        help="Directory for combined JSON summaries (default: leipzig_output/json).",
    )
    fetch_parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".leipzig_cache"),
        help="Directory for downloaded corpus archives (default: .leipzig_cache).",
    )
    fetch_parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip languages that already have output files.",
    )
    fetch_parser.set_defaults(func=fetch_command)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
