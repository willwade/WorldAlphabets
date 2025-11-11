#!/usr/bin/env python3
"""
Unified Top-1000 frequency data builder - consolidates all sources and approaches.

This script combines the best features from all previous build scripts:
- Original modular system (scripts/build_top200/)
- Comprehensive coverage approach
- 3-priority plan implementation
- Extended HermitDave integration

Priority order for maximum coverage:
1. Leipzig Corpora Collection (Wortschatz) - High-quality news/web corpora
2. HermitDave FrequencyWords - OpenSubtitles/Wikipedia sources
3. CommonVoice - Speech transcriptions for 130+ languages
4. Tatoeba sentences - Great for under-resourced languages
5. Existing alphabet frequency data - Character-level fallback
6. Simia unigrams - CJK character data

Usage:
    uv run python scripts/build_top200_unified.py --all
    uv run python scripts/build_top200_unified.py --langs en,fr,de
    uv run python scripts/build_top200_unified.py --missing-only
    uv run python scripts/build_top200_unified.py --force
"""

import argparse
import json
import tarfile
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError

import requests
from bs4 import BeautifulSoup

# Import existing modular components where possible
try:
    from scripts.build_top200.tokenize import char_bigrams, word_tokens
    from scripts.build_top200.normalize import normalize_token
    from scripts.build_top200.sources import load_hermitdave
except ImportError:
    # Fallback implementations if modular system not available
    def char_bigrams(text: str) -> List[str]:
        return [text[i : i + 2] for i in range(len(text) - 1)]

    def word_tokens(text: str) -> List[str]:
        import re

        return re.findall(r"\b\w+\b", text.lower())

    def normalize_token(
        token: str, lang: str, allowlists: Dict[str, Set[str]]
    ) -> Optional[str]:
        return token.strip() if token.strip() else None

    def load_hermitdave(path: str | Path) -> List[str]:
        tokens = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if parts:
                    tokens.append(parts[0])
        return tokens


USER_AGENT = "WorldAlphabets/1.0 (https://github.com/willwade/WorldAlphabets)"


def is_cjk_language(lang_code: str) -> bool:
    """Check if language uses CJK scripts requiring bigram tokenization."""
    cjk_languages = {"zh", "ja", "ko", "th", "my", "km", "lo"}
    return lang_code in cjk_languages or lang_code.startswith("zh-")


def tokenize_bigrams(text: str) -> List[str]:
    """Generate character bigrams from text."""
    return char_bigrams(text)


def tokenize_words(text: str) -> List[str]:
    """Tokenize text into words."""
    return word_tokens(text)


def _is_word(token: str) -> bool:
    """Check if a token is a word (not just punctuation/symbols)."""
    if not token:
        return False
    # A word must contain at least one letter or digit
    return any(c.isalpha() or c.isdigit() for c in token)


