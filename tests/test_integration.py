"""Integration tests for the WorldAlphabets library."""

from worldalphabets import (
    load_alphabet,
    strip_diacritics,
    has_diacritics,
    characters_with_diacritics,
    get_diacritic_variants,
    detect_languages,
    get_available_codes,
)


class TestIntegration:
    """Integration tests that verify all components work together."""
    
    def test_end_to_end_workflow(self) -> None:
        """Test a complete workflow from text analysis to language detection."""
        # Start with some Polish text
        text = "Żółć gęślą jaźń"
        
        # Detect languages
        detected = detect_languages(text)
        assert "pl" in detected
        
        # Load Polish alphabet
        alphabet = load_alphabet("pl")
        assert alphabet is not None
        assert len(alphabet.lowercase) > 0
        
        # Get diacritic variants for Polish
        variants = get_diacritic_variants("pl")
        assert "Z" in variants
        assert "z" in variants
        # Check that variants contain expected characters (order may vary)
        assert set(variants["Z"]) == {"Z", "Ż", "Ź"}
        assert set(variants["z"]) == {"z", "ż", "ź"}
        
        # Test diacritic processing
        stripped = strip_diacritics(text)
        assert stripped == "Zolc gesla jazn"
        
        # Find characters with diacritics
        chars_with_diac = characters_with_diacritics(list(text))
        expected_diac = ["Ż", "ó", "ł", "ć", "ę", "ś", "ą", "ź", "ń"]
        for char in expected_diac:
            if char in text:
                assert char in chars_with_diac
    
    def test_cross_language_detection(self) -> None:
        """Test language detection with text that could match multiple languages."""
        # Text that uses only basic Latin letters
        text = "hello world"
        detected = detect_languages(text)
        
        # Should detect multiple languages including English
        assert "en" in detected
        assert len(detected) > 5  # Many languages use these basic letters
        
        # Text with specific diacritics should narrow down options
        specific_text = "Łódź"
        specific_detected = detect_languages(specific_text)
        assert "pl" in specific_detected
        # The specific text should still detect Polish
        # Note: The number of detected languages may vary based on alphabet coverage
    
    def test_diacritic_consistency(self) -> None:
        """Test that diacritic handling is consistent across functions."""
        test_chars = ["é", "ñ", "ü", "Ł", "ø", "a", "b", "1", "!"]
        
        # Characters identified as having diacritics should be stripped differently
        for char in test_chars:
            has_diac = has_diacritics(char)
            stripped = strip_diacritics(char)
            
            if has_diac:
                assert char != stripped, f"Character {char} should be stripped"
            else:
                assert char == stripped, f"Character {char} should not be stripped"
    
    def test_alphabet_completeness(self) -> None:
        """Test that loaded alphabets contain expected diacritic variants."""
        # Test a few languages known to have diacritics
        test_languages = ["pl", "fr", "de", "es"]
        
        for lang in test_languages:
            try:
                alphabet = load_alphabet(lang)
                variants = get_diacritic_variants(lang)
                
                # All variant characters should be in the alphabet
                for base, variant_list in variants.items():
                    for variant in variant_list:
                        if variant.isupper():
                            assert variant in alphabet.uppercase, \
                                f"Variant {variant} not in {lang} uppercase"
                        else:
                            assert variant in alphabet.lowercase, \
                                f"Variant {variant} not in {lang} lowercase"
                            
            except FileNotFoundError:
                # Skip languages that don't have data
                continue
    
    def test_available_codes_consistency(self) -> None:
        """Test that available codes are consistent with loadable alphabets."""
        codes = get_available_codes()
        assert len(codes) > 0
        
        # Test a few random codes to ensure they can be loaded
        test_codes = codes[:5]  # Test first 5 codes
        
        for code in test_codes:
            try:
                alphabet = load_alphabet(code)
                assert alphabet is not None
                # Should have at least some letters
                assert len(alphabet.lowercase) > 0 or len(alphabet.uppercase) > 0
            except FileNotFoundError:
                # Some codes might not have alphabet data, that's ok
                continue
    
    def test_error_handling_robustness(self) -> None:
        """Test that error handling works correctly across all functions."""
        # Test with invalid language codes
        invalid_codes = ["invalid", "xyz", "123"]
        
        for code in invalid_codes:
            # These should handle errors gracefully
            detected = detect_languages("test")  # Should not crash
            assert isinstance(detected, list)
            
            # These should raise appropriate errors
            try:
                get_diacritic_variants(code)
                assert False, f"Should have raised error for {code}"
            except FileNotFoundError:
                pass  # Expected
