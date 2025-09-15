#!/usr/bin/env python3
"""
Test with Bashkir which should have distinctive characters.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from enhanced_detect import enhanced_detect_languages
from worldalphabets.detect import detect_languages

def test_bashkir():
    # Bashkir text with distinctive characters
    text = "Башҡорт теле"  # "Bashkir language" in Bashkir
    candidates = ["ba", "ru", "tt", "kk"]  # Bashkir, Russian, Tatar, Kazakh
    
    print("Testing Bashkir detection")
    print(f"Text: '{text}'")
    print(f"Candidates: {candidates}")
    print()
    
    # Test original method
    try:
        original_results = detect_languages(text, candidate_langs=candidates, topk=len(candidates))
        print(f"Original method: {original_results}")
    except Exception as e:
        print(f"Original method error: {e}")
    
    # Test enhanced method
    try:
        enhanced_results = enhanced_detect_languages(text, candidates, topk=len(candidates))
        print(f"Enhanced method: {enhanced_results}")
        
        # Check if target language was detected
        detected_langs = [lang for lang, score in enhanced_results]
        if "ba" in detected_langs:
            rank = detected_langs.index("ba") + 1
            score = enhanced_results[detected_langs.index("ba")][1]
            print(f"✓ Target 'ba' detected at rank {rank} with score {score:.4f}")
        else:
            print("✗ Target 'ba' NOT detected")
            
    except Exception as e:
        print(f"Enhanced method error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bashkir()