# Priority 1: Leipzig Corpora Collection (Dynamic Catalogue-Based)
class LeipzigClient:
    """Client for fetching Leipzig Corpora using dynamic catalogue discovery."""

    CATALOGUE_URL = "https://corpora.wortschatz-leipzig.de/en/webservice/loadCorpusSelection"
    DOWNLOAD_BASE = "https://downloads.wortschatz-leipzig.de/corpora"
    DEFAULT_CORPUS_ID = "eng_news_2024"

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._catalogue_cache: Optional[Dict] = None

    def get_catalogue(self) -> Dict:
        """Fetch and parse the Leipzig corpus catalogue."""
        if self._catalogue_cache is not None:
            return self._catalogue_cache

        try:
            params = {"corpusId": self.DEFAULT_CORPUS_ID, "word": ""}
            resp = requests.get(
                self.CATALOGUE_URL,
                params=params,
                timeout=60,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            self._catalogue_cache = self._parse_catalogue(resp.text)
            return self._catalogue_cache
        except Exception as e:
            print(f"  Leipzig catalogue error: {e}")
            return {}

    @staticmethod
    def _parse_catalogue(html: str) -> Dict:
        """Parse catalogue HTML to extract available corpora by ISO 639-3 code."""
        soup = BeautifulSoup(html, "html.parser")
        result: Dict[str, List[str]] = {}

        for anchor in soup.select("a[data-lang-id]"):
            lang_id_attr = anchor.get("data-lang-id")
            lang_id = lang_id_attr[0] if isinstance(lang_id_attr, list) else lang_id_attr
            if not lang_id:
                continue

            corpora: List[str] = []

            # Get corpus ID from the anchor itself
            corpus_id_attr = anchor.get("data-corpus-id")
            corpus_id = corpus_id_attr[0] if isinstance(corpus_id_attr, list) else corpus_id_attr
            if corpus_id and corpus_id not in corpora:
                corpora.append(corpus_id)

            # Look for nested corpora in parent list item
            parent_li = anchor.find_parent("li")
            if parent_li:
                for link in parent_li.select("a[data-corpus-id]"):
                    nested_id_attr = link.get("data-corpus-id")
                    nested_id = nested_id_attr[0] if isinstance(nested_id_attr, list) else nested_id_attr
                    if nested_id and nested_id not in corpora:
                        corpora.append(nested_id)

            if corpora:
                result[lang_id] = corpora

        return result

    @staticmethod
    def choose_corpus(corpora: List[str]) -> Optional[str]:
        """Choose the best corpus from available options based on priority."""
        if not corpora:
            return None

        priority = ["_community_", "_news_", "_mixed_", "_web_", "_newscrawl_", "_wikipedia_"]
        for token in priority:
            for corpus_id in corpora:
                if token in corpus_id:
                    return corpus_id
        return corpora[0]

    def download_corpus(self, corpus_id: str) -> Optional[Path]:
        """Download a corpus archive if not already cached."""
        archive_path = self.cache_dir / f"{corpus_id}.tar.gz"
        if archive_path.exists():
            return archive_path

        try:
            url = f"{self.DOWNLOAD_BASE}/{corpus_id}.tar.gz"
            with requests.get(url, stream=True, timeout=120, headers={"User-Agent": USER_AGENT}) as resp:
                resp.raise_for_status()
                with archive_path.open("wb") as fh:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            fh.write(chunk)
            return archive_path
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None  # Corpus doesn't exist
            raise

    @staticmethod
    def extract_words(archive_path: Path, limit: int) -> Optional[List[str]]:
        """Extract word list from Leipzig corpus archive."""
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                word_member = next(
                    (m for m in tar.getmembers() if m.name.endswith("-words.txt")),
                    None,
                )
                if not word_member:
                    return None

                handle = tar.extractfile(word_member)
                if not handle:
                    return None

                words: List[str] = []
                for raw_line in handle:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2:
                        continue
                    token = parts[1].strip()
                    if token and _is_word(token):
                        words.append(token)
                        if len(words) >= limit:
                            break

                return words
        except Exception:
            return None

    @staticmethod
    def generate_fallback_corpus_ids(iso3: str, primary_corpus_id: str) -> List[str]:
        """Generate fallback corpus IDs when primary corpus is unavailable."""
        fallbacks: List[str] = []
        corpus_types = ["community", "news", "mixed", "web", "newscrawl", "wikipedia"]
        years = ["2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]

        # Extract primary type
        primary_type = None
        for ctype in corpus_types:
            if f"_{ctype}_" in primary_corpus_id:
                primary_type = ctype
                break

        # Generate fallbacks
        for ctype in corpus_types:
            if ctype == primary_type:
                continue
            for year in years:
                fallback = f"{iso3}_{ctype}_{year}"
                if fallback != primary_corpus_id:
                    fallbacks.append(fallback)

        return fallbacks


def get_iso639_3_code(lang_code: str) -> Optional[str]:
    """Map language code to ISO 639-3 using the index."""
    try:
        index_path = Path("data/index.json")
        if not index_path.exists():
            return None

        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        for entry in index_data:
            if entry.get("language") == lang_code:
                return entry.get("iso639_3")

        return None
    except Exception:
        return None


def fetch_leipzig_words(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """Fetch high-quality frequency data from Leipzig Corpora Collection using dynamic catalogue."""
    # Get ISO 639-3 code for Leipzig lookup
    iso3 = get_iso639_3_code(lang_code)
    if not iso3:
        return None

    # Initialize client with cache
    cache_dir = Path(".leipzig_cache")
    client = LeipzigClient(cache_dir)

    # Get available corpora for this language
    catalogue = client.get_catalogue()
    corpora = catalogue.get(iso3, [])
    if not corpora:
        return None

    # Choose best corpus
    corpus_id = client.choose_corpus(corpora)
    if not corpus_id:
        return None

    # Try to download and extract with fallbacks
    tried_corpora = []
    for attempt_corpus_id in [corpus_id] + client.generate_fallback_corpus_ids(iso3, corpus_id):
        if attempt_corpus_id in tried_corpora:
            continue
        tried_corpora.append(attempt_corpus_id)

        try:
            archive = client.download_corpus(attempt_corpus_id)
            if not archive:
                continue  # 404, try next

            words = client.extract_words(archive, limit)
            if words:
                print(f"  Leipzig: {len(words)} words from {attempt_corpus_id}")
                return words
        except Exception:
            continue

    return None


# Priority 2: HermitDave FrequencyWords
def fetch_hermitdave_words(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """Fetch from HermitDave FrequencyWords repository.

    Tries multiple file patterns in order of preference:
    1. {lang}_full.txt (complete frequency data)
    2. {lang}_50k.txt (top 50k words)
    3. {lang}.txt (basic frequency list)
    """

    # Try multiple filename patterns in order of preference
    filename_patterns = [
        f"{lang_code}_full.txt",  # Most comprehensive
        f"{lang_code}_50k.txt",  # Standard 50k words
        f"{lang_code}.txt",  # Basic list
    ]

    for filename in filename_patterns:
        try:
            url = f"https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{lang_code}/{filename}"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

            with urllib.request.urlopen(req) as resp:
                text = resp.read().decode("utf-8", errors="ignore")

            words = []
            for line in text.splitlines()[:limit]:
                parts = line.split()
                if parts:
                    words.append(parts[0])

            if words:
                print(f"  HermitDave: {len(words)} words from {filename}")
                return words

        except HTTPError as e:
            if e.code == 404:
                continue  # Try next filename pattern
            else:
                print(f"  HermitDave HTTP {e.code} for {filename}")
        except Exception as e:
            print(f"  HermitDave error for {filename}: {e}")
            continue  # Try next filename pattern

    return None


# Priority 3: Tatoeba sentences
def fetch_tatoeba_sentences(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """Fetch from Tatoeba sentences and extract top words."""
    # Tatoeba language code mappings (ISO 639-3)
    tatoeba_mappings = {
        "zh": "cmn",
        "nb": "nor",
        "nn": "nno",
        "cy": "cym",
        "tl": "tgl",
        "jv": "jav",
        "su": "sun",
        "gn": "grn",
        "mn": "mon",
        "ay": "aym",
        "qu": "que",
        "nah": "nah",
        "bo": "bod",
        "my": "mya",
        "km": "khm",
        "lo": "lao",
        "si": "sin",
        "ne": "nep",
        "bn": "ben",
        "gu": "guj",
        "pa": "pan",
        "ta": "tam",
        "te": "tel",
        "kn": "kan",
        "ml": "mal",
        "or": "ori",
        "as": "asm",
        "ur": "urd",
        "fa": "pes",
        "ps": "pus",
        "ku": "kur",
        "am": "amh",
        "ti": "tir",
        "om": "orm",
        "so": "som",
        "ha": "hau",
        "yo": "yor",
        "ig": "ibo",
        "zu": "zul",
        "xh": "xho",
        "af": "afr",
        "st": "sot",
        "tn": "tsn",
        "ss": "ssw",
        "ve": "ven",
        "ts": "tso",
        "nr": "nbl",
        "ga": "gle",
        "mt": "mlt",
        "is": "isl",
        "fo": "fao",
        "gd": "gla",
        "br": "bre",
        "co": "cos",
        "eu": "eus",
        "ca": "cat",
        "gl": "glg",
        "oc": "oci",
        "la": "lat",
        "eo": "epo",
        "ia": "ina",
        "ie": "ile",
        "vo": "vol",
        "jbo": "jbo",
    }

    tatoeba_code = tatoeba_mappings.get(lang_code, lang_code)

    try:
        # Get sentences using the search API
        url = f"https://tatoeba.org/en/api_v0/search?from={tatoeba_code}&query=&sort=random&limit=500"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req) as resp:
            import json

            data = json.loads(resp.read().decode("utf-8"))

        # Extract sentences from API response - filter by correct language
        sentences = []
        if "results" in data:
            for result in data["results"]:
                if "text" in result and "lang" in result:
                    # Only include sentences in the target language
                    if result["lang"] == tatoeba_code:
                        sentence = result["text"].strip()
                        if sentence and len(sentence) > 5:  # Skip very short sentences
                            sentences.append(sentence)

        if not sentences:
            return None

        # Tokenize all sentences and count word frequencies
        use_bigrams = is_cjk_language(lang_code)
        word_counts: Counter[str] = Counter()

        for sentence in sentences:
            if use_bigrams:
                tokens = tokenize_bigrams(sentence)
            else:
                tokens = tokenize_words(sentence)
            word_counts.update(tokens)

        # Get top words
        top_words = [word for word, count in word_counts.most_common(limit)]

        if top_words:
            print(f"  Tatoeba: {len(top_words)} tokens from {len(sentences)} sentences")
            return top_words

    except HTTPError as e:
        if e.code != 404:
            print(f"  Tatoeba HTTP {e.code} for {tatoeba_code}")
    except Exception as e:
        print(f"  Tatoeba error for {tatoeba_code}: {e}")

    return None


# Priority 3: CommonVoice speech transcriptions
def fetch_commonvoice_words(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """
    Fetch word frequencies from CommonVoice transcriptions.

    Requires manually downloaded CommonVoice datasets in .cache/commonvoice/<lang>/
    See scripts/download_commonvoice_manual.md for instructions.
    """
    import csv

    cache_dir = Path(".cache/commonvoice") / lang_code

    if not cache_dir.exists():
        return None

    # Find validated.tsv file
    tsv_path = cache_dir / "validated.tsv"

    if not tsv_path.exists():
        # Try in subdirectory (CommonVoice extracts to cv-corpus-*/)
        subdirs = list(cache_dir.glob("cv-corpus-*"))
        if subdirs:
            tsv_path = subdirs[0] / lang_code / "validated.tsv"

    if not tsv_path.exists():
        return None

    try:
        # Read transcriptions from TSV
        transcriptions = []
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                text = row.get("sentence", "").strip()
                if text:
                    transcriptions.append(text)

        if not transcriptions:
            return None

        # Tokenize and count word frequencies
        use_bigrams = is_cjk_language(lang_code)
        word_counts: Counter[str] = Counter()

        for text in transcriptions:
            if use_bigrams:
                tokens = tokenize_bigrams(text)
            else:
                tokens = tokenize_words(text)
                # Filter out non-words (punctuation, etc.)
                tokens = [t for t in tokens if _is_word(t)]
            word_counts.update(tokens)

        # Get top words
        top_words = [word for word, count in word_counts.most_common(limit)]

        if top_words:
            print(f"  CommonVoice: {len(top_words)} tokens from {len(transcriptions)} transcriptions")
            return top_words

    except Exception as e:
        print(f"  CommonVoice error for {lang_code}: {e}")

    return None


# Priority 5: Existing alphabet frequency data
def load_alphabet_frequencies(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """Load character frequencies from existing alphabet data."""
    try:
        # Try to load from existing alphabet JSON files
        alphabet_dir = Path("data/alphabets")
        if not alphabet_dir.exists():
            return None

        # Look for alphabet files for this language
        alphabet_files = list(alphabet_dir.glob(f"{lang_code}-*.json"))
        if not alphabet_files:
            return None

        # Try the first available alphabet file
        alphabet_file = alphabet_files[0]
        with open(alphabet_file, "r", encoding="utf-8") as f:
            import json

            alphabet_data = json.load(f)

        if alphabet_data and "frequencies" in alphabet_data:
            # Extract character frequencies
            freq_data = alphabet_data["frequencies"]
            if isinstance(freq_data, dict):
                # Sort by frequency (descending)
                sorted_chars = sorted(
                    freq_data.items(), key=lambda x: x[1], reverse=True
                )
                chars = [char for char, freq in sorted_chars[:limit]]
                if chars:
                    print(
                        f"  Alphabet: {len(chars)} characters from {alphabet_file.name}"
                    )
                    return chars

    except Exception as e:
        print(f"  Alphabet error for {lang_code}: {e}")

    return None


# Priority 5: Simia unigrams (CJK fallback)
def load_simia_unigrams(lang_code: str, limit: int = 1000) -> Optional[List[str]]:
    """Load character data from Simia unigrams for CJK languages."""
    if not is_cjk_language(lang_code):
        return None

    try:
        # Check for Simia data files
        simia_dir = Path("data/sources/simia")
        if not simia_dir.exists():
            return None

        # Look for language-specific files
        possible_files = [
            simia_dir / f"{lang_code}-unigrams.txt",
            simia_dir / f"{lang_code}_unigrams.txt",
            simia_dir / f"unigrams-{lang_code}.txt",
        ]

        for file_path in possible_files:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    chars = []
                    for line in f:
                        char = line.strip().split()[0] if line.strip() else None
                        if char and len(char) == 1:  # Single characters only
                            chars.append(char)
                        if len(chars) >= limit:
                            break

                if chars:
                    print(f"  Simia: {len(chars)} characters from {file_path.name}")
                    return chars

    except Exception as e:
        print(f"  Simia error for {lang_code}: {e}")

    return None


def generate_bigrams(text: str, limit: int = 1000) -> List[str]:
    """Generate bigrams from text with frequency counting."""
    bigram_counts = Counter(tokenize_bigrams(text))
    return [bigram for bigram, _ in bigram_counts.most_common(limit)]


def build_top1000_unified(
    lang_code: str, output_dir: Path, force: bool = False
) -> Tuple[bool, str]:
    """Build Top-1000 list using unified 6-priority approach."""
    print(f"Building Top-1000 for {lang_code} (unified approach)...")

    output_file = output_dir / f"{lang_code}.txt"
    if output_file.exists() and not force:
        print(f"  File already exists: {output_file}")
        return True, "Existing"

    use_bigrams = is_cjk_language(lang_code)
    tokens = None
    source_used = "Unknown"

    # Priority 1: Leipzig Corpora Collection
    tokens = fetch_leipzig_words(lang_code, 1000)
    if tokens:
        source_used = "Leipzig"

    # Priority 2: HermitDave FrequencyWords
    if not tokens:
        words = fetch_hermitdave_words(lang_code, 1000 if not use_bigrams else 2000)
        if words:
            if use_bigrams and lang_code.startswith("zh"):
                # Chinese words are often characters/phrases, use directly
                tokens = words[:1000]
            elif use_bigrams:
                # Generate bigrams from text
                text = "".join(words)
                bigram_counts = Counter(tokenize_bigrams(text))
                tokens = [bigram for bigram, _ in bigram_counts.most_common(1000)]
            else:
                tokens = words[:1000]
            source_used = "HermitDave"

    # Priority 3: CommonVoice speech transcriptions
    if not tokens:
        tokens = fetch_commonvoice_words(lang_code, 1000)
        if tokens:
            source_used = "CommonVoice"

    # Priority 4: Tatoeba sentences
    if not tokens:
        tokens = fetch_tatoeba_sentences(lang_code, 1000)
        if tokens:
            source_used = "Tatoeba"

    # Priority 5: Existing alphabet frequency data
    if not tokens:
        chars = load_alphabet_frequencies(lang_code, 1000)
        if chars:
            if use_bigrams:
                # Generate bigrams from character sequence
                text = "".join(chars * 10)
                tokens = generate_bigrams(text, 1000)
            else:
                # For word-based languages, characters aren't ideal but better than nothing
                tokens = chars[:1000]
            source_used = "Alphabet"

    # Priority 6: Simia unigrams (CJK fallback)
    if not tokens:
        chars = load_simia_unigrams(lang_code, 1000)
        if chars:
            if use_bigrams:
                # Generate bigrams from character sequence
                text = "".join(chars * 10)
                tokens = generate_bigrams(text, 1000)
            else:
                tokens = chars[:1000]
            source_used = "Simia"

    if not tokens:
        print(f"  No frequency data available for {lang_code}")
        return False, "None"

    # Write the file
    header = "# type=bigram\n" if use_bigrams else ""
    content = header + "\n".join(tokens) + "\n"

    output_file.write_text(content, encoding="utf-8")
    print(f"  Generated {len(tokens)} tokens for {lang_code} (source: {source_used})")
    return True, source_used


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--langs", help="Comma-separated language codes")
    parser.add_argument(
        "--all", action="store_true", help="Process all supported languages"
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only process languages missing frequency data",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--output-dir", default="data/freq/top1000", help="Output directory"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine target languages
    if args.all:
        try:
            from worldalphabets import get_available_codes

            target_langs = get_available_codes()
        except ImportError:
            print(
                "Error: Cannot import worldalphabets. Install the package or specify --langs"
            )
            return
    elif args.missing_only:
        try:
            from worldalphabets import get_available_codes

            all_codes = get_available_codes()
            existing_codes = {f.stem for f in output_dir.glob("*.txt")}
            target_langs = sorted(set(all_codes) - existing_codes)
        except ImportError:
            print(
                "Error: Cannot import worldalphabets. Install the package or specify --langs"
            )
            return
    elif args.langs:
        target_langs = [code.strip() for code in args.langs.split(",")]
    else:
        print("Error: Must specify --langs, --all, or --missing-only")
        return

    print(
        f"Processing {len(target_langs)} languages using unified 6-priority approach..."
    )
    print("Priority 1: Leipzig Corpora Collection")
    print("Priority 2: HermitDave FrequencyWords")
    print("Priority 3: CommonVoice speech transcriptions")
    print("Priority 4: Tatoeba sentences")
    print("Priority 5: Existing alphabet frequency data")
    print("Priority 6: Simia unigrams")
    print()

    successful = 0
    failed = 0
    sources_used = {
        "Leipzig": 0,
        "HermitDave": 0,
        "CommonVoice": 0,
        "Tatoeba": 0,
        "Alphabet": 0,
        "Simia": 0,
        "Existing": 0,
    }

    for lang_code in target_langs:
        success, source = build_top1000_unified(lang_code, output_dir, force=args.force)
        if success:
            successful += 1
            sources_used[source] = sources_used.get(source, 0) + 1
        else:
            failed += 1

    print(f"\nCompleted: {successful} successful, {failed} failed")
    print("Sources used:")
    for source, count in sources_used.items():
        if count > 0:
            print(f"  {source}: {count} languages")

    # Write build report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Unified 6-Priority Pipeline (Leipzig + HermitDave + CommonVoice + Tatoeba + Alphabet + Simia)",
        "successful": successful,
        "failed": failed,
        "languages": target_langs,
        "sources_used": sources_used,
    }

    report_file = output_dir / "BUILD_REPORT_UNIFIED.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Build report written to {report_file}")


if __name__ == "__main__":
    main()
