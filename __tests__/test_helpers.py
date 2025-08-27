from worldalphabets import get_index_data, get_language


def test_get_index_data() -> None:
    data = get_index_data()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_language_default_script() -> None:
    lang = get_language("mr")
    assert lang is not None
    assert lang["script"] == "Deva"


def test_get_language_with_script() -> None:
    lang = get_language("mr", script="Latn")
    assert lang is not None
    assert lang["script"] == "Latn"
    assert "A" in lang["alphabetical"]


def test_get_language_invalid() -> None:
    assert get_language("invalid-code") is None
