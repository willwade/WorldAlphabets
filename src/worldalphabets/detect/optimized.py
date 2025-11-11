"""
Optimized language detection with performance enhancements.
Incorporates all optimizations from the webUI and Node.js implementations.
"""

import json
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any
from functools import lru_cache
import time

from . import (
    PRIOR_WEIGHT,
    FREQ_WEIGHT,
    CHAR_WEIGHT,
    DEFAULT_FREQ_DIR,
    _tokenize_words,
    _tokenize_bigrams,
    _tokenize_characters,
    _load_rank_data,
    _overlap,
    _character_overlap,
    _frequency_overlap,
)
from ..helpers import get_language

# Performance constants
HIGH_CONFIDENCE_THRESHOLD = 0.8
COMMON_LANGUAGES = [
    "en",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "ru",
    "zh",
    "ja",
    "ar",
    "hi",
    "ko",
]

# Global caches
_alphabet_cache: Dict[str, Optional[Dict]] = {}
_char_index: Optional[Dict] = None
_script_index: Optional[Dict] = None


class ProgressCallback:
    """Progress callback interface for detection progress."""

    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
        self.start_time = time.time()

    def update(self, status: str, processed: int, total: int) -> None:
        """Update progress with current status."""
        if self.callback:
            percentage = (processed / total * 100) if total > 0 else 0
            elapsed = time.time() - self.start_time

            self.callback(
                {
                    "status": status,
                    "percentage": percentage,
                    "processed": processed,
                    "total": total,
                    "elapsed_time": elapsed,
                }
            )


@lru_cache(maxsize=1)
def _load_char_index() -> Optional[Dict]:
    """Load character index for candidate filtering."""
    global _char_index
    if _char_index is not None:
        return _char_index

    try:
        char_index_path = (
            Path(__file__).parent.parent.parent.parent / "data" / "char_index.json"
        )
        if char_index_path.exists():
            with open(char_index_path, "r", encoding="utf-8") as f:
                _char_index = json.load(f)
                return _char_index
    except Exception:
        pass

    _char_index = None
    return None


@lru_cache(maxsize=1)
def _load_script_index() -> Optional[Dict]:
    """Load script index for filtering."""
    global _script_index
    if _script_index is not None:
        return _script_index

    try:
        script_index_path = (
            Path(__file__).parent.parent.parent.parent / "data" / "script_index.json"
        )
        if script_index_path.exists():
            with open(script_index_path, "r", encoding="utf-8") as f:
                _script_index = json.load(f)
                return _script_index
    except Exception:
        pass

    _script_index = None
    return None


def _get_cached_alphabet_data(lang_code: str) -> Optional[Dict]:
    """Get alphabet data with caching."""
    if lang_code in _alphabet_cache:
        return _alphabet_cache[lang_code]

    try:
        data = get_language(lang_code)
        _alphabet_cache[lang_code] = data
        return data
    except Exception:
        _alphabet_cache[lang_code] = None
        return None


def get_candidate_languages_from_text(text: str, all_languages: List[str]) -> List[str]:
    """Get candidate languages based on character analysis."""
    char_index = _load_char_index()
    if not char_index:
        return all_languages  # Fallback to all languages

    text_chars = _tokenize_characters(text)
    candidate_languages = set()

    # Find languages that contain the characters in the text
    for char in text_chars:
        languages = char_index.get("char_to_languages", {}).get(char, [])
        candidate_languages.update(languages)

    # If no candidates found, fall back to all languages
    if not candidate_languages:
        return all_languages

    # Convert to list and prioritize common languages
    candidates = list(candidate_languages)
    prioritized = [lang for lang in candidates if lang in COMMON_LANGUAGES] + [
        lang for lang in candidates if lang not in COMMON_LANGUAGES
    ]

    return prioritized


