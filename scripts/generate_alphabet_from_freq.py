#!/usr/bin/env python3
"""
Generate alphabet JSON file from word frequency data.

This script creates an alphabet file for a language using:
1. Character extraction from word frequency list
2. Character frequency calculation
3. Basic uppercase/lowercase detection

Usage:
    uv run python scripts/generate_alphabet_from_freq.py --lang ady --script Cyrl
"""

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set


def get_script_name(lang_code: str) -> str:
    """Guess script from language code or characters."""
    # Common script mappings
    cyrillic_langs = {"ady", "ab", "av", "ba", "be", "bg", "ce", "cv", "kk", "ky", "mk", "mn", "os", "ru", "sr", "tg", "tt", "uk", "uz"}
    
    if lang_code in cyrillic_langs:
        return "Cyrl"
    return "Latn"  # Default


def is_cyrillic(char: str) -> bool:
    """Check if character is Cyrillic."""
    try:
        return "CYRILLIC" in unicodedata.name(char, "")
    except (ValueError, TypeError):
        return False


def is_latin(char: str) -> bool:
    """Check if character is Latin (including extended Latin)."""
    try:
        name = unicodedata.name(char, "")
        return "LATIN" in name or char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    except (ValueError, TypeError):
        return False


def extract_characters(words: List[str], script: Optional[str] = None) -> Set[str]:
    """Extract unique characters from word list, filtered by script."""
    chars = set()
    for word in words:
        for char in word:
            if not char.isalpha():
                continue

            # Filter by script if specified
            if script == "Cyrl" and not is_cyrillic(char):
                continue
            elif script == "Latn" and not is_latin(char):
                continue

            chars.add(char)
    return chars


def calculate_char_frequencies(words: List[str], script: Optional[str] = None) -> Dict[str, float]:
    """Calculate character frequencies from word list, filtered by script."""
    char_counts: Counter[str] = Counter()
    total_chars = 0

    for word in words:
        for char in word.lower():
            if not char.isalpha():
                continue

            # Filter by script if specified
            if script == "Cyrl" and not is_cyrillic(char):
                continue
            elif script == "Latn" and not is_latin(char):
                continue

            char_counts[char] += 1
            total_chars += 1

    if total_chars == 0:
        return {}

    # Convert to frequencies
    frequencies = {}
    for char, count in char_counts.items():
        frequencies[char] = round(count / total_chars, 4)

    return frequencies


def sort_alphabetically(chars: List[str], script: str) -> List[str]:
    """Sort characters alphabetically based on script."""
    # For Cyrillic, use Unicode order (which is correct for Cyrillic)
    # For Latin, use standard alphabetical order
    return sorted(chars)


def separate_case(chars: Set[str]) -> tuple[List[str], List[str]]:
    """Separate uppercase and lowercase characters, generating missing cases."""
    uppercase = []
    lowercase = []

    # Collect existing cases
    for c in chars:
        if c.isupper():
            uppercase.append(c)
        elif c.islower():
            lowercase.append(c)

    # Generate missing uppercase from lowercase
    lowercase_set = set(lowercase)
    for c in lowercase_set:
        upper = c.upper()
        if upper != c and upper not in uppercase:
            uppercase.append(upper)

    # Generate missing lowercase from uppercase
    uppercase_set = set(uppercase)
    for c in uppercase_set:
        lower = c.lower()
        if lower != c and lower not in lowercase_set:
            lowercase.append(lower)

    return sorted(uppercase), sorted(lowercase)


def get_language_name(lang_code: str) -> str:
    """Get language name from code."""
    try:
        import langcodes
        return langcodes.Language.get(lang_code).display_name()
    except (ImportError, AttributeError, LookupError):
        # Fallback names
        names = {
            "ady": "Adyghe",
            "ab": "Abkhazian",
            "av": "Avaric",
        }
        return names.get(lang_code, lang_code.upper())


def generate_alphabet_file(lang_code: str, script: Optional[str] = None) -> bool:
    """Generate alphabet JSON file from word frequency data."""
    
    # Paths
    freq_file = Path(f"data/freq/top1000/{lang_code}.txt")
    if not freq_file.exists():
        print(f"❌ Frequency file not found: {freq_file}")
        return False
    
    # Read words
    words = freq_file.read_text(encoding="utf-8").strip().split("\n")
    print(f"📖 Read {len(words)} words from {freq_file}")
    
    # Determine script
    if not script:
        script = get_script_name(lang_code)
    print(f"📝 Script: {script}")
    
    # Extract characters (with script filtering)
    chars = extract_characters(words, script)
    print(f"🔤 Found {len(chars)} unique characters")

    # Separate case (generates missing uppercase/lowercase)
    uppercase, lowercase = separate_case(chars)
    
    # Get all unique letters (both cases)
    all_letters = sorted(set(c.lower() for c in chars))

    # Calculate frequencies (with script filtering)
    frequencies = calculate_char_frequencies(words, script)
    
    # Get language name
    language_name = get_language_name(lang_code)
    
    # Build alphabet data
    alphabet_data = {
        "language": language_name,
        "iso639_3": lang_code,  # Note: might not be exact ISO 639-3
        "alphabetical": all_letters,
        "uppercase": uppercase,
        "lowercase": lowercase,
        "frequency": frequencies,
        "script": script,
        "digits": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "iso639_1": lang_code if len(lang_code) == 2 else None,
    }
    
    # Output file
    output_file = Path(f"data/alphabets/{lang_code}-{script}.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(alphabet_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated: {output_file}")
    print(f"   Language: {language_name}")
    print(f"   Script: {script}")
    print(f"   Characters: {len(all_letters)}")
    print(f"   Sample: {' '.join(all_letters[:10])}")
    
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate alphabet JSON from word frequency data")
    parser.add_argument("--lang", required=True, help="Language code (e.g., ady)")
    parser.add_argument("--script", help="Script code (e.g., Cyrl, Latn). Auto-detected if not provided")
    
    args = parser.parse_args()
    
    success = generate_alphabet_file(args.lang, args.script)
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

