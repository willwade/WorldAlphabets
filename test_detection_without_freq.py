#!/usr/bin/env python3
"""
Test language detection for languages without frequency data.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets import get_available_codes
from worldalphabets.detect import detect_languages

def get_languages_without_freq_data():
    """Find languages that have alphabet data but no frequency data."""
    # Get all available language codes from alphabet data
    all_codes = get_available_codes()
    
    # Get languages with frequency data
    freq_dir = Path("data/freq/top200")
    freq_codes = set()
    if freq_dir.exists():
        for freq_file in freq_dir.glob("*.txt"):
            freq_codes.add(freq_file.stem)
    
    # Find languages without frequency data
    without_freq = [code for code in all_codes if code not in freq_codes]
    
    print(f"Total languages with alphabet data: {len(all_codes)}")
    print(f"Languages with frequency data: {len(freq_codes)}")
    print(f"Languages WITHOUT frequency data: {len(without_freq)}")
    print(f"\nFirst 20 languages without frequency data: {without_freq[:20]}")
    
    return without_freq

def test_detection_without_freq(test_lang, test_text, candidate_langs=None):
    """Test detection for a language without frequency data."""
    print(f"\n{'='*60}")
    print(f"Testing detection for language: {test_lang}")
    print(f"Test text: '{test_text}'")
    print(f"{'='*60}")
    
    if candidate_langs is None:
        # Use a small set of candidates including the test language
        candidate_langs = [test_lang, 'en', 'es', 'fr', 'de', 'it']
    
    print(f"Candidate languages: {candidate_langs}")
    
    try:
        results = detect_languages(
            test_text,
            candidate_langs=candidate_langs,
            topk=len(candidate_langs)
        )
        
        print("\nDetection results:")
        if results:
            for i, (lang, score) in enumerate(results, 1):
                print(f"  {i}. {lang}: {score:.4f}")
        else:
            print("  No languages detected (all scores below threshold)")
            
        # Check if our target language was detected
        detected_langs = [lang for lang, score in results]
        if test_lang in detected_langs:
            rank = detected_langs.index(test_lang) + 1
            score = results[detected_langs.index(test_lang)][1]
            print(f"\n✓ Target language '{test_lang}' detected at rank {rank} with score {score:.4f}")
        else:
            print(f"\n✗ Target language '{test_lang}' NOT detected")
            
    except Exception as e:
        print(f"Error during detection: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("WorldAlphabets Language Detection Test")
    print("Testing detection for languages without frequency data")
    
    # Find languages without frequency data
    without_freq = get_languages_without_freq_data()
    
    if not without_freq:
        print("All languages have frequency data!")
        return
    
    # Test a few specific languages without frequency data
    test_cases = [
        # Pick some languages that are likely to have distinctive text
        ("aa", "Qafar af keena"),  # Afar - if available
        ("ab", "Аҧсуа бызшәа"),   # Abkhazian - Cyrillic script
        ("cop", "ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ"),  # Coptic - distinctive script
        ("gez", "ግዕዝ"),           # Ge'ez - Ethiopic script
        ("vai", "ꕙꔤ"),            # Vai - distinctive script
    ]
    
    for lang_code, sample_text in test_cases:
        if lang_code in without_freq:
            test_detection_without_freq(lang_code, sample_text)
        else:
            print(f"\nSkipping {lang_code} - it has frequency data")
    
    # Test with a broader candidate set for one case
    if "ab" in without_freq:
        print(f"\n{'='*60}")
        print("Testing Abkhazian with broader candidate set")
        print(f"{'='*60}")
        
        # Include other Cyrillic languages as candidates
        cyrillic_candidates = ["ab", "ru", "bg", "mk", "sr", "uk", "be"]
        test_detection_without_freq("ab", "Аҧсуа бызшәа", cyrillic_candidates)

if __name__ == "__main__":
    main()
