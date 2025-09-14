#!/usr/bin/env python3
"""
Unified Top-200 frequency data builder - consolidates all sources and approaches.

This script combines the best features from all previous build scripts:
- Original modular system (scripts/build_top200/)
- Comprehensive coverage approach 
- 3-priority plan implementation
- Extended HermitDave integration

Priority order for maximum coverage:
1. Leipzig Corpora Collection (Wortschatz) - High-quality news/web corpora
2. HermitDave FrequencyWords - OpenSubtitles/Wikipedia sources
3. Tatoeba sentences - Great for under-resourced languages
4. Existing alphabet frequency data - Character-level fallback
5. Simia unigrams - CJK character data

Usage:
    uv run python scripts/build_top200_unified.py --all
    uv run python scripts/build_top200_unified.py --langs en,fr,de
    uv run python scripts/build_top200_unified.py --missing-only
    uv run python scripts/build_top200_unified.py --force
"""

import argparse
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError

# Import existing modular components where possible
try:
    from scripts.build_top200.tokenize import char_bigrams, word_tokens
    from scripts.build_top200.normalize import normalize_token
    from scripts.build_top200.sources import load_hermitdave
except ImportError:
    # Fallback implementations if modular system not available
    def char_bigrams(text: str) -> List[str]:
        return [text[i:i+2] for i in range(len(text)-1)]
    
    def word_tokens(text: str) -> List[str]:
        import re
        return re.findall(r'\b\w+\b', text.lower())
    
    def normalize_token(token: str, lang: str, allowlists: Dict[str, Set[str]]) -> Optional[str]:
        return token.strip() if token.strip() else None

    def load_hermitdave(path: str | Path) -> List[str]:
        tokens = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.split()
                if parts:
                    tokens.append(parts[0])
        return tokens

USER_AGENT = "WorldAlphabets/1.0 (https://github.com/willwade/WorldAlphabets)"

def is_cjk_language(lang_code: str) -> bool:
    """Check if language uses CJK scripts requiring bigram tokenization."""
    cjk_languages = {'zh', 'ja', 'ko', 'th', 'my', 'km', 'lo'}
    return lang_code in cjk_languages or lang_code.startswith('zh-')

def tokenize_bigrams(text: str) -> List[str]:
    """Generate character bigrams from text."""
    return char_bigrams(text)

def tokenize_words(text: str) -> List[str]:
    """Tokenize text into words."""
    return word_tokens(text)

