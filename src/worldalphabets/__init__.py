"""Utilities for loading world alphabets."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Dict, List, Optional, Literal

from .helpers import get_index_data, get_language, get_scripts
from .keyboards import (
    DEFAULT_LAYERS,
    extract_layers,
    get_available_layouts,
    generate_c_header,
    find_layouts_by_keycode,
    load_keyboard,
)
from .models.keyboard import KeyboardLayout, KeyEntry, LayerLegends, DeadKey, Ligature
from .diacritics import (
    strip_diacritics,
    has_diacritics,
    characters_with_diacritics,
    diacritic_variants,
)
from .detect import detect_languages
from .detect.optimized import optimized_detect_languages, detect_languages_with_progress
from .inflect import (
    LookupResult,
    LocaleSummary,
    apply_rules,
    get_available_locales as _get_inflection_locales,
    get_summary as get_inflection_summary,
    get_word_forms as _get_word_forms,
    inflect_word as _inflect_word,
    load_data as _load_inflection_data,
    load_rules as _load_inflection_rules,
    load_words as _load_inflection_words,
    lookup_word,
    clear_cache as clear_inflection_cache,
)

ALPHABET_DIR = files("worldalphabets") / "data" / "alphabets"


@dataclass
class Alphabet:
    """Alphabet data for a language."""

    alphabetical: List[str]
    uppercase: List[str]
    lowercase: List[str]
    frequency: Dict[str, float]
    digits: Optional[List[str]] = None


@dataclass
class FrequencyList:
    """Top-1000 token list for language detection."""

    language: str
    tokens: List[str]
    mode: Literal["word", "bigram"] = "word"


def load_alphabet(code: str, script: str | None = None) -> Alphabet:
    """Return alphabet information for ISO language ``code`` and ``script``."""

    data = get_language(code, script=script)
    if data is None:
        raise FileNotFoundError(f"Alphabet data for code '{code}' not found")
    return Alphabet(
        alphabetical=data.get("alphabetical", []),
        uppercase=data.get("uppercase", []),
        lowercase=data.get("lowercase", []),
        frequency=data.get("frequency", {}),
        digits=data.get("digits"),
    )


def get_available_codes() -> List[str]:
    """Return sorted language codes with available alphabets."""
    return sorted(item["language"] for item in get_index_data())


def load_frequency_list(code: str) -> FrequencyList:
    """Return Top-1000 token list for ISO language ``code``."""

    freq_dir = files("worldalphabets") / "data" / "freq" / "top1000"
    path = freq_dir / f"{code}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Frequency list for code '{code}' not found")

    mode: Literal["word", "bigram"] = "word"
    tokens: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not tokens and stripped.startswith("#"):
            if "bigram" in stripped.lower():
                mode = "bigram"
            continue
        tokens.append(stripped)

    return FrequencyList(language=code, tokens=tokens, mode=mode)


def get_available_inflection_locales() -> List[str]:
    """Return sorted locales with available inflection datasets."""
    return _get_inflection_locales()


def load_inflection_words(locale: str) -> Dict[str, Any]:
    """Return word-form data for ``locale``."""
    return _load_inflection_words(locale)


def load_inflection_rules(locale: str) -> Dict[str, Any]:
    """Return inflection rule data for ``locale``."""
    return _load_inflection_rules(locale)


def load_inflection_data(locale: str) -> Dict[str, Dict[str, Any]]:
    """Return both word-form and rule data for ``locale``."""
    return _load_inflection_data(locale)


def get_word_forms(locale: str, word: str) -> Optional[Dict[str, Any]]:
    """Return the word-form entry for ``word`` in ``locale`` if present."""
    return _get_word_forms(locale, word)


def inflect_word(locale: str, word: str, inflection: str) -> Optional[str]:
    """Return an explicit inflected form for ``word`` if one is available."""
    return _inflect_word(locale, word, inflection)


def get_diacritic_variants(
    code: str, script: str | None = None
) -> Dict[str, List[str]]:
    """Return mapping of base letters to diacritic variants for ``code``."""

    data = get_language(code, script=script)
    if data is None and script is None:
        entry = next(
            (item for item in get_index_data() if item["language"] == code),
            None,
        )
        if entry:
            data = get_language(code, script=entry.get("script"))
    if data is None:
        raise FileNotFoundError(f"Alphabet data for code '{code}' not found")

    result = diacritic_variants(data.get("uppercase", []))
    result.update(diacritic_variants(data.get("lowercase", [])))
    return result


__all__ = [
    # Alphabets
    "load_alphabet",
    "Alphabet",
    "get_available_codes",
    "load_frequency_list",
    "FrequencyList",
    "get_index_data",
    "get_language",
    "get_scripts",
    # Inflections
    "get_available_inflection_locales",
    "load_inflection_words",
    "load_inflection_rules",
    "load_inflection_data",
    "get_word_forms",
    "inflect_word",
    "get_inflection_summary",
    "lookup_word",
    "apply_rules",
    "clear_inflection_cache",
    "LookupResult",
    "LocaleSummary",
    # Diacritics
    "strip_diacritics",
    "has_diacritics",
    "characters_with_diacritics",
    "get_diacritic_variants",
    # Language detection
    "detect_languages",
    "optimized_detect_languages",
    "detect_languages_with_progress",
    "PRIOR_WEIGHT",
    "FREQ_WEIGHT",
    # Keyboards
    "load_keyboard",
    "get_available_layouts",
    "DEFAULT_LAYERS",
    "extract_layers",
    "generate_c_header",
    "find_layouts_by_keycode",
    "KeyboardLayout",
    "KeyEntry",
    "LayerLegends",
    "DeadKey",
    "Ligature",
]
