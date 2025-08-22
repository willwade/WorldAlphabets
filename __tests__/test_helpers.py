from worldalphabets import get_index_data, get_language

def test_get_index_data() -> None:
    data = get_index_data()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_language() -> None:
    lang_info = get_language('en')
    assert isinstance(lang_info, dict)
    assert lang_info['language'] == 'en'
    assert lang_info['language-name'] == 'English'

def test_get_language_invalid() -> None:
    lang_info = get_language('invalid-code')
    assert lang_info is None