# Priority 1: Leipzig Corpora Collection
def fetch_leipzig_words(lang_code: str, limit: int = 200) -> Optional[List[str]]:
    """Fetch high-quality frequency data from Leipzig Corpora Collection."""
    # Comprehensive corpus mappings for major languages
    leipzig_mappings = {
        'en': ['eng_news_2013_1M', 'eng_news_2012_3M', 'eng_wikipedia_2012_1M'],
        'de': ['deu_news_2012_1M', 'deu_news_2012_3M', 'deu_wikipedia_2010_1M'],
        'fr': ['fra_news_2012_1M', 'fra_news_2011_3M', 'fra_wikipedia_2013_1M'],
        'es': ['spa_news_2011_1M', 'spa_news_2012_3M', 'spa_wikipedia_2013_1M'],
        'it': ['ita_news_2009_1M', 'ita_news_2012_3M', 'ita_wikipedia_2013_1M'],
        'pt': ['por_news_2012_1M', 'por_news_2011_3M', 'por_wikipedia_2013_1M'],
        'ru': ['rus_news_2013_1M', 'rus_news_2012_3M', 'rus_wikipedia_2013_1M'],
        'zh': ['cmn_news_2007_1M', 'cmn_news_2005_3M', 'cmn_wikipedia_2013_1M'],
        'ja': ['jpn_news_2008_1M', 'jpn_news_2012_3M', 'jpn_wikipedia_2013_1M'],
        'ar': ['ara_news_2013_1M', 'ara_news_2012_3M', 'ara_wikipedia_2013_1M'],
        'hi': ['hin_news_2012_1M', 'hin_news_2013_3M', 'hin_wikipedia_2013_1M'],
        'tr': ['tur_news_2012_1M', 'tur_news_2011_3M', 'tur_wikipedia_2013_1M'],
        'pl': ['pol_news_2012_1M', 'pol_news_2011_3M', 'pol_wikipedia_2013_1M'],
        'nl': ['nld_news_2012_1M', 'nld_news_2011_3M', 'nld_wikipedia_2013_1M'],
        'sv': ['swe_news_2012_1M', 'swe_news_2011_3M', 'swe_wikipedia_2013_1M'],
        'da': ['dan_news_2012_1M', 'dan_news_2011_3M', 'dan_wikipedia_2013_1M'],
        'no': ['nor_news_2012_1M', 'nor_news_2011_3M', 'nor_wikipedia_2013_1M'],
        'fi': ['fin_news_2012_1M', 'fin_news_2011_3M', 'fin_wikipedia_2013_1M'],
        'hu': ['hun_news_2012_1M', 'hun_news_2011_3M', 'hun_wikipedia_2013_1M'],
        'cs': ['ces_news_2012_1M', 'ces_news_2011_3M', 'ces_wikipedia_2013_1M'],
        'sk': ['slk_news_2012_1M', 'slk_news_2011_3M', 'slk_wikipedia_2013_1M'],
        'bg': ['bul_news_2012_1M', 'bul_news_2011_3M', 'bul_wikipedia_2013_1M'],
        'hr': ['hrv_news_2012_1M', 'hrv_news_2011_3M', 'hrv_wikipedia_2013_1M'],
        'sr': ['srp_news_2012_1M', 'srp_news_2011_3M', 'srp_wikipedia_2013_1M'],
        'sl': ['slv_news_2012_1M', 'slv_news_2011_3M', 'slv_wikipedia_2013_1M'],
        'et': ['est_news_2012_1M', 'est_news_2011_3M', 'est_wikipedia_2013_1M'],
        'lv': ['lav_news_2012_1M', 'lav_news_2011_3M', 'lav_wikipedia_2013_1M'],
        'lt': ['lit_news_2012_1M', 'lit_news_2011_3M', 'lit_wikipedia_2013_1M'],
        'ro': ['ron_news_2012_1M', 'ron_news_2011_3M', 'ron_wikipedia_2013_1M'],
        'el': ['ell_news_2012_1M', 'ell_news_2011_3M', 'ell_wikipedia_2013_1M'],
        'he': ['heb_news_2012_1M', 'heb_news_2011_3M', 'heb_wikipedia_2013_1M'],
        'th': ['tha_news_2012_1M', 'tha_news_2011_3M', 'tha_wikipedia_2013_1M'],
        'vi': ['vie_news_2012_1M', 'vie_news_2011_3M', 'vie_wikipedia_2013_1M'],
        'id': ['ind_news_2012_1M', 'ind_news_2011_3M', 'ind_wikipedia_2013_1M'],
        'ms': ['msa_news_2012_1M', 'msa_news_2011_3M', 'msa_wikipedia_2013_1M'],
        'tl': ['tgl_newscrawl_2013_300K', 'tgl_wikipedia_2013_300K'],
        'ko': ['kor_news_2008_1M', 'kor_news_2012_3M', 'kor_wikipedia_2013_1M'],
        'ca': ['cat_news_2012_1M', 'cat_news_2011_3M', 'cat_wikipedia_2013_1M'],
        'eu': ['eus_news_2012_1M', 'eus_news_2011_3M', 'eus_wikipedia_2013_1M'],
        'gl': ['glg_news_2012_1M', 'glg_news_2011_3M', 'glg_wikipedia_2013_1M'],
        'mt': ['mlt_news_2012_1M', 'mlt_news_2011_3M', 'mlt_wikipedia_2013_1M'],
        'is': ['isl_news_2012_1M', 'isl_news_2011_3M', 'isl_wikipedia_2013_1M'],
        'ga': ['gle_news_2012_1M', 'gle_news_2011_3M', 'gle_wikipedia_2013_1M'],
        'cy': ['cym_news_2012_1M', 'cym_news_2011_3M', 'cym_wikipedia_2013_1M'],
        'la': ['lat_news_2012_1M', 'lat_news_2011_3M', 'lat_wikipedia_2013_1M'],
        'eo': ['epo_news_2012_1M', 'epo_news_2011_3M', 'epo_wikipedia_2013_1M'],
    }
    
    corpora = leipzig_mappings.get(lang_code, [])
    
    for corpus_name in corpora:
        try:
            url = f"https://api.wortschatz-leipzig.de/ws/words/{corpus_name}/wordlist/?limit={limit}"
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            
            with urllib.request.urlopen(req) as resp:
                import json
                data = json.loads(resp.read().decode("utf-8"))
            
            if 'words' in data:
                words = [item['word'] for item in data['words'] if 'word' in item]
                if words:
                    print(f"  Leipzig: {len(words)} words from {corpus_name}")
                    return words[:limit]
                    
        except HTTPError as e:
            if e.code != 404:
                print(f"  Leipzig HTTP {e.code} for {corpus_name}")
        except Exception as e:
            print(f"  Leipzig error for {corpus_name}: {e}")
    
    return None

