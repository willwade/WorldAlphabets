#!/usr/bin/env python3
"""
Generate character frequency index for faster language detection.
Creates a consolidated index of character frequencies across all languages.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict


def load_alphabet_data(alphabets_dir: Path) -> Dict[str, Dict]:
    """Load all alphabet data files."""
    alphabet_data = {}

    for file_path in alphabets_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract language code from filename
            filename = file_path.stem
            if "-" in filename:
                lang_code = filename.split("-")[0]
            else:
                lang_code = filename

            alphabet_data[lang_code] = data

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

    return alphabet_data


def generate_character_index(alphabet_data: Dict[str, Dict]) -> Dict:
    """Generate character frequency index for fast lookups."""

    # Character to languages mapping
    char_to_languages = defaultdict(set)

    # Language to character sets mapping
    lang_to_chars = {}

    # Language to character frequencies mapping
    lang_to_freq = {}

    for lang_code, data in alphabet_data.items():
        # Get character set
        chars = set()
        if "lowercase" in data:
            chars.update(data["lowercase"])
        if "uppercase" in data:
            chars.update(data["uppercase"])
        if "alphabet" in data:
            chars.update(data["alphabet"])

        lang_to_chars[lang_code] = list(chars)

        # Get character frequencies
        if "frequency" in data and data["frequency"]:
            lang_to_freq[lang_code] = data["frequency"]

        # Build reverse index
        for char in chars:
            char_to_languages[char].add(lang_code)

    # Convert sets to lists for JSON serialization
    char_to_languages_json = {
        char: list(languages) for char, languages in char_to_languages.items()
    }

    return {
        "char_to_languages": char_to_languages_json,
        "lang_to_chars": lang_to_chars,
        "lang_to_freq": lang_to_freq,
        "metadata": {
            "total_languages": len(lang_to_chars),
            "total_characters": len(char_to_languages_json),
            "languages_with_frequencies": len(lang_to_freq),
        },
    }


def generate_script_index(alphabet_data: Dict[str, Dict]) -> Dict:
    """Generate script-based index for faster filtering."""

    script_to_languages = defaultdict(set)
    lang_to_script = {}

    for lang_code, data in alphabet_data.items():
        # Try to determine script
        script = "Unknown"

        if "script" in data:
            script = data["script"]
        elif any(ord(c) > 127 for c in "".join(data.get("lowercase", []))):
            # Non-ASCII characters, try to guess script
            chars = "".join(data.get("lowercase", []))
            if any("\u4e00" <= c <= "\u9fff" for c in chars):
                script = "Hans"  # Chinese
            elif any("\u3040" <= c <= "\u309f" for c in chars):
                script = "Hira"  # Japanese Hiragana
            elif any("\u30a0" <= c <= "\u30ff" for c in chars):
                script = "Kana"  # Japanese Katakana
            elif any("\u0400" <= c <= "\u04ff" for c in chars):
                script = "Cyrl"  # Cyrillic
            elif any("\u0370" <= c <= "\u03ff" for c in chars):
                script = "Grek"  # Greek
            elif any("\u0590" <= c <= "\u05ff" for c in chars):
                script = "Hebr"  # Hebrew
            elif any("\u0600" <= c <= "\u06ff" for c in chars):
                script = "Arab"  # Arabic
            else:
                script = "Latn"  # Default to Latin
        else:
            script = "Latn"  # ASCII characters

        lang_to_script[lang_code] = script
        script_to_languages[script].add(lang_code)

    # Convert sets to lists
    script_to_languages_json = {
        script: list(languages) for script, languages in script_to_languages.items()
    }

    return {
        "script_to_languages": script_to_languages_json,
        "lang_to_script": lang_to_script,
        "metadata": {
            "total_scripts": len(script_to_languages_json),
            "total_languages": len(lang_to_script),
        },
    }


def main() -> None:
    """Generate character and script indexes."""

    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    alphabets_dir = data_dir / "alphabets"

    if not alphabets_dir.exists():
        print(f"Alphabets directory not found: {alphabets_dir}")
        return

    print("Loading alphabet data...")
    alphabet_data = load_alphabet_data(alphabets_dir)
    print(f"Loaded {len(alphabet_data)} alphabet files")

    print("Generating character index...")
    char_index = generate_character_index(alphabet_data)

    print("Generating script index...")
    script_index = generate_script_index(alphabet_data)

    # Save indexes
    char_index_path = data_dir / "char_index.json"
    script_index_path = data_dir / "script_index.json"

    with open(char_index_path, "w", encoding="utf-8") as f:
        json.dump(char_index, f, ensure_ascii=False, indent=2)

    with open(script_index_path, "w", encoding="utf-8") as f:
        json.dump(script_index, f, ensure_ascii=False, indent=2)

    print("\n✅ Generated indexes:")
    print(f"   Character index: {char_index_path}")
    print(f"   - {char_index['metadata']['total_characters']} unique characters")
    print(f"   - {char_index['metadata']['total_languages']} languages")
    print(
        f"   - {char_index['metadata']['languages_with_frequencies']} with frequencies"
    )

    print(f"   Script index: {script_index_path}")
    print(f"   - {script_index['metadata']['total_scripts']} scripts")
    print(f"   - {script_index['metadata']['total_languages']} languages")

    # Show some examples
    print("\n📊 Examples:")
    print(f"   Scripts: {list(script_index['script_to_languages'].keys())[:10]}")

    # Most common characters
    char_counts = {
        char: len(langs) for char, langs in char_index["char_to_languages"].items()
    }
    common_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print(
        f"   Most common chars: {[f'{char}({count})' for char, count in common_chars]}"
    )


if __name__ == "__main__":
    main()
