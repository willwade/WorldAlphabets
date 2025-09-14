from pathlib import Path

from scripts.build_top200.sources import (
    load_hermitdave,
    load_leipzig,
    load_stopwords,
    load_tatoeba,
)


def test_load_leipzig(tmp_path: Path) -> None:
    p = tmp_path / "l.txt"
    p.write_text("1\tfoo\t10\n2\tbar\t9\n", encoding="utf-8")
    assert load_leipzig(p) == ["foo", "bar"]


def test_load_hermitdave(tmp_path: Path) -> None:
    p = tmp_path / "h.txt"
    p.write_text("foo 10\nbar 9\n", encoding="utf-8")
    assert load_hermitdave(p) == ["foo", "bar"]


def test_load_stopwords(tmp_path: Path) -> None:
    p = tmp_path / "s.txt"
    p.write_text("foo\nbar\n", encoding="utf-8")
    assert load_stopwords(p) == ["foo", "bar"]


def test_load_tatoeba(tmp_path: Path) -> None:
    p = tmp_path / "t.txt"
    p.write_text("foo bar\nqux\n", encoding="utf-8")
    assert load_tatoeba(p, "word") == ["foo", "bar", "qux"]
    assert load_tatoeba(p, "bigram")[:2] == ["fo", "oo"]
