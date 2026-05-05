from worldalphabets import (
    get_available_inflection_locales,
    get_inflection_summary,
    load_inflection_data,
    load_inflection_rules,
    load_inflection_words,
    lookup_word,
    apply_rules,
    clear_inflection_cache,
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


def test_get_inflection_summary() -> None:
    summary = get_inflection_summary("en")
    assert summary.locale == "en"
    assert summary.word_count > 0
    assert summary.rule_count > 0
    assert summary.test_count > 0
    assert "verb" in summary.pos_types
    assert len(summary.inflection_keys) > 0


def test_lookup_word_returns_result() -> None:
    clear_inflection_cache()
    result = lookup_word("en", "run", "she")
    assert result.word == "run"
    assert result.replacement is not None


def test_apply_rules_transforms_text() -> None:
    clear_inflection_cache()
    result = apply_rules("en", "she run")
    assert isinstance(result, str)
    assert len(result) > 0