def optimized_detect_languages(
    text: str,
    candidate_langs: Optional[List[str]] = None,
    priors: Optional[Dict[str, float]] = None,
    topk: int = 3,
    use_character_fallback: bool = True,
    enable_early_termination: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Tuple[str, float]]:
    """
    Optimized language detection with all performance enhancements.

    Args:
        text: Input text to analyze
        candidate_langs: List of candidate languages (if None, uses character-based
            filtering)
        priors: Prior probabilities for languages
        topk: Number of top results to return
        use_character_fallback: Whether to use character-based detection for fallback
        enable_early_termination: Whether to stop early for high confidence matches
        progress_callback: Optional callback for progress updates

    Returns:
        List of (language_code, confidence_score) tuples
    """
    priors = priors or {}
    env_dir = os.environ.get("WORLDALPHABETS_FREQ_DIR")
    freq_dir = Path(env_dir) if env_dir else Path(str(DEFAULT_FREQ_DIR))

    # Initialize progress tracking
    progress = ProgressCallback(progress_callback)

    # Get all available languages if needed
    if candidate_langs is None:
        try:
            from ..helpers import get_index_data

            index_data = get_index_data()
            all_languages = list(set(item["language"] for item in index_data))
            candidate_langs = get_candidate_languages_from_text(text, all_languages)
            progress.update(
                "Filtered candidates using character analysis", 0, len(candidate_langs)
            )
        except Exception:
            # Fallback to common languages if index loading fails
            candidate_langs = COMMON_LANGUAGES

    # Prioritize common languages
    prioritized_langs = [
        lang for lang in candidate_langs if lang in COMMON_LANGUAGES
    ] + [lang for lang in candidate_langs if lang not in COMMON_LANGUAGES]

    progress.update("Starting language detection", 0, len(prioritized_langs))

    word_tokens = _tokenize_words(text)
    bigram_tokens = _tokenize_bigrams(text)
    text_chars = _tokenize_characters(text)

    results: List[Tuple[str, float]] = []
    word_based_langs = set()
    found_high_confidence = False

    for i, lang in enumerate(prioritized_langs):
        if found_high_confidence and enable_early_termination:
            progress.update(
                "Early termination - high confidence match found",
                len(prioritized_langs),
                len(prioritized_langs),
            )
            break

        progress.update(f"Processing {lang}", i, len(prioritized_langs))

        try:
            # Try word-based detection first
            data = _load_rank_data(lang, freq_dir)
            tokens = word_tokens if data.mode == "word" else bigram_tokens
            word_overlap = 0.0

            if data.ranks and tokens:
                word_overlap = _overlap(tokens, data.ranks)
                word_overlap /= math.sqrt(len(tokens) + 3)

            # Calculate word-based score
            word_score = (
                PRIOR_WEIGHT * priors.get(lang, 0.0) + FREQ_WEIGHT * word_overlap
            )

            # If word-based detection succeeds, use it
            if word_score > 0.05:
                results.append((lang, word_score))
                word_based_langs.add(lang)

                # Check for early termination
                if enable_early_termination and word_score > HIGH_CONFIDENCE_THRESHOLD:
                    found_high_confidence = True
                    progress.update(
                        f"High confidence match found: {lang}",
                        i + 1,
                        len(prioritized_langs),
                    )

                continue

            # Fallback to character-based detection
            if use_character_fallback and text_chars:
                alphabet_data = _get_cached_alphabet_data(lang)
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

                    # Apply character-based weight (reduced to prevent false positives)
                    final_char_score = (
                        PRIOR_WEIGHT * priors.get(lang, 0.0)
                        + CHAR_WEIGHT * char_score * 0.5
                    )

                    # Use a higher threshold for character-based detection to prevent false positives
                    if final_char_score > 0.04:
                        results.append((lang, final_char_score))

        except Exception:
            # Skip languages that fail to load
            continue

    progress.update(
        "Finalizing results", len(prioritized_langs), len(prioritized_langs)
    )

    # Sort results, prioritizing word-based detections
    def sort_key(item: Tuple[str, float]) -> float:
        lang, score = item
        if lang in word_based_langs:
            return score + 0.15  # Larger boost for word-based detection
        return score

    results.sort(key=sort_key, reverse=True)
    return results[:topk]


def detect_languages_with_progress(
    text: str,
    candidate_langs: Optional[List[str]] = None,
    priors: Optional[Dict[str, float]] = None,
    topk: int = 3,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Tuple[str, float]]:
    """
    Convenience function for detection with progress callback.
    Uses all optimizations by default.
    """
    return optimized_detect_languages(
        text=text,
        candidate_langs=candidate_langs,
        priors=priors,
        topk=topk,
        use_character_fallback=True,
        enable_early_termination=True,
        progress_callback=progress_callback,
    )
