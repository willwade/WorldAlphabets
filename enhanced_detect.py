#!/usr/bin/env python3
"""
Enhanced language detection with character-based fallback.
"""

import os
import sys
import math
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets.detect import (
    _tokenize_words,
    _load_rank_data,
    _overlap,
    DEFAULT_FREQ_DIR,
    PRIOR_WEIGHT,
    FREQ_WEIGHT,
)
from worldalphabets import get_language


def _tokenize_characters(text: str) -> Set[str]:
    """Extract unique characters from text, normalized and lowercased."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    return set(ch for ch in normalized if ch.isalpha())


def _character_overlap(text_chars: Set[str], alphabet_chars: Set[str]) -> float:
    """Calculate overlap score between text characters and alphabet characters."""
    if not text_chars or not alphabet_chars:
        return 0.0

    # Characters that are in the text and in the alphabet
    matching_chars = text_chars.intersection(alphabet_chars)
    # Characters that are in the text but NOT in the alphabet
    non_matching_chars = text_chars - alphabet_chars

    if not matching_chars:
        return 0.0

    # Base score: how well the alphabet covers the text
    coverage = len(matching_chars) / len(text_chars)

    # Penalty for characters that don't belong to this alphabet
    penalty = len(non_matching_chars) / len(text_chars)

    # Bonus for using distinctive characters (less common across alphabets)
    # This helps distinguish between similar scripts like different Cyrillic variants
    alphabet_coverage = (
        len(matching_chars) / len(alphabet_chars) if alphabet_chars else 0
    )

    # Combine: high coverage, low penalty, bonus for distinctive usage
    score = coverage * 0.6 - penalty * 0.2 + alphabet_coverage * 0.2

    return max(0.0, score)  # Ensure non-negative


def _frequency_overlap(
    text_chars: Set[str], char_frequencies: Dict[str, float]
) -> float:
    """Calculate weighted overlap using character frequencies."""
    if not text_chars or not char_frequencies:
        return 0.0

    score = 0.0
    total_freq = 0.0

    for char in text_chars:
        freq = char_frequencies.get(char, 0.0)
        if freq > 0:
            # Weight by frequency (more common chars get higher scores)
            score += freq
            total_freq += freq

    # Normalize by the total frequency of matched characters
    return score / max(total_freq, 0.001) if total_freq > 0 else 0.0


def enhanced_detect_languages(
    text: str,
    candidate_langs: List[str],
    priors: Dict[str, float] | None = None,
    topk: int = 3,
    use_character_fallback: bool = True,
) -> List[Tuple[str, float]]:
    """Enhanced language detection with character-based fallback."""

    priors = priors or {}
    env_dir = os.environ.get("WORLDALPHABETS_FREQ_DIR")
    freq_dir = Path(env_dir) if env_dir else Path(str(DEFAULT_FREQ_DIR))

    word_tokens = _tokenize_words(text)
    text_chars = _tokenize_characters(text)

    results: List[Tuple[str, float]] = []
    word_based_langs = set()  # Track which languages used word-based detection

    for lang in candidate_langs:
        # Try word-based detection first
        data = _load_rank_data(lang, freq_dir)
        word_overlap = 0.0

        if data.ranks and word_tokens:
            word_overlap = _overlap(word_tokens, data.ranks)
            word_overlap /= math.sqrt(len(word_tokens) + 3)

        # Calculate word-based score
        word_score = PRIOR_WEIGHT * priors.get(lang, 0.0) + FREQ_WEIGHT * word_overlap

        # If word-based detection succeeds, use it and mark as word-based
        if word_score > 0.05:
            results.append((lang, word_score))
            word_based_langs.add(lang)
            continue

        # Fallback to character-based detection
        if use_character_fallback and text_chars:
            try:
                # Load alphabet data for this language
                alphabet_data = get_language(lang)
                if alphabet_data:
                    # Get character sets
                    lowercase_chars = set(alphabet_data.get("lowercase", []))
                    char_frequencies = alphabet_data.get("frequency", {})

                    # Calculate character-based scores
                    char_overlap_score = _character_overlap(text_chars, lowercase_chars)
                    freq_overlap_score = _frequency_overlap(
                        text_chars, char_frequencies
                    )

                    # Combine character overlap and frequency overlap
                    char_score = char_overlap_score * 0.6 + freq_overlap_score * 0.4

                    # Apply a lower weight for character-based detection
                    CHAR_WEIGHT = 0.2  # Lower than FREQ_WEIGHT (0.35)
                    final_char_score = (
                        PRIOR_WEIGHT * priors.get(lang, 0.0) + CHAR_WEIGHT * char_score
                    )

                    # Use a lower threshold for character-based detection
                    if final_char_score > 0.02:
                        results.append((lang, final_char_score))

            except Exception as e:
                # If alphabet loading fails, skip this language
                print(f"Warning: Could not load alphabet data for {lang}: {e}")
                continue

    # Sort results, but prioritize word-based detections over character-based ones
    # by giving word-based results a small boost
    def sort_key(item: Tuple[str, float]) -> float:
        lang, score = item
        if lang in word_based_langs:
            return score + 0.01  # Small boost for word-based detection
        return score

    results.sort(key=sort_key, reverse=True)
    return results[:topk]


def test_enhanced_detection() -> None:
    """Test the enhanced detection method."""

    test_cases = [
        # Languages without word frequency data
        ("ab", "Аҧсуа бызшәа", ["ab", "ru", "bg", "mk"]),  # Abkhazian
        ("cop", "ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ", ["cop", "el", "ar", "he"]),  # Coptic
        ("gez", "ግዕዝ", ["gez", "am", "ti", "ar"]),  # Ge'ez
        ("vai", "ꕙꔤ", ["vai", "en", "fr", "de"]),  # Vai
        # Languages with word frequency data (should still work)
        ("en", "Hello world this is a test", ["en", "es", "fr", "de"]),
        ("de", "Hallo Welt das ist ein Test", ["de", "en", "nl", "da"]),
    ]

    print("Enhanced Language Detection Test")
    print("=" * 60)

    for lang_code, sample_text, candidates in test_cases:
        print(f"\nTesting: {lang_code}")
        print(f"Text: '{sample_text}'")
        print(f"Candidates: {candidates}")

        # Test original method
        try:
            from worldalphabets.detect import detect_languages

            original_results = detect_languages(
                sample_text, candidate_langs=candidates, topk=len(candidates)
            )
            print(f"Original method: {original_results}")
        except Exception as e:
            print(f"Original method error: {e}")

        # Test enhanced method
        try:
            enhanced_results = enhanced_detect_languages(
                sample_text, candidates, topk=len(candidates)
            )
            print(f"Enhanced method: {enhanced_results}")

            # Check if target language was detected
            detected_langs = [lang for lang, score in enhanced_results]
            if lang_code in detected_langs:
                rank = detected_langs.index(lang_code) + 1
                score = enhanced_results[detected_langs.index(lang_code)][1]
                print(
                    f"✓ Target '{lang_code}' detected at rank {rank} with score {score:.4f}"
                )
            else:
                print(f"✗ Target '{lang_code}' NOT detected")

        except Exception as e:
            print(f"Enhanced method error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_detection()