# Priority 2: HermitDave FrequencyWords  
def fetch_hermitdave_words(lang_code: str, limit: int = 200) -> Optional[List[str]]:
    """Fetch from HermitDave FrequencyWords repository."""
    hermitdave_mappings = {
        'en': 'en_50k.txt', 'es': 'es_50k.txt', 'fr': 'fr_50k.txt', 'de': 'de_50k.txt',
        'it': 'it_50k.txt', 'pt': 'pt_50k.txt', 'ru': 'ru_50k.txt', 'zh': 'zh_50k.txt',
        'ja': 'ja_50k.txt', 'ko': 'ko_50k.txt', 'ar': 'ar_50k.txt', 'hi': 'hi_50k.txt',
        'tr': 'tr_50k.txt', 'pl': 'pl_50k.txt', 'nl': 'nl_50k.txt', 'sv': 'sv_50k.txt',
        'da': 'da_50k.txt', 'no': 'no_50k.txt', 'fi': 'fi_50k.txt', 'hu': 'hu_50k.txt',
        'cs': 'cs_50k.txt', 'sk': 'sk_50k.txt', 'bg': 'bg_50k.txt', 'hr': 'hr_50k.txt',
        'sr': 'sr_50k.txt', 'sl': 'sl_50k.txt', 'et': 'et_50k.txt', 'lv': 'lv_50k.txt',
        'lt': 'lt_50k.txt', 'ro': 'ro_50k.txt', 'el': 'el_50k.txt', 'he': 'he_50k.txt',
        'th': 'th_50k.txt', 'vi': 'vi_50k.txt', 'id': 'id_50k.txt', 'ms': 'ms_50k.txt',
        'tl': 'tl_50k.txt', 'ca': 'ca_50k.txt', 'eu': 'eu_50k.txt', 'gl': 'gl_50k.txt',
        'mt': 'mt_50k.txt', 'is': 'is_50k.txt', 'ga': 'ga_50k.txt', 'cy': 'cy_50k.txt',
        'la': 'la_50k.txt', 'eo': 'eo_50k.txt', 'uk': 'uk_50k.txt', 'be': 'be_50k.txt',
        'mk': 'mk_50k.txt', 'sq': 'sq_50k.txt', 'az': 'az_50k.txt', 'ka': 'ka_50k.txt',
        'hy': 'hy_50k.txt', 'fa': 'fa_50k.txt', 'ur': 'ur_50k.txt', 'bn': 'bn_50k.txt',
        'ta': 'ta_50k.txt', 'te': 'te_50k.txt', 'ml': 'ml_50k.txt', 'kn': 'kn_50k.txt',
        'gu': 'gu_50k.txt', 'pa': 'pa_50k.txt', 'or': 'or_50k.txt', 'as': 'as_50k.txt',
        'ne': 'ne_50k.txt', 'si': 'si_50k.txt', 'my': 'my_50k.txt', 'km': 'km_50k.txt',
        'lo': 'lo_50k.txt', 'am': 'am_50k.txt', 'ti': 'ti_50k.txt', 'om': 'om_50k.txt',
        'so': 'so_50k.txt', 'sw': 'sw_50k.txt', 'ha': 'ha_50k.txt', 'yo': 'yo_50k.txt',
        'ig': 'ig_50k.txt', 'zu': 'zu_50k.txt', 'xh': 'xh_50k.txt', 'af': 'af_50k.txt'
    }
    
    filename = hermitdave_mappings.get(lang_code)
    if not filename:
        return None
    
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
        if e.code != 404:
            print(f"  HermitDave HTTP {e.code} for {filename}")
    except Exception as e:
        print(f"  HermitDave error for {filename}: {e}")
    
    return None

