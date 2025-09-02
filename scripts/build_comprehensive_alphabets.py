#!/usr/bin/env python3
"""Enhanced alphabet builder with better coverage and error handling.

This script improves upon build_alphabet_from_cldr.py by:
1. Adding fallback data sources for missing languages
2. Better error handling and reporting
3. Support for more script systems
4. Enhanced frequency data collection
"""
from __future__ import annotations

import argparse
import json
import logging
import unicodedata
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError

import langcodes
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from icu import Collator, Locale
except ImportError:
    logger.warning("PyICU not available, falling back to basic sorting")
    Collator = None
    Locale = None

CLDR_BASE = "https://raw.githubusercontent.com/unicode-org/cldr-json/main/cldr-json"
USER_AGENT = "WorldAlphabets frequency bot (https://github.com/willwade/WorldAlphabets)"

# Fallback alphabet data for common languages missing from CLDR
FALLBACK_ALPHABETS = {
    "ja": {
        "Hira": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん",
        "Kana": "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
        "Jpan": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
    },
    "ko": {
        "Hang": "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ"
    },
    "zh": {
        "Hans": "一二三四五六七八九十百千万亿的是在有人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三",
        "Hant": "一二三四五六七八九十百千萬億的是在有人這中大為上個國我以要他時來用們生到作地於出就分對成會可主發年動同工也能下過子說產種面而方後多定行學法所民得經十三"
    },
    "om": {
        "Latn": "abcdefghijklmnopqrstuvwxyz"  # Basic for now - needs proper Oromo alphabet with digraphs
    }
}

