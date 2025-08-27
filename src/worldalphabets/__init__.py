"""Utilities for loading world alphabets."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Dict, List

from .helpers import get_index_data, get_language, get_scripts
from .keyboards import get_available_layouts, load_keyboard
from .models.keyboard import KeyboardLayout, KeyEntry, LayerLegends, DeadKey, Ligature

ALPHABET_DIR = files("worldalphabets") / "data" / "alphabets"


@dataclass
class Alphabet:
    """Alphabet data for a language."""

    alphabetical: List[str]
    uppercase: List[str]
    lowercase: List[str]
    frequency: Dict[str, float]


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
    )


def get_available_codes() -> List[str]:
    """Return sorted language codes with available alphabets."""
    return sorted(item["language"] for item in get_index_data())


__all__ = [
    # Alphabets
    "load_alphabet",
    "Alphabet",
    "get_available_codes",
    "get_index_data",
    "get_language",
    "get_scripts",
    # Keyboards
    "load_keyboard",
    "get_available_layouts",
    "KeyboardLayout",
    "KeyEntry",
    "LayerLegends",
    "DeadKey",
    "Ligature",
]
