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
from worldalphabets.inflect import (
    join_words,
    get_features,
    load_tag_map,
    create_buffer,
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


def test_get_features_german_verb() -> None:
    features = get_features("v_ind_pl_1_prs")
    assert features is not None
    assert features["pos"] == "verb"
    assert features["mood"] == "indicative"
    assert features["number"] == "plural"
    assert features["person"] == "1"
    assert features["tense"] == "present"


def test_get_features_english_plural() -> None:
    features = get_features("plural")
    assert features is not None
    assert features["number"] == "plural"


def test_get_features_english_past_participle() -> None:
    features = get_features("past_participle")
    assert features is not None
    assert features["verbform"] == "participle"
    assert features["tense"] == "past"


def test_get_features_arabic_dual() -> None:
    features = get_features("adj_du_fem_def_acc")
    assert features is not None
    assert features["pos"] == "adjective"
    assert features["number"] == "dual"
    assert features["gender"] == "feminine"
    assert features["definiteness"] == "definite"
    assert features["case"] == "accusative"


def test_get_features_unknown_tag() -> None:
    features = get_features("xyz_unknown_123")
    assert features is None


def test_load_tag_map() -> None:
    tag_map = load_tag_map()
    assert isinstance(tag_map, dict)
    assert len(tag_map) > 7000
    assert "v_ind_pl_1_prs" in tag_map
    assert "features" in tag_map["v_ind_pl_1_prs"]


def test_get_features_basque_args() -> None:
    features = get_features(
        "v_argabs1_argabspl_argerg2_argergpl_hyp_ind"
    )
    assert features is not None
    assert features["pos"] == "verb"
    assert "arg_abs" in features
    assert "arg_erg" in features
    assert features["mood"] == "indicative"


def test_get_features_japanese_formality() -> None:
    features = get_features("v_form_elev_imp_col")
    assert features is not None
    assert features["pos"] == "verb"
    assert features["formality"] == "colloquial"
    assert features["mood"] == "imperative"


def test_get_features_variant() -> None:
    features = get_features("adj_acc_fem_sg_2")
    assert features is not None
    assert features["pos"] == "adjective"
    assert features["variant"] == "2"


class TestSentenceBuffer:
    def test_create_buffer(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        assert len(buf) == 0
        assert buf.tokens == []

    def test_push_and_render(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        snap = buf.push("she")
        assert len(buf) == 1
        assert snap.text == "she"
        assert len(snap.tokens) == 1
        assert snap.tokens[0].base == "she"
        assert snap.tokens[0].surface == "she"

    def test_push_applies_rules(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("de")
        buf.push("ich")
        snap = buf.push("haben")
        assert snap.tokens[-1].base == "haben"
        assert snap.tokens[-1].surface == "habe"
        assert snap.tokens[-1].rule_id is not None

    def test_update_reacts(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("de")
        buf.push("ich")
        buf.push("haben")
        assert buf.render_tokens()[-1].surface == "habe"
        snap = buf.update(0, "er")
        assert snap.tokens[-1].surface == "hat"

    def test_remove(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("I")
        buf.push("run")
        snap = buf.remove(0)
        assert len(buf) == 1
        assert snap.text == "run"

    def test_insert(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        buf.push("run")
        snap = buf.insert(1, "not")
        assert len(snap.tokens) == 3

    def test_clear(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        buf.push("run")
        buf.clear()
        assert len(buf) == 0
        assert buf.render() == ""

    def test_token_at(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        buf.push("run")
        assert buf.token_at(0) == "she"
        assert buf.token_at(1) == "run"

    def test_token_at_out_of_range(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        try:
            buf.token_at(5)
        except IndexError:
            pass
        else:
            raise AssertionError("expected IndexError")

    def test_render_snapshot_diffs_add(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        snap = buf.push("she")
        assert len(snap.diffs) == 1
        assert snap.diffs[0].kind == "add"
        assert snap.diffs[0].new_surface == "she"

    def test_render_snapshot_diffs_change(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("de")
        buf.push("ich")
        buf.push("haben")
        snap = buf.update(0, "er")
        change_diffs = [d for d in snap.diffs if d.kind == "change"]
        assert len(change_diffs) > 0

    def test_render_snapshot_diffs_remove(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        buf.push("run")
        snap = buf.remove(1)
        remove_diffs = [d for d in snap.diffs if d.kind == "remove"]
        assert len(remove_diffs) > 0

    def test_join_applied_french(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("fr")
        buf.push("le")
        snap = buf.push("ami")
        assert "l'ami" in snap.text
        join_tokens = [t for t in snap.tokens if t.join_applied]
        assert len(join_tokens) == 1

    def test_german_sentence(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("de")
        buf.push("ich")
        snap = buf.push("haben")
        assert snap.text == "ich habe"

    def test_unknown_word_passes_through(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        snap = buf.push("xyz123")
        assert snap.text == "xyz123"
        assert snap.tokens[0].surface == "xyz123"

    def test_render_tokens_method(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("de")
        buf.push("ich")
        buf.push("haben")
        tokens = buf.render_tokens()
        assert len(tokens) == 2
        assert tokens[0].surface == "ich"
        assert tokens[1].surface == "habe"

    def test_multiple_pushes_accumulate(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        buf.push("run")
        snap = buf.push("fast")
        assert len(snap.tokens) == 3

    def test_spanish_no_inflection_still_works(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("es")
        buf.push("yo")
        snap = buf.push("hablar")
        assert snap.text == "yo hablar"

    def test_update_out_of_range(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        try:
            buf.update(5, "I")
        except IndexError:
            pass
        else:
            raise AssertionError("expected IndexError")

    def test_remove_out_of_range(self) -> None:
        clear_inflection_cache()
        buf = create_buffer("en")
        buf.push("she")
        try:
            buf.remove(5)
        except IndexError:
            pass
        else:
            raise AssertionError("expected IndexError")
