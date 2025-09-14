from scripts.build_top200.tokenize import char_bigrams, word_tokens


def test_word_tokens() -> None:
    assert word_tokens("Hello, world! 123") == ["Hello", "world"]


def test_char_bigrams() -> None:
    assert char_bigrams("abcd") == ["ab", "bc", "cd"]
    assert char_bigrams("a1b") == ["ab"]
