import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.import_inflection_sources import (
    load_forms,
    load_frequency_priorities,
    merge_forms,
)
from scripts.fetch_inflection_sources import load_locale_candidates
from scripts.sync_inflection_tests import tests_csv_to_array as csv_tests_to_array
from scripts.ingest_inflection_tests import tests_array_to_csv as array_tests_to_csv


def test_parse_unimorph_source(tmp_path: Path) -> None:
    source = tmp_path / "um.tsv"
    source.write_text("go\twent\tV;PST\ngo\tgoing\tV;V.PTCP;PRS\n", encoding="utf-8")

    forms = load_forms(source, "unimorph", "unimorph")

    assert forms[0].base == "go"
    assert forms[0].form == "went"
    assert forms[0].part_of_speech == "verb"
    assert forms[0].inflection == "v_pst"


def test_parse_wiktextract_source(tmp_path: Path) -> None:
    source = tmp_path / "wiktextract.jsonl"
    source.write_text(
        json.dumps(
            {
                "word": "cat",
                "pos": "noun",
                "forms": [{"form": "cats", "tags": ["plural"]}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    forms = load_forms(source, "wiktextract", "wiktextract")

    assert forms[0].base == "cat"
    assert forms[0].form == "cats"
    assert forms[0].inflection == "plural"


def test_parse_hfst_tsv_source(tmp_path: Path) -> None:
    source = tmp_path / "hfst.tsv"
    source.write_text("talo\ttalot\tN+PL\tnoun\n", encoding="utf-8")

    forms = load_forms(source, "hfst-tsv", "omorfi")

    assert forms[0].base == "talo"
    assert forms[0].form == "talot"
    assert forms[0].part_of_speech == "noun"


def test_merge_forms_adds_base_and_surface_entries(tmp_path: Path) -> None:
    source = tmp_path / "um.tsv"
    source.write_text("go\twent\tV;PST\n", encoding="utf-8")
    forms = load_forms(source, "unimorph", "unimorph")
    words: dict[str, Any] = {"_type": "words", "_locale": "en", "_version": "0.1"}

    changed = merge_forms(words, forms, {"go": 10, "went": 9}, True)

    assert changed == 1
    assert words["go"]["inflections"]["v_pst"] == "went"
    assert words["went"]["base"] == "go"
    assert words["go"]["priority"] == 10


def test_load_frequency_priorities_falls_back_to_base_locale() -> None:
    priorities = load_frequency_priorities("pt-BR", 5)

    assert priorities
    assert max(priorities.values()) == 10


def test_unimorph_candidates_use_iso3_and_overrides() -> None:
    candidates = {item.locale: item.candidates for item in load_locale_candidates(["ar", "pt-BR", "en"])}

    assert candidates["ar"][0] == "ara"
    assert candidates["pt-BR"][0] == "por"
    assert "eng" in candidates["en"]


def test_tests_csv_to_array(tmp_path: Path) -> None:
    tests = tmp_path / "tests.csv"
    tests.write_text(
        "rule_id,inflection,pre_words,test_word,updated_words\n"
        'she_looks,simple_present,she,look,she looks\n'
        'no_rule,,want,look,want look\n',
        encoding="utf-8",
    )

    rows = csv_tests_to_array(tests)

    assert rows[0] == [
        "she",
        "look",
        "she looks",
        {"rule_id": "she_looks", "inflection": "simple_present"},
    ]
    assert rows[1] == ["want", "look", "want look", {"rule_id": "no_rule"}]


def test_tests_array_to_csv_roundtrip(tmp_path: Path) -> None:
    tests = [
        ["she", "look", "she looks", {"rule_id": "she_looks", "inflection": "simple_present"}],
        ["want", "look", "want look", {"rule_id": "no_rule"}],
    ]

    csv_text = array_tests_to_csv(tests)
    path = tmp_path / "tests.csv"
    path.write_text(csv_text, encoding="utf-8")

    assert csv_tests_to_array(path) == tests
