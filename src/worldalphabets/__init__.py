"""Utilities for loading world alphabets."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import json
from typing import Dict, List

DATA_DIR = files("worldalphabets") / "data" / "alphabets"


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


__all__ = ["load_alphabet", "Alphabet", "get_available_codes"]
