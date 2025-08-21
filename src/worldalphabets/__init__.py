"""Utilities for loading world alphabets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "alphabets"


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


__all__ = ["load_alphabet", "Alphabet"]