# Priority 3: Tatoeba sentences
def fetch_tatoeba_sentences(lang_code: str, limit: int = 200) -> Optional[List[str]]:
    """Fetch from Tatoeba sentences and extract top words."""
    # Tatoeba language code mappings (ISO 639-3)
    tatoeba_mappings = {
        'zh': 'cmn', 'nb': 'nor', 'nn': 'nno', 'cy': 'cym', 'tl': 'tgl',
        'jv': 'jav', 'su': 'sun', 'gn': 'grn', 'mn': 'mon', 'ay': 'aym',
        'qu': 'que', 'nah': 'nah', 'bo': 'bod', 'my': 'mya', 'km': 'khm',
        'lo': 'lao', 'si': 'sin', 'ne': 'nep', 'bn': 'ben', 'gu': 'guj',
        'pa': 'pan', 'ta': 'tam', 'te': 'tel', 'kn': 'kan', 'ml': 'mal',
        'or': 'ori', 'as': 'asm', 'ur': 'urd', 'fa': 'pes', 'ps': 'pus',
        'ku': 'kur', 'am': 'amh', 'ti': 'tir', 'om': 'orm', 'so': 'som',
        'ha': 'hau', 'yo': 'yor', 'ig': 'ibo', 'zu': 'zul', 'xh': 'xho',
        'af': 'afr', 'st': 'sot', 'tn': 'tsn', 'ss': 'ssw', 've': 'ven',
        'ts': 'tso', 'nr': 'nbl', 'ga': 'gle', 'mt': 'mlt', 'is': 'isl',
        'fo': 'fao', 'gd': 'gla', 'br': 'bre', 'co': 'cos', 'eu': 'eus',
        'ca': 'cat', 'gl': 'glg', 'oc': 'oci', 'la': 'lat', 'eo': 'epo',
        'ia': 'ina', 'ie': 'ile', 'vo': 'vol', 'jbo': 'jbo'
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
        if 'results' in data:
            for result in data['results']:
                if 'text' in result and 'lang' in result:
                    # Only include sentences in the target language
                    if result['lang'] == tatoeba_code:
                        sentence = result['text'].strip()
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

# Priority 4: Existing alphabet frequency data
def load_alphabet_frequencies(lang_code: str, limit: int = 200) -> Optional[List[str]]:
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
        with open(alphabet_file, 'r', encoding='utf-8') as f:
            import json
            alphabet_data = json.load(f)

        if alphabet_data and 'frequencies' in alphabet_data:
            # Extract character frequencies
            freq_data = alphabet_data['frequencies']
            if isinstance(freq_data, dict):
                # Sort by frequency (descending)
                sorted_chars = sorted(freq_data.items(), key=lambda x: x[1], reverse=True)
                chars = [char for char, freq in sorted_chars[:limit]]
                if chars:
                    print(f"  Alphabet: {len(chars)} characters from {alphabet_file.name}")
                    return chars

    except Exception as e:
        print(f"  Alphabet error for {lang_code}: {e}")

    return None

# Priority 5: Simia unigrams (CJK fallback)
def load_simia_unigrams(lang_code: str, limit: int = 200) -> Optional[List[str]]:
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
                with open(file_path, 'r', encoding='utf-8') as f:
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

def generate_bigrams(text: str, limit: int = 200) -> List[str]:
    """Generate bigrams from text with frequency counting."""
    bigram_counts = Counter(tokenize_bigrams(text))
    return [bigram for bigram, _ in bigram_counts.most_common(limit)]

def build_top200_unified(lang_code: str, output_dir: Path, force: bool = False) -> Tuple[bool, str]:
    """Build Top-200 list using unified 5-priority approach."""
    print(f"Building Top-200 for {lang_code} (unified approach)...")

    output_file = output_dir / f"{lang_code}.txt"
    if output_file.exists() and not force:
        print(f"  File already exists: {output_file}")
        return True, "Existing"

    use_bigrams = is_cjk_language(lang_code)
    tokens = None
    source_used = "Unknown"

    # Priority 1: Leipzig Corpora Collection
    tokens = fetch_leipzig_words(lang_code, 200)
    if tokens:
        source_used = "Leipzig"

    # Priority 2: HermitDave FrequencyWords
    if not tokens:
        words = fetch_hermitdave_words(lang_code, 200 if not use_bigrams else 1000)
        if words:
            if use_bigrams and lang_code.startswith('zh'):
                # Chinese words are often characters/phrases, use directly
                tokens = words[:200]
            elif use_bigrams:
                # Generate bigrams from text
                text = "".join(words)
                bigram_counts = Counter(tokenize_bigrams(text))
                tokens = [bigram for bigram, _ in bigram_counts.most_common(200)]
            else:
                tokens = words[:200]
            source_used = "HermitDave"

    # Priority 3: Tatoeba sentences
    if not tokens:
        tokens = fetch_tatoeba_sentences(lang_code, 200)
        if tokens:
            source_used = "Tatoeba"

    # Priority 4: Existing alphabet frequency data
    if not tokens:
        chars = load_alphabet_frequencies(lang_code, 200)
        if chars:
            if use_bigrams:
                # Generate bigrams from character sequence
                text = "".join(chars * 10)
                tokens = generate_bigrams(text, 200)
            else:
                # For word-based languages, characters aren't ideal but better than nothing
                tokens = chars[:200]
            source_used = "Alphabet"

    # Priority 5: Simia unigrams (CJK fallback)
    if not tokens:
        chars = load_simia_unigrams(lang_code, 200)
        if chars:
            if use_bigrams:
                # Generate bigrams from character sequence
                text = "".join(chars * 10)
                tokens = generate_bigrams(text, 200)
            else:
                tokens = chars[:200]
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
    parser.add_argument("--all", action="store_true", help="Process all supported languages")
    parser.add_argument("--missing-only", action="store_true", help="Only process languages missing frequency data")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--output-dir", default="data/freq/top200", help="Output directory")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine target languages
    if args.all:
        try:
            from worldalphabets import get_available_codes
            target_langs = get_available_codes()
        except ImportError:
            print("Error: Cannot import worldalphabets. Install the package or specify --langs")
            return
    elif args.missing_only:
        try:
            from worldalphabets import get_available_codes
            all_codes = get_available_codes()
            existing_codes = {f.stem for f in output_dir.glob("*.txt")}
            target_langs = sorted(set(all_codes) - existing_codes)
        except ImportError:
            print("Error: Cannot import worldalphabets. Install the package or specify --langs")
            return
    elif args.langs:
        target_langs = [code.strip() for code in args.langs.split(",")]
    else:
        print("Error: Must specify --langs, --all, or --missing-only")
        return

    print(f"Processing {len(target_langs)} languages using unified 5-priority approach...")
    print("Priority 1: Leipzig Corpora Collection")
    print("Priority 2: HermitDave FrequencyWords")
    print("Priority 3: Tatoeba sentences")
    print("Priority 4: Existing alphabet frequency data")
    print("Priority 5: Simia unigrams")
    print()

    successful = 0
    failed = 0
    sources_used = {"Leipzig": 0, "HermitDave": 0, "Tatoeba": 0, "Alphabet": 0, "Simia": 0, "Existing": 0}

    for lang_code in target_langs:
        success, source = build_top200_unified(lang_code, output_dir, force=args.force)
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
        "source": "Unified 5-Priority Pipeline (Leipzig + HermitDave + Tatoeba + Alphabet + Simia)",
        "successful": successful,
        "failed": failed,
        "languages": target_langs,
        "sources_used": sources_used
    }

    report_file = output_dir / "BUILD_REPORT_UNIFIED.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Build report written to {report_file}")

if __name__ == "__main__":
    main()
