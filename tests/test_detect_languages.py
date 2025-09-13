from worldalphabets import detect_languages


def test_detect_languages() -> None:
    langs = detect_languages("Żółć")
    assert "pl" in langs
