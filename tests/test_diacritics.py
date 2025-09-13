from worldalphabets import (
    strip_diacritics,
    has_diacritics,
    characters_with_diacritics,
    get_diacritic_variants,
)


def test_strip_diacritics() -> None:
    assert strip_diacritics("café") == "cafe"


def test_has_diacritics() -> None:
    assert has_diacritics("é")
    assert not has_diacritics("e")


def test_characters_with_diacritics() -> None:
    chars = ["a", "é", "ö", "b"]
    assert characters_with_diacritics(chars) == ["é", "ö"]


def test_get_diacritic_variants() -> None:
    variants = get_diacritic_variants("pl", "Latn")
    assert variants["L"] == ["L", "Ł"]
    assert variants["l"] == ["l", "ł"]
