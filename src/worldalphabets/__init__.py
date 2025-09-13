"""Utilities for loading world alphabets."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Dict, List, Optional

from .helpers import get_index_data, get_language, get_scripts
from .keyboards import get_available_layouts, load_keyboard
from .models.keyboard import KeyboardLayout, KeyEntry, LayerLegends, DeadKey, Ligature
from .diacritics import (
    strip_diacritics,
    has_diacritics,
    characters_with_diacritics,
    diacritic_variants,
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


def get_diacritic_variants(code: str, script: str | None = None) -> Dict[str, List[str]]:
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


def detect_languages(text: str) -> List[str]:
    """Return language codes whose alphabets cover characters in ``text``."""

    letters = {strip_diacritics(ch).lower() for ch in text if ch.isalpha()}
    if not letters:
        return []

    candidates: List[str] = []
    for entry in get_index_data():
        lang = entry["language"]
        script = entry.get("script")
        data = get_language(lang, script=script)
        if data is None:
            continue
        alphabet = {
            strip_diacritics(ch).lower()
            for ch in data.get("lowercase", [])
        }
        if letters <= alphabet:
            candidates.append(lang)
    return candidates


__all__ = [
    # Alphabets
    "load_alphabet",
    "Alphabet",
    "get_available_codes",
    "get_index_data",
    "get_language",
    "get_scripts",
    # Diacritics
    "strip_diacritics",
    "has_diacritics",
    "characters_with_diacritics",
    "get_diacritic_variants",
    # Language detection
    "detect_languages",
    # Keyboards
    "load_keyboard",
    "get_available_layouts",
    "KeyboardLayout",
    "KeyEntry",
    "LayerLegends",
    "DeadKey",
    "Ligature",
]
