"""Language detection using script priors and Top-200 token overlap."""

from __future__ import annotations

import math
import os
import unicodedata
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

__all__ = ["detect_languages", "PRIOR_WEIGHT", "FREQ_WEIGHT"]

DEFAULT_FREQ_DIR = files("worldalphabets") / "data" / "freq" / "top1000"
PRIOR_WEIGHT = float(os.environ.get("WA_FREQ_PRIOR_WEIGHT", 0.65))
FREQ_WEIGHT = float(os.environ.get("WA_FREQ_OVERLAP_WEIGHT", 0.35))
CHAR_WEIGHT = 0.2  # Weight for character-based detection fallback


def _tokenize_words(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return set(
        __import__("re").findall(
            r"[^\W\d_]+", normalized, flags=__import__("re").UNICODE
        )
    )


def _tokenize_bigrams(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    letters = [ch for ch in normalized if ch.isalpha()]
    return {"".join(letters[i : i + 2]) for i in range(len(letters) - 1)}


def _tokenize_characters(text: str) -> set[str]:
    """Extract unique characters from text, normalized and lowercased."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    return set(ch for ch in normalized if ch.isalpha())


def _character_overlap(text_chars: set[str], alphabet_chars: set[str]) -> float:
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
    alphabet_coverage = (
        len(matching_chars) / len(alphabet_chars) if alphabet_chars else 0
    )

    # Combine: high coverage, low penalty, bonus for distinctive usage
    score = coverage * 0.6 - penalty * 0.2 + alphabet_coverage * 0.2

    return max(0.0, score)  # Ensure non-negative


def _frequency_overlap(
    text_chars: set[str], char_frequencies: Dict[str, float]
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


@dataclass
class RankData:
    mode: str
    ranks: Dict[str, int]


def _load_rank_data(lang: str, freq_dir: Path) -> RankData:
    path = freq_dir / f"{lang}.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return RankData("word", {})
    mode = "word"
    if lines and lines[0].startswith("#"):
        header = lines.pop(0)
        if "bigram" in header:
            mode = "bigram"
    ranks: Dict[str, int] = {}
    for idx, token in enumerate(lines, start=1):
        if token and token not in ranks:
            ranks[token] = idx
    return RankData(mode, ranks)


def _overlap(tokens: Iterable[str], ranks: Dict[str, int]) -> float:
    score = 0.0
    for token in tokens:
        rank = ranks.get(token)
        if rank:
            score += 1 / math.log2(rank + 1.5)
    if score == 0:
        return 0.0
    return score


def detect_languages(
    text: str,
    *,
    candidate_langs: List[str],
    priors: Dict[str, float] | None = None,
    topk: int = 3,
) -> List[Tuple[str, float]]:
    """Return top language guesses for ``text``.

    Combines provided ``priors`` with token overlap from Top-200 lists.
    Falls back to character-based detection when word frequency data is unavailable.
    """

    priors = priors or {}
    env_dir = os.environ.get("WORLDALPHABETS_FREQ_DIR")
    freq_dir = Path(env_dir) if env_dir else Path(str(DEFAULT_FREQ_DIR))

    word_tokens = _tokenize_words(text)
    bigram_tokens = _tokenize_bigrams(text)
    text_chars = _tokenize_characters(text)

    results: List[Tuple[str, float]] = []
    word_based_langs = set()  # Track which languages used word-based detection

    for lang in candidate_langs:
        # Try word-based detection first
        data = _load_rank_data(lang, freq_dir)
        tokens = word_tokens if data.mode == "word" else bigram_tokens
        word_overlap = 0.0
        if data.ranks and tokens:
            word_overlap = _overlap(tokens, data.ranks)
            word_overlap /= math.sqrt(len(tokens) + 3)

        # Calculate word-based score
        word_score = PRIOR_WEIGHT * priors.get(lang, 0.0) + FREQ_WEIGHT * word_overlap

        # If word-based detection succeeds, use it and mark as word-based
        if word_score > 0.05:
            results.append((lang, word_score))
            word_based_langs.add(lang)
            continue

        # Fallback to character-based detection
        if text_chars:
            try:
                from ..helpers import get_language

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

                    # Apply character-based weight (reduced to prevent false positives)
                    final_char_score = (
                        PRIOR_WEIGHT * priors.get(lang, 0.0)
                        + CHAR_WEIGHT * char_score * 0.5
                    )

                    # Use a higher threshold for character-based detection to prevent false positives
                    if final_char_score > 0.04:
                        results.append((lang, final_char_score))

            except Exception:
                # If alphabet loading fails, skip this language
                continue

    # Sort results, but prioritize word-based detections over character-based ones
    def sort_key(item: Tuple[str, float]) -> float:
        lang, score = item
        if lang in word_based_langs:
            return score + 0.15  # Larger boost for word-based detection
        return score

    results.sort(key=sort_key, reverse=True)
    return results[:topk]
