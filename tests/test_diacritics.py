import pytest
from worldalphabets import (
    strip_diacritics,
    has_diacritics,
    characters_with_diacritics,
    get_diacritic_variants,
)


class TestStripDiacritics:
    """Test cases for strip_diacritics function."""

    def test_basic_diacritics(self) -> None:
        """Test basic diacritic removal."""
        assert strip_diacritics("café") == "cafe"
        assert strip_diacritics("naïve") == "naive"
        assert strip_diacritics("résumé") == "resume"

    def test_special_characters(self) -> None:
        """Test special characters that need explicit mapping."""
        assert strip_diacritics("Łódź") == "Lodz"
        assert strip_diacritics("Đorđe") == "Dorde"
        assert strip_diacritics("København") == "Kobenhavn"
        assert strip_diacritics("Þórr") == "Torr"
        assert strip_diacritics("Ðorðe") == "Dorde"

    def test_mixed_case(self) -> None:
        """Test mixed case handling."""
        assert strip_diacritics("ÄÖÜäöü") == "AOUaou"
        assert strip_diacritics("ÇçÑñ") == "CcNn"

    def test_edge_cases(self) -> None:
        """Test edge cases."""
        assert strip_diacritics("") == ""
        assert strip_diacritics("abc") == "abc"  # No diacritics
        assert strip_diacritics("123") == "123"  # Numbers
        assert strip_diacritics("!@#") == "!@#"  # Symbols

    def test_complex_text(self) -> None:
        """Test complex text with mixed content."""
        text = "Żółć gęślą jaźń! 123 @#$"
        expected = "Zolc gesla jazn! 123 @#$"
        assert strip_diacritics(text) == expected


class TestHasDiacritics:
    """Test cases for has_diacritics function."""

    def test_with_diacritics(self) -> None:
        """Test characters with diacritics."""
        assert has_diacritics("é")
        assert has_diacritics("ñ")
        assert has_diacritics("ü")
        assert has_diacritics("Ł")
        assert has_diacritics("ø")

    def test_without_diacritics(self) -> None:
        """Test characters without diacritics."""
        assert not has_diacritics("e")
        assert not has_diacritics("n")
        assert not has_diacritics("u")
        assert not has_diacritics("L")
        assert not has_diacritics("o")

    def test_edge_cases(self) -> None:
        """Test edge cases."""
        assert not has_diacritics("")
        assert not has_diacritics("1")
        assert not has_diacritics("!")

    def test_multi_character_strings(self) -> None:
        """Test with multi-character strings."""
        assert has_diacritics("café")  # Contains diacritics
        assert not has_diacritics("cafe")  # No diacritics


class TestCharactersWithDiacritics:
    """Test cases for characters_with_diacritics function."""

    def test_filtering(self) -> None:
        """Test basic filtering."""
        chars = ["a", "é", "ö", "b", "ñ"]
        result = characters_with_diacritics(chars)
        assert result == ["é", "ö", "ñ"]

    def test_empty_input(self) -> None:
        """Test with empty input."""
        assert characters_with_diacritics([]) == []

    def test_no_diacritics(self) -> None:
        """Test with no diacritics."""
        chars = ["a", "b", "c"]
        assert characters_with_diacritics(chars) == []

    def test_all_diacritics(self) -> None:
        """Test with all diacritics."""
        chars = ["é", "ñ", "ü"]
        assert characters_with_diacritics(chars) == ["é", "ñ", "ü"]

    def test_with_empty_strings(self) -> None:
        """Test handling of empty strings in input."""
        chars = ["a", "", "é", ""]
        result = characters_with_diacritics(chars)
        assert result == ["é"]


class TestGetDiacriticVariants:
    """Test cases for get_diacritic_variants function."""

    def test_polish_variants(self) -> None:
        """Test Polish diacritic variants."""
        variants = get_diacritic_variants("pl", "Latn")
        assert variants["L"] == ["L", "Ł"]
        assert variants["l"] == ["l", "ł"]
        assert variants["A"] == ["A", "Ą"]
        assert variants["a"] == ["a", "ą"]

    def test_invalid_language(self) -> None:
        """Test with invalid language code."""
        with pytest.raises(FileNotFoundError):
            get_diacritic_variants("invalid_lang")

    def test_language_without_script(self) -> None:
        """Test language detection without explicit script."""
        # This should work by finding the default script
        variants = get_diacritic_variants("pl")
        assert "L" in variants
        assert "l" in variants
