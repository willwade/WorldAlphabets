from worldalphabets import get_language, load_alphabet


def test_get_language_with_script() -> None:
    lang = get_language("mr", script="Latn")
    assert lang is not None
    assert lang["script"] == "Latn"
    assert "A" in lang["alphabetical"]


def test_load_alphabet_with_script() -> None:
    alphabet = load_alphabet("mr", "Latn")
    assert "A" in alphabet.alphabetical
