"""Utilities for loading world alphabets."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from .corpora import get_corpus, list_corpora
from .detect import detect_languages
from .detect.optimized import detect_languages_with_progress, optimized_detect_languages
from .diacritics import (
    characters_with_diacritics,
    diacritic_variants,
    has_diacritics,
    strip_diacritics,
)
from .helpers import get_index_data, get_language, get_scripts
from .keyboards import (
    DEFAULT_LAYERS,
    char_to_hid,
    extract_layers,
    find_layouts_by_keycode,
    generate_c_header,
    get_available_layouts,
    load_keyboard,
)
from .models.keyboard import DeadKey, KeyboardLayout, KeyEntry, LayerLegends, Ligature

ALPHABET_DIR = files("worldalphabets") / "data" / "alphabets"


@dataclass
class Alphabet:
    """Alphabet data for a language."""

    alphabetical: list[str]
    uppercase: list[str]
    lowercase: list[str]
    frequency: dict[str, float]
    digits: list[str] | None = None


@dataclass
class FrequencyList:
    """Top-1000 token list for language detection."""

    language: str
    tokens: list[str]
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


def get_available_codes() -> list[str]:
    """Return sorted language codes with available alphabets."""
    return sorted(item["language"] for item in get_index_data())


def load_frequency_list(code: str) -> FrequencyList:
    """Return Top-1000 token list for ISO language ``code``."""

    freq_dir = files("worldalphabets") / "data" / "freq" / "top1000"
    path = freq_dir / f"{code}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Frequency list for code '{code}' not found")

    mode: Literal["word", "bigram"] = "word"
    tokens: list[str] = []
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


def get_diacritic_variants(
    code: str, script: str | None = None
) -> dict[str, list[str]]:
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
    "DEFAULT_LAYERS",
    "FREQ_WEIGHT",
    "PRIOR_WEIGHT",
    "Alphabet",
    "DeadKey",
    "FrequencyList",
    "KeyEntry",
    "KeyboardLayout",
    "LayerLegends",
    "Ligature",
    "char_to_hid",
    "characters_with_diacritics",
    # Language detection
    "detect_languages",
    "detect_languages_with_progress",
    "extract_layers",
    "find_layouts_by_keycode",
    "generate_c_header",
    "get_available_codes",
    "get_available_layouts",
    # Text corpora (manifest always shipped; text optional — see worldalphabets.corpora)
    "get_corpus",
    "get_diacritic_variants",
    "get_index_data",
    "get_language",
    "get_scripts",
    "has_diacritics",
    "list_corpora",
    # Alphabets
    "load_alphabet",
    "load_frequency_list",
    # Keyboards
    "load_keyboard",
    "optimized_detect_languages",
    # Diacritics
    "strip_diacritics",
]
