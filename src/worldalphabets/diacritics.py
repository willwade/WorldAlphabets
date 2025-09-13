import unicodedata
from typing import Dict, Iterable, List, Set

# Special characters that don't decompose properly with NFD
# These need explicit mapping to their base forms
SPECIAL_BASE_MAPPING = {
    "Ł": "L",
    "ł": "l",
    "Đ": "D",
    "đ": "d",
    "Ø": "O",
    "ø": "o",
    "Ð": "D",  # Icelandic eth
    "ð": "d",
    "Þ": "T",  # Icelandic thorn
    "þ": "t",
    "Ŋ": "N",  # Eng
    "ŋ": "n",
}


def strip_diacritics(text: str) -> str:
    """Return ``text`` with diacritic marks removed.

    This function removes diacritic marks from characters using Unicode
    normalization (NFD) and also handles special cases like Ł, Đ, Ø
    that don't decompose properly.
    """
    if not text:
        return text

    result: List[str] = []
    for ch in text:
        # First check if it's a special character that needs explicit mapping
        if ch in SPECIAL_BASE_MAPPING:
            result.append(SPECIAL_BASE_MAPPING[ch])
        else:
            # Use Unicode normalization to decompose and remove combining marks
            normalized = unicodedata.normalize("NFD", ch)
            base = "".join(c for c in normalized if not unicodedata.combining(c))
            result.append(base)
    return "".join(result)


def has_diacritics(char: str) -> bool:
    """Return ``True`` if ``char`` contains any diacritic marks.

    Args:
        char: A single character or string to check

    Returns:
        True if the character has diacritics, False otherwise
    """
    if not char:
        return False
    return char != strip_diacritics(char)


def characters_with_diacritics(chars: Iterable[str]) -> List[str]:
    """Return characters from ``chars`` that contain diacritic marks.

    Args:
        chars: An iterable of characters to filter

    Returns:
        List of characters that contain diacritic marks
    """
    return [c for c in chars if c and has_diacritics(c)]


def diacritic_variants(chars: Iterable[str]) -> Dict[str, List[str]]:
    """Group ``chars`` by base form and return those with variants.

    The result maps a base character to a sorted list of characters in ``chars``
    that share that base and include at least one diacritic form.
    """

    groups: Dict[str, Set[str]] = {}
    for ch in chars:
        base = strip_diacritics(ch)
        groups.setdefault(base, set()).add(ch)

    return {
        base: sorted(list(variants))
        for base, variants in groups.items()
        if len(variants) > 1
    }
