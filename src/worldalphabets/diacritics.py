import unicodedata
from typing import Iterable, List


def strip_diacritics(text: str) -> str:
    """Return ``text`` with all combining diacritic marks removed."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def has_diacritics(char: str) -> bool:
    """Return ``True`` if ``char`` contains any diacritic marks."""
    return char != strip_diacritics(char)


def characters_with_diacritics(chars: Iterable[str]) -> List[str]:
    """Return characters from ``chars`` that contain diacritic marks."""
    return [c for c in chars if has_diacritics(c)]