class AlphabetBuilder:
    def __init__(self):
        self.unigrams_dir = Path("external/unigrams")
        self.unigrams_zip = self.unigrams_dir / "unigrams.zip"
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "cldr_missing": 0,
            "frequency_missing": 0,
            "fallback_used": 0,
            "errors": []
        }

    def download_unigrams(self) -> None:
        """Download and extract the unigrams dataset if needed."""
        if self.unigrams_zip.exists():
            return
        
        logger.info("Downloading unigrams dataset...")
        self.unigrams_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with urllib.request.urlopen("http://simia.net/letters/unigrams.zip") as resp:
                self.unigrams_zip.write_bytes(resp.read())
            
            with zipfile.ZipFile(self.unigrams_zip) as zf:
                zf.extractall(self.unigrams_dir)
            logger.info("Unigrams dataset downloaded successfully")
        except Exception as e:
            logger.error(f"Failed to download unigrams: {e}")

    def load_frequency_data(self, code: str) -> Dict[str, int]:
        """Load character frequency data from unigrams file."""
        path = self.unigrams_dir / f"unigrams-{code}.txt"
        if not path.exists():
            return {}
        
        counts: Dict[str, int] = {}
        try:
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    char, count = line.split()
                    counts[char] = int(count)
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Error reading frequency data for {code}: {e}")
        
        return counts

    def get_opensubtitles_frequency(self, code: str, letters: List[str]) -> Optional[Dict[str, float]]:
        """Get frequency data from OpenSubtitles dataset."""
        try:
            lang = langcodes.Language.get(code)
        except langcodes.LanguageTagError:
            subdomain = code
        else:
            subdomain = lang.language or code
            if len(subdomain) == 3 and len(code) < 3:
                subdomain = code

        url = f"https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/{subdomain}/{subdomain}_50k.txt"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        
        try:
            with urllib.request.urlopen(req) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            if exc.code == 404:
                logger.debug(f"No OpenSubtitles data for {code}")
            else:
                logger.warning(f"Failed to fetch OpenSubtitles data for {code}: HTTP {exc.code}")
            return None

        # Process frequency data
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
            
            # Handle case sensitivity
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

    def parse_exemplars(self, text: str) -> List[str]:
        """Extract single-letter tokens from CLDR exemplar string."""
        letters: List[str] = []
        for token in text.strip("[]").split():
            if token.startswith("{") and token.endswith("}"):
                token = token[1:-1]
            for ch in token:
                ch = unicodedata.normalize("NFC", ch)
                if unicodedata.category(ch).startswith("L"):
                    letters.append(ch)
        return letters

    def parse_numbers(self, text: str) -> List[str]:
        """Extract digit tokens from CLDR numbers string."""
        digits = []
        digit_map = {}  # Map ASCII digit to local digit

        for token in text.strip("[]").split():
            if token.startswith("{") and token.endswith("}"):
                token = token[1:-1]

            # Skip Unicode escape sequences like \u061C\u200E
            if "\\" in token and "u" in token:
                continue

            # Look for digit characters in the token
            token_digits = [ch for ch in token if unicodedata.category(ch) == "Nd"]

            if len(token_digits) == 2:
                # Digit pair like "0٠" or "1١"
                ascii_digit = None
                local_digit = None

                for ch in token_digits:
                    if ord(ch) <= 127:  # ASCII digit
                        ascii_digit = ch
                    else:  # Local digit
                        local_digit = ch

                # Map ASCII to local digit
                if ascii_digit and local_digit:
                    digit_map[ascii_digit] = local_digit

            elif len(token_digits) == 1:
                # Single digit
                ch = token_digits[0]
                if ord(ch) <= 127:
                    digit_map[ch] = ch
                else:
                    # Find which position this local digit represents
                    # For now, assume it's in order 0-9
                    pos = str(len(digit_map))
                    if pos not in digit_map:
                        digit_map[pos] = ch

        # Build ordered list of digits (0-9)
        for i in range(10):
            key = str(i)
            if key in digit_map:
                digits.append(digit_map[key])

        return digits

    def sort_letters(self, letters: List[str], locale: str) -> List[str]:
        """Sort letters with locale-aware rules if available."""
        if Collator and locale:
            try:
                collator = Collator.createInstance(Locale(locale))
                return sorted(letters, key=collator.getSortKey)
            except Exception:
                pass
        return sorted(letters)

    def get_fallback_alphabet(self, language: str, script: str) -> Optional[List[str]]:
        """Get fallback alphabet data for languages missing from CLDR."""
        if language in FALLBACK_ALPHABETS and script in FALLBACK_ALPHABETS[language]:
            alphabet_str = FALLBACK_ALPHABETS[language][script]
            return list(alphabet_str)
        return None

    def build_alphabet(self, language: str, script: str) -> Optional[Dict]:
        """Build alphabet data for a language-script combination."""
        self.stats["total_processed"] += 1
        locale = f"{language}-{script}"
        
        logger.info(f"Processing {locale}")
        
        # Try CLDR first
        url = f"{CLDR_BASE}/cldr-misc-full/main/{locale}/characters.json"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code == 404:
            # Try without script
            try:
                default_script = langcodes.get(language).maximize().script
                if script != default_script:
                    logger.debug(f"No CLDR data for {locale}, trying fallback")
                    fallback_letters = self.get_fallback_alphabet(language, script)
                    if fallback_letters:
                        self.stats["fallback_used"] += 1
                        return self._build_from_letters(language, script, fallback_letters, None, [])
                    self.stats["cldr_missing"] += 1
                    return None
                
                locale = language
                url = f"{CLDR_BASE}/cldr-misc-full/main/{locale}/characters.json"
                resp = requests.get(url, timeout=30)
            except Exception as e:
                logger.warning(f"Error getting default script for {language}: {e}")
        
        if resp.status_code == 404:
            logger.debug(f"No CLDR data for {locale}")
            fallback_letters = self.get_fallback_alphabet(language, script)
            if fallback_letters:
                self.stats["fallback_used"] += 1
                return self._build_from_letters(language, script, fallback_letters, None, [])
            self.stats["cldr_missing"] += 1
            return None
        
        try:
            resp.raise_for_status()
            data = resp.json()["main"][locale]["characters"]
            exemplar = data["exemplarCharacters"]
            letters = set(self.parse_exemplars(exemplar))

            if not letters:
                logger.warning(f"No exemplar data for {locale}")
                return None

            # Extract digits if available
            digits = []
            if "numbers" in data:
                digits = self.parse_numbers(data["numbers"])

            return self._build_from_letters(language, script, list(letters), data, digits)
            
        except Exception as e:
            logger.error(f"Error processing {locale}: {e}")
            self.stats["errors"].append(f"{locale}: {e}")
            return None

    def _build_from_letters(self, language: str, script: str, letters: List[str], cldr_data: Optional[Dict] = None, digits: Optional[List[str]] = None) -> Dict:
        """Build alphabet data from a list of letters."""
        locale = f"{language}-{script}"
        
        # Handle case
        has_case = any(ch.lower() != ch.upper() for ch in letters)
        if has_case:
            lower = {unicodedata.normalize("NFC", ch.lower()) for ch in letters}
            upper_map = {ch: unicodedata.normalize("NFC", ch.upper()) for ch in lower}
        else:
            lower = set(letters)
            upper_map = {ch: ch for ch in lower}

        # Sort letters
        if cldr_data and cldr_data.get("index"):
            order = {ch: i for i, ch in enumerate(self.parse_exemplars(cldr_data["index"]))}
            lower_sorted = sorted(lower, key=lambda ch: (order.get(ch.upper(), len(order)), ch))
        else:
            lower_sorted = self.sort_letters(list(lower), locale)

        upper_sorted = [upper_map[ch] for ch in lower_sorted]
        alphabetical = upper_sorted

        # Get frequency data
        self.download_unigrams()
        counts = self.load_frequency_data(language)
        total = sum(counts.get(ch, 0) for ch in lower_sorted)
        
        if total:
            freq = {ch: round(counts.get(ch, 0) / total, 4) for ch in lower_sorted}
        else:
            osfreq = self.get_opensubtitles_frequency(language, lower_sorted)
            if osfreq is not None:
                freq = osfreq
            else:
                freq = {ch: 0.0 for ch in lower_sorted}
                self.stats["frequency_missing"] += 1

        # Process digits if available
        digits_data = None
        if digits:
            logger.debug(f"Raw digits for {language}-{script}: {digits}")

            # The digits should already be unique and in order from parse_numbers
            digits_unique = digits

            logger.debug(f"Final digits for {language}-{script}: {digits_unique}")

            digits_data = digits_unique

        # Build result
        try:
            lang = langcodes.get(language)
            result = {
                "language": lang.language_name(),
                "iso639_3": lang.to_alpha3(),
                "alphabetical": alphabetical,
                "uppercase": upper_sorted,
                "lowercase": lower_sorted,
                "frequency": freq,
                "script": script,
            }

            # Add digits if available
            if digits_data:
                result["digits"] = digits_data

            alpha2 = lang.language
            if alpha2 and len(alpha2) == 2:
                result["iso639_1"] = alpha2
                
        except Exception as e:
            logger.warning(f"Error getting language info for {language}: {e}")
            result = {
                "language": language,
                "alphabetical": alphabetical,
                "uppercase": upper_sorted,
                "lowercase": lower_sorted,
                "frequency": freq,
                "script": script,
            }

            # Add digits if available
            if digits_data:
                result["digits"] = digits_data

        self.stats["successful"] += 1
        return result

    def save_alphabet(self, language: str, script: str, data: Dict) -> None:
        """Save alphabet data to JSON file."""
        out_path = Path("data/alphabets") / f"{language}-{script}.json"
        
        # Preserve existing translations if they exist
        if out_path.exists():
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
                if "hello_how_are_you" in existing:
                    data["hello_how_are_you"] = existing["hello_how_are_you"]
            except Exception as e:
                logger.warning(f"Error reading existing file {out_path}: {e}")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Wrote {out_path}")

    def print_stats(self) -> None:
        """Print collection statistics."""
        print("\n" + "="*50)
        print("ALPHABET COLLECTION STATISTICS")
        print("="*50)
        print(f"Total processed: {self.stats['total_processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"CLDR missing: {self.stats['cldr_missing']}")
        print(f"Frequency missing: {self.stats['frequency_missing']}")
        print(f"Fallback used: {self.stats['fallback_used']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("language", nargs="?", help="ISO 639 code")
    parser.add_argument("script", nargs="?", help="ISO 15924 code")
    parser.add_argument("--manifest", help="JSON file mapping languages to script codes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    builder = AlphabetBuilder()
    
    if args.manifest:
        mapping = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        for lang, scripts in mapping.items():
            for script in scripts:
                try:
                    data = builder.build_alphabet(lang, script)
                    if data:
                        builder.save_alphabet(lang, script, data)
                except Exception as e:
                    logger.error(f"Failed to process {lang}-{script}: {e}")
                    builder.stats["errors"].append(f"{lang}-{script}: {e}")
    else:
        if not args.language or not args.script:
            parser.error("language and script required when not using --manifest")
        
        data = builder.build_alphabet(args.language, args.script)
        if data:
            builder.save_alphabet(args.language, args.script, data)

    builder.print_stats()

if __name__ == "__main__":
    main()
