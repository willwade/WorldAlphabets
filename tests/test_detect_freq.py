import os
from pathlib import Path

from worldalphabets import detect_languages


def test_phrase_rankings() -> None:
    text = "gracias por todo"
    res = detect_languages(
        text,
        candidate_langs=["es", "pt"],
        priors={"es": 0.6, "pt": 0.4},
    )
    assert res[0][0] == "es"
    assert res[1][0] == "pt"

    text = "je ne peux pas venir"
    res = detect_languages(
        text,
        candidate_langs=["fr", "en"],
        priors={"fr": 0.6, "en": 0.4},
    )
    assert res[0][0] == "fr"
    assert res[1][0] == "en"

    text = "今日は忙しい"
    res = detect_languages(
        text,
        candidate_langs=["ja", "zh"],
        priors={"ja": 0.6, "zh": 0.4},
    )
    assert res[0][0] == "ja"
    assert res[1][0] == "zh"

    text = "o dia está lindo"
    res = detect_languages(
        text,
        candidate_langs=["pt", "es"],
        priors={"pt": 0.6, "es": 0.4},
    )
    assert res[0][0] == "pt"
    assert res[1][0] == "es"


def test_empty_and_prior_fallback(tmp_path: Path) -> None:
    assert detect_languages("", candidate_langs=["en", "es"]) == []

    freq_dir = tmp_path / "freq"
    freq_dir.mkdir()
    os.environ["WORLDALPHABETS_FREQ_DIR"] = str(freq_dir)
    try:
        res = detect_languages("hello", candidate_langs=["en"], priors={"en": 1.0})
    finally:
        del os.environ["WORLDALPHABETS_FREQ_DIR"]
    assert res[0][0] == "en"


def test_env_override(tmp_path: Path) -> None:
    freq_dir = tmp_path / "freq"
    freq_dir.mkdir()
    (freq_dir / "es.txt").write_text("override", encoding="utf-8")
    # Add English frequency data with "override" at lower rank to prevent fallback
    (freq_dir / "en.txt").write_text("hello\nworld\ntest\noverride", encoding="utf-8")
    os.environ["WORLDALPHABETS_FREQ_DIR"] = str(freq_dir)
    try:
        res = detect_languages("override", candidate_langs=["es", "en"])
    finally:
        del os.environ["WORLDALPHABETS_FREQ_DIR"]
    assert res[0][0] == "es"


def test_bigram_header(tmp_path: Path) -> None:
    freq_dir = tmp_path / "freq"
    freq_dir.mkdir()
    (freq_dir / "zz.txt").write_text("# type=bigram\nab\n", encoding="utf-8")
    os.environ["WORLDALPHABETS_FREQ_DIR"] = str(freq_dir)
    try:
        res = detect_languages("ab", candidate_langs=["zz"])
    finally:
        del os.environ["WORLDALPHABETS_FREQ_DIR"]
    assert res and res[0][0] == "zz"
