"""Utilities for loading world alphabets."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import json
from typing import Dict, List

from .helpers import get_index_data, get_language
from .keyboards import get_available_layouts, load_keyboard
from .models.keyboard import KeyboardLayout, KeyEntry, LayerLegends, DeadKey, Ligature

# The data files are packaged at the root of the site-packages directory,
# so we go up one level from the package to find the data directory.
from importlib.resources import as_file
with as_file(files("worldalphabets")) as p:
    _PACKAGE_PATH = Path(p)
DATA_DIR = _PACKAGE_PATH.parent.parent / "data" / "alphabets"


@dataclass
class Alphabet:
    """Alphabet data for a language."""

    alphabetical: List[str]
    uppercase: List[str]
    lowercase: List[str]
    frequency: Dict[str, float]


def load_alphabet(code: str) -> Alphabet:
    """Return alphabet information for ISO language ``code``."""

    path = DATA_DIR / f"{code}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return Alphabet(**data)


def get_available_codes() -> List[str]:
    """Return sorted language codes with available alphabets."""

    return sorted(
        Path(p.name).stem for p in DATA_DIR.iterdir() if p.name.endswith(".json")
    )


__all__ = [
    # Alphabets
    "load_alphabet",
    "Alphabet",
    "get_available_codes",
    "get_index_data",
    "get_language",
    # Keyboards
    "load_keyboard",
    "get_available_layouts",
    "KeyboardLayout",
    "KeyEntry",
    "LayerLegends",
    "DeadKey",
    "Ligature",
]
