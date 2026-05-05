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
from worldalphabets.inflect import join_words


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


def test_join_words_french_elision() -> None:
    clear_inflection_cache()
    jr = join_words("fr", "le", "ami")
    assert jr is not None
    assert jr.result == "l'ami"
    assert jr.replaces_pair is True

    jr2 = join_words("fr", "je", "aime")
    assert jr2 is not None
    assert jr2.result == "j'aime"


def test_join_words_french_h_aspire() -> None:
    clear_inflection_cache()
    jr = join_words("fr", "le", "hibou")
    assert jr is not None
    assert jr.result == "le hibou"
    assert jr.replaces_pair is False


def test_join_words_english_a_an() -> None:
    clear_inflection_cache()
    jr = join_words("en", "a", "apple")
    assert jr is not None
    assert jr.result == "an apple"

    jr2 = join_words("en", "a", "university")
    assert jr2 is not None
    assert jr2.result == "a university"

    jr3 = join_words("en", "a", "hour")
    assert jr3 is not None
    assert jr3.result == "an hour"


def test_join_words_spanish_contraction() -> None:
    clear_inflection_cache()
    jr = join_words("es", "a", "el")
    assert jr is not None
    assert jr.result == "al"

    jr2 = join_words("es", "de", "el")
    assert jr2 is not None
    assert jr2.result == "del"


def test_join_words_no_match() -> None:
    clear_inflection_cache()
    jr = join_words("en", "the", "dog")
    assert jr is None


def test_apply_rules_with_join_french() -> None:
    clear_inflection_cache()
    result = apply_rules("fr", "le ami")
    assert "l'ami" in result


def test_apply_rules_with_join_english() -> None:
    clear_inflection_cache()
    result = apply_rules("en", "a apple")
    assert "an apple" in result
