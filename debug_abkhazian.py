#!/usr/bin/env python3
"""
Debug Abkhazian detection specifically.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets import get_language
import unicodedata


def debug_abkhazian():
    text = "Аҧсуа бызшәа"
    candidates = ["ab", "ru", "bg", "mk"]

    print(f"Text: '{text}'")
    print(
        f"Text characters: {set(ch for ch in unicodedata.normalize('NFKC', text).lower() if ch.isalpha())}"
    )
    print()

    for lang in candidates:
        print(f"=== {lang.upper()} ===")
        try:
            alphabet_data = get_language(lang)
            if alphabet_data:
                lowercase_chars = set(alphabet_data.get("lowercase", []))
                char_frequencies = alphabet_data.get("frequency", {})

                print(f"Alphabet size: {len(lowercase_chars)}")
                print(f"First 10 chars: {list(lowercase_chars)[:10]}")
                print(
                    f"Has frequency data: {any(f > 0 for f in char_frequencies.values())}"
                )

                # Check text characters
                text_chars = set(
                    ch
                    for ch in unicodedata.normalize("NFKC", text).lower()
                    if ch.isalpha()
                )
                matching = text_chars.intersection(lowercase_chars)
                non_matching = text_chars - lowercase_chars

                print(f"Text chars in alphabet: {matching}")
                print(f"Text chars NOT in alphabet: {non_matching}")
                print(
                    f"Coverage: {len(matching)}/{len(text_chars)} = {len(matching)/len(text_chars):.3f}"
                )

                # Check for distinctive characters
                distinctive_chars = []
                for char in matching:
                    # Check how many other alphabets also have this character
                    count = 0
                    for other_lang in candidates:
                        if other_lang != lang:
                            try:
                                other_data = get_language(other_lang)
                                if other_data and char in set(
                                    other_data.get("lowercase", [])
                                ):
                                    count += 1
                            except Exception:
                                pass
                    if count == 0:  # Only in this alphabet
                        distinctive_chars.append(char)

                print(f"Distinctive chars (unique to {lang}): {distinctive_chars}")
                print()

        except Exception as e:
            print(f"Error loading {lang}: {e}")
            print()


if __name__ == "__main__":
    debug_abkhazian()
