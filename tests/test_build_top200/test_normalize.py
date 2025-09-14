from scripts.build_top200.normalize import normalize_token


def test_normalization_rules() -> None:
    allow = {"default": {"a", "i"}}
    assert normalize_token("Café", "en", allow) == "café"
    assert normalize_token("can't", "en", allow) == "cant"
    assert normalize_token("42", "en", allow) is None
    assert normalize_token("x", "en", allow) is None
    assert normalize_token("i", "en", allow) == "i"
