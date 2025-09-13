from worldalphabets import detect_languages


class TestDetectLanguages:
    """Test cases for detect_languages function."""

    def test_polish_text(self) -> None:
        """Test detection of Polish text."""
        langs = detect_languages("Żółć")
        assert "pl" in langs

    def test_english_text(self) -> None:
        """Test detection of English text."""
        langs = detect_languages("hello world")
        assert "en" in langs

    def test_mixed_diacritics(self) -> None:
        """Test text with various diacritics."""
        langs = detect_languages("café naïve résumé")
        # Should match languages that have these base letters
        assert len(langs) > 0

    def test_special_characters(self) -> None:
        """Test text with special characters like Ł, Ø."""
        langs = detect_languages("Łódź")
        assert "pl" in langs

    def test_empty_input(self) -> None:
        """Test with empty input."""
        assert detect_languages("") == []

    def test_no_letters(self) -> None:
        """Test with no alphabetic characters."""
        assert detect_languages("123 !@# $%^") == []

    def test_numbers_and_symbols(self) -> None:
        """Test text with numbers and symbols mixed with letters."""
        langs = detect_languages("hello123!@#")
        assert "en" in langs

    def test_single_letter(self) -> None:
        """Test with single letter."""
        langs = detect_languages("a")
        # Should match many languages that have 'a'
        assert len(langs) > 10

    def test_case_insensitive(self) -> None:
        """Test that detection is case insensitive."""
        langs_lower = detect_languages("hello")
        langs_upper = detect_languages("HELLO")
        langs_mixed = detect_languages("Hello")
        # All should detect the same languages
        assert set(langs_lower) == set(langs_upper) == set(langs_mixed)

    def test_unicode_normalization(self) -> None:
        """Test that Unicode normalization works correctly."""
        # These should be treated the same after normalization
        text1 = "café"  # é as single character
        text2 = "cafe\u0301"  # e + combining acute accent
        langs1 = detect_languages(text1)
        langs2 = detect_languages(text2)
        assert set(langs1) == set(langs2)
