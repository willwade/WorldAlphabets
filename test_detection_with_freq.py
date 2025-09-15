#!/usr/bin/env python3
"""
Test language detection for languages WITH frequency data to verify our setup works.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets.detect import detect_languages

def test_detection_with_freq():
    """Test detection for languages that have frequency data."""
    
    test_cases = [
        ("en", "Hello world this is a test", ["en", "es", "fr", "de", "it"]),
        ("es", "Hola mundo esto es una prueba", ["en", "es", "fr", "de", "it"]),
        ("fr", "Bonjour le monde ceci est un test", ["en", "es", "fr", "de", "it"]),
        ("de", "Hallo Welt das ist ein Test", ["en", "es", "fr", "de", "it"]),
        ("pl", "Żółć gęś jaźń", ["pl", "cs", "sk", "hr", "sl"]),  # Polish with diacritics
    ]
    
    for lang_code, sample_text, candidates in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing detection for language: {lang_code}")
        print(f"Test text: '{sample_text}'")
        print(f"Candidate languages: {candidates}")
        print(f"{'='*60}")
        
        try:
            results = detect_languages(
                sample_text,
                candidate_langs=candidates,
                topk=len(candidates)
            )
            
            print("\nDetection results:")
            if results:
                for i, (lang, score) in enumerate(results, 1):
                    print(f"  {i}. {lang}: {score:.4f}")
            else:
                print("  No languages detected (all scores below threshold)")
                
            # Check if our target language was detected
            detected_langs = [lang for lang, score in results]
            if lang_code in detected_langs:
                rank = detected_langs.index(lang_code) + 1
                score = results[detected_langs.index(lang_code)][1]
                print(f"\n✓ Target language '{lang_code}' detected at rank {rank} with score {score:.4f}")
            else:
                print(f"\n✗ Target language '{lang_code}' NOT detected")
                
        except Exception as e:
            print(f"Error during detection: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("WorldAlphabets Language Detection Test")
    print("Testing detection for languages WITH frequency data")
    test_detection_with_freq()
