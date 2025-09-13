import unicodedata
from typing import Dict, Iterable, List, Set


def strip_diacritics(text: str) -> str:
    """Return ``text`` with diacritic marks removed."""

    result: List[str] = []
    for ch in text:
        normalized = unicodedata.normalize("NFD", ch)
        base = "".join(c for c in normalized if not unicodedata.combining(c))
        if base == ch:
            name = unicodedata.name(ch, "")
            if " WITH " in name:
                base_name = name.split(" WITH ")[0]
                try:
                    base = unicodedata.lookup(base_name)
                except KeyError:
                    pass
        result.append(base)
    return "".join(result)


def has_diacritics(char: str) -> bool:
    """Return ``True`` if ``char`` contains any diacritic marks."""
    return char != strip_diacritics(char)


def characters_with_diacritics(chars: Iterable[str]) -> List[str]:
    """Return characters from ``chars`` that contain diacritic marks."""
    return [c for c in chars if has_diacritics(c)]


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
