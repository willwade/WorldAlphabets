#!/usr/bin/env python3
"""
Final test of enhanced language detection system.
Tests both word-based and character-based detection across multiple languages.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from worldalphabets.detect import detect_languages

def test_enhanced_detection():
    """Test the enhanced detection system with various languages."""
    
    print("🧪 Testing Enhanced Language Detection System")
    print("=" * 50)
    
    # Test cases: (language_code, text, expected_name, expected_detection_type)
    test_cases = [
        # Character-based detection (languages without frequency data)
        ('ab', 'Аҧсуа бызшәа', 'Abkhazian', 'character-based'),
        ('cop', 'ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ', 'Coptic', 'character-based'),
        ('vai', '𖤍𖤘𖤧𖤃𖤉𖤍', 'Vai', 'character-based'),
        ('gez', 'ግዕዝ', 'Ge\'ez', 'character-based'),
        ('ba', 'Башҡорт теле', 'Bashkir', 'character-based'),
        
        # Word-based detection (languages with frequency data)
        ('en', 'Hello world this is a test', 'English', 'word-based'),
        ('de', 'Hallo Welt das ist ein Test', 'German', 'word-based'),
        ('fr', 'Bonjour le monde ceci est un test', 'French', 'word-based'),
        ('es', 'Hola mundo esto es una prueba', 'Spanish', 'word-based'),
        ('ru', 'Привет мир это тест', 'Russian', 'word-based'),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for lang_code, text, expected_name, expected_type in test_cases:
        print(f"\n🔍 Testing {expected_name} ({lang_code})")
        print(f"Text: '{text}'")
        print(f"Expected: {expected_type} detection")
        
        try:
            # Test with a reasonable set of candidate languages
            candidates = [lang_code, 'en', 'de', 'fr', 'ru', 'es', 'ar', 'zh']
            results = detect_languages(text, candidate_langs=candidates, topk=5)
            
            if results:
                print("📊 Top 3 results:")
                for i, (lang, score) in enumerate(results[:3]):
                    marker = "👉" if lang == lang_code else "  "
                    print(f"{marker} {i+1}. {lang}: {score:.4f}")
                
                top_lang, top_score = results[0]
                if top_lang == lang_code:
                    print(f"✅ SUCCESS: {expected_name} detected at rank 1 (score: {top_score:.4f})")
                    passed += 1
                else:
                    # Check if target language is in results
                    target_rank = None
                    for i, (lang, score) in enumerate(results):
                        if lang == lang_code:
                            target_rank = i + 1
                            break
                    
                    if target_rank:
                        print(f"⚠️ PARTIAL: {expected_name} detected at rank {target_rank}")
                    else:
                        print(f"❌ FAILED: {expected_name} not detected")
            else:
                print("❌ FAILED: No results returned")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n📈 Test Summary")
    print("=" * 20)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced detection is working correctly.")
    elif passed > 0:
        print("⚠️ Some tests passed. Enhanced detection is partially working.")
    else:
        print("❌ No tests passed. Enhanced detection needs debugging.")
    
    return passed, total

def test_coverage():
    """Test detection coverage by checking available languages."""
    
    print("\n📊 Testing Detection Coverage")
    print("=" * 30)
    
    try:
        from worldalphabets import get_available_codes
        all_codes = get_available_codes()
        print(f"Total languages with alphabet data: {len(all_codes)}")
        
        # Test a sample of languages to see detection coverage
        sample_languages = ['ab', 'cop', 'vai', 'gez', 'ba', 'en', 'de', 'fr', 'zh', 'ar']
        detectable = 0
        
        for lang in sample_languages:
            if lang in all_codes:
                # Try to detect with a simple test
                try:
                    detect_languages("test", candidate_langs=[lang], topk=1)
                    # Even if it doesn't detect (due to simple text), 
                    # the fact that it doesn't error means the language is supported
                    detectable += 1
                except Exception:
                    pass
        
        print(f"Sample detection test: {detectable}/{len(sample_languages)} languages supported")
        
    except Exception as e:
        print(f"❌ Coverage test error: {e}")

if __name__ == "__main__":
    passed, total = test_enhanced_detection()
    test_coverage()
    
    print(f"\n🏁 Final Result: {passed}/{total} tests passed")
    sys.exit(0 if passed == total else 1)
