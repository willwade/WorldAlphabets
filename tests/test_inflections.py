from worldalphabets import (
    get_available_inflection_locales,
    load_inflection_data,
    load_inflection_rules,
    load_inflection_words,
)


def test_inflection_locale_index_loads() -> None:
    locales = get_available_inflection_locales()
    assert isinstance(locales, list)
    assert "ar" in locales


def test_missing_inflection_locale_raises() -> None:
    try:
        load_inflection_words("zz")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing inflection words should raise")

    try:
        load_inflection_rules("zz")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing inflection rules should raise")


def test_inflection_locale_falls_back_to_base_language() -> None:
    data = load_inflection_data("en-TEST")

    assert data["words"]["_locale"] == "en"
    assert data["rules"]["_locale"] == "en"
