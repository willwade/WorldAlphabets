#!/usr/bin/env python3
"""
Debug language detection to understand why some languages fail.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets.detect import detect_languages, _tokenize_words, _load_rank_data, _overlap, DEFAULT_FREQ_DIR

def debug_detection(text, lang_code):
    """Debug detection for a specific language."""
    print(f"\n{'='*60}")
    print(f"Debugging detection for: {lang_code}")
    print(f"Text: '{text}'")
    print(f"{'='*60}")
    
    # Tokenize the text
    word_tokens = _tokenize_words(text)
    print(f"Word tokens: {word_tokens}")
    
    # Load frequency data for the language
    freq_dir = Path(str(DEFAULT_FREQ_DIR))
    data = _load_rank_data(lang_code, freq_dir)
    print(f"Frequency data mode: {data.mode}")
    print(f"Frequency data size: {len(data.ranks)}")
    
    if data.ranks:
        print(f"First 10 frequency words: {list(data.ranks.keys())[:10]}")
        
        # Check overlap
        overlap_score = _overlap(word_tokens, data.ranks)
        print(f"Raw overlap score: {overlap_score}")
        
        # Normalized overlap
        if word_tokens:
            normalized_overlap = overlap_score / (len(word_tokens) + 3) ** 0.5
            print(f"Normalized overlap: {normalized_overlap}")
            
            # Final score (frequency weight only, no priors)
            FREQ_WEIGHT = 0.35
            final_score = FREQ_WEIGHT * normalized_overlap
            print(f"Final score (freq_weight * normalized): {final_score}")
            print("Threshold: 0.05")
            print(f"Above threshold: {final_score > 0.05}")
            
            # Show which tokens matched
            matched_tokens = []
            for token in word_tokens:
                if token in data.ranks:
                    rank = data.ranks[token]
                    matched_tokens.append((token, rank))
            
            if matched_tokens:
                print(f"Matched tokens: {matched_tokens}")
            else:
                print("No tokens matched!")
        else:
            print("No word tokens found!")
    else:
        print("No frequency data loaded!")

def main():
    print("Language Detection Debug Tool")
    
    # Test cases that failed
    test_cases = [
        ("de", "Hallo Welt das ist ein Test"),
        ("pl", "Żółć gęś jaźń"),
        ("en", "Hello world this is a test"),  # This one worked
    ]
    
    for lang_code, text in test_cases:
        debug_detection(text, lang_code)
        
        # Also run the actual detection
        try:
            results = detect_languages(text, candidate_langs=[lang_code], topk=1)
            print(f"Actual detection result: {results}")
        except Exception as e:
            print(f"Detection error: {e}")

if __name__ == "__main__":
    main()
