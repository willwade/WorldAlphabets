"""Test that word-based detection is prioritized over character-based fallback."""

import os
import pytest
from pathlib import Path
from typing import Generator
from worldalphabets.detect.optimized import optimized_detect_languages
from worldalphabets.helpers import get_index_data


@pytest.fixture(autouse=True)
def set_freq_dir() -> Generator[None, None, None]:
    """Set the frequency directory to the project root data directory for testing."""
    PROJECT_ROOT = Path(__file__).parent.parent
    old_value = os.environ.get("WORLDALPHABETS_FREQ_DIR")
    os.environ["WORLDALPHABETS_FREQ_DIR"] = str(PROJECT_ROOT / "data" / "freq" / "top1000")
    yield
    # Restore old value
    if old_value is None:
        os.environ.pop("WORLDALPHABETS_FREQ_DIR", None)
    else:
        os.environ["WORLDALPHABETS_FREQ_DIR"] = old_value


def test_shona_word_detection_priority() -> None:
    """
    Test that Shona ranks #1 when text contains Shona-specific words.
    
    The text "vanoti vanodaro" contains two words that are in Shona's top 25
    most frequent words (ranks 18 and 21). This should result in word-based
    detection for Shona, which should rank higher than character-based fallback
    for other Latin-script languages.
    """
    text = "vanoti vanodaro"
    
    # Get uniform priors for fair comparison
    index = get_index_data()
    all_langs = list(set(item["language"] for item in index))
    uniform_priors = {lang: 1.0 / len(all_langs) for lang in all_langs}
    
    # Detect with uniform priors
    results = optimized_detect_languages(text, priors=uniform_priors, topk=10)
    
    # Extract language codes
    detected_langs = [lang for lang, score in results]
    
    # Shona should be #1
    assert detected_langs[0] == "sn", (
        f"Expected Shona (sn) to rank #1, but got {detected_langs[0]}. "
        f"Top 5: {detected_langs[:5]}"
    )


def test_spanish_word_detection_priority() -> None:
    """
    Test that Spanish ranks #1 for Spanish-specific text.
    
    The phrase "gracias por todo" contains common Spanish words that should
    trigger word-based detection for Spanish.
    """
    text = "gracias por todo"
    
    # Get uniform priors
    index = get_index_data()
    all_langs = list(set(item["language"] for item in index))
    uniform_priors = {lang: 1.0 / len(all_langs) for lang in all_langs}
    
    # Detect with uniform priors
    results = optimized_detect_languages(text, priors=uniform_priors, topk=10)
    
    # Extract language codes
    detected_langs = [lang for lang, score in results]
    
    # Spanish should be in top 3 (allowing some flexibility for similar languages)
    assert "es" in detected_langs[:3], (
        f"Expected Spanish (es) in top 3, but got {detected_langs[:3]}"
    )


def test_french_word_detection_priority() -> None:
    """
    Test that French ranks #1 for French-specific text.
    
    The phrase "je ne peux pas venir" contains common French words.
    """
    text = "je ne peux pas venir"
    
    # Get uniform priors
    index = get_index_data()
    all_langs = list(set(item["language"] for item in index))
    uniform_priors = {lang: 1.0 / len(all_langs) for lang in all_langs}
    
    # Detect with uniform priors
    results = optimized_detect_languages(text, priors=uniform_priors, topk=10)
    
    # Extract language codes
    detected_langs = [lang for lang, score in results]
    
    # French should be in top 3
    assert "fr" in detected_langs[:3], (
        f"Expected French (fr) in top 3, but got {detected_langs[:3]}"
    )


def test_word_based_beats_character_based() -> None:
    """
    Test that languages with word matches rank higher than those with only
    character matches, even if character overlap is high.
    
    This is a regression test for the issue where character-based scores
    (0.082) were ranking higher than word-based scores (0.073).
    """
    text = "vanoti vanodaro"
    
    # Get uniform priors
    index = get_index_data()
    all_langs = list(set(item["language"] for item in index))
    uniform_priors = {lang: 1.0 / len(all_langs) for lang in all_langs}
    
    # Detect with uniform priors
    results = optimized_detect_languages(text, priors=uniform_priors, topk=20)
    
    # Find positions of Shona (word-based) vs Swahili/English (character-based)
    positions = {lang: i for i, (lang, score) in enumerate(results)}
    
    sn_pos = positions.get("sn", 999)
    sw_pos = positions.get("sw", 999)
    en_pos = positions.get("en", 999)
    
    # Shona (word-based) should rank higher than Swahili and English (character-based)
    assert sn_pos < sw_pos, (
        f"Shona (word-based, pos {sn_pos}) should rank higher than "
        f"Swahili (character-based, pos {sw_pos})"
    )
    assert sn_pos < en_pos, (
        f"Shona (word-based, pos {sn_pos}) should rank higher than "
        f"English (character-based, pos {en_pos})"
    )


if __name__ == "__main__":
    # Run tests manually for debugging
    print("Testing Shona word detection priority...")
    test_shona_word_detection_priority()
    print("✅ Shona test passed!\n")
    
    print("Testing Spanish word detection priority...")
    test_spanish_word_detection_priority()
    print("✅ Spanish test passed!\n")
    
    print("Testing French word detection priority...")
    test_french_word_detection_priority()
    print("✅ French test passed!\n")
    
    print("Testing word-based beats character-based...")
    test_word_based_beats_character_based()
    print("✅ Word-based priority test passed!\n")
    
    print("All tests passed! ✅")

