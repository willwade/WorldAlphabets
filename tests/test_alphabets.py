from worldalphabets import get_language, load_alphabet


def test_get_language_with_script() -> None:
    lang = get_language("mr", script="Latn")
    assert lang is not None
    assert lang["script"] == "Latn"
    assert "A" in lang["alphabetical"]


def test_load_alphabet_with_script() -> None:
    alphabet = load_alphabet("mr", "Latn")
    assert "A" in alphabet.alphabetical


def test_case_alignment() -> None:
    from pathlib import Path
    import json
    import unicodedata

    for path in Path("data/alphabets").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        upper = data["uppercase"]
        lower = data["lowercase"]
        assert data["alphabetical"] == upper
        assert len(upper) == len(lower)
        for up, low in zip(upper, lower):
            if (
                unicodedata.normalize("NFC", up.lower())
                != unicodedata.normalize("NFC", low)
                and unicodedata.normalize("NFC", low.upper())
                != unicodedata.normalize("NFC", up)
            ):
                raise AssertionError(f"Mismatch in {path.name}: {up} / {low}")
