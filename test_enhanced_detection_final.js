#!/usr/bin/env node
/**
 * Final test of enhanced language detection system for Node.js.
 * Tests both word-based and character-based detection across multiple languages.
 */

const { detectLanguages, getAvailableCodes } = require('./index.js');

async function testEnhancedDetection() {
    console.log('🧪 Testing Enhanced Language Detection System (Node.js)');
    console.log('='.repeat(55));
    
    // Test cases: [language_code, text, expected_name, expected_detection_type]
    const testCases = [
        // Character-based detection (languages without frequency data)
        ['ab', 'Аҧсуа бызшәа', 'Abkhazian', 'character-based'],
        ['cop', 'ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ', 'Coptic', 'character-based'],
        ['vai', '𖤍𖤘𖤧𖤃𖤉𖤍', 'Vai', 'character-based'],
        ['gez', 'ግዕዝ', 'Ge\'ez', 'character-based'],
        ['ba', 'Башҡорт теле', 'Bashkir', 'character-based'],
        
        // Word-based detection (languages with frequency data)
        ['en', 'Hello world this is a test', 'English', 'word-based'],
        ['de', 'Hallo Welt das ist ein Test', 'German', 'word-based'],
        ['fr', 'Bonjour le monde ceci est un test', 'French', 'word-based'],
        ['es', 'Hola mundo esto es una prueba', 'Spanish', 'word-based'],
        ['ru', 'Привет мир это тест', 'Russian', 'word-based'],
    ];
    
    let passed = 0;
    const total = testCases.length;
    
    for (const [langCode, text, expectedName, expectedType] of testCases) {
        console.log(`\n🔍 Testing ${expectedName} (${langCode})`);
        console.log(`Text: '${text}'`);
        console.log(`Expected: ${expectedType} detection`);
        
        try {
            // Test with a reasonable set of candidate languages
            const candidates = [langCode, 'en', 'de', 'fr', 'ru', 'es', 'ar', 'zh'];
            const results = detectLanguages(text, candidates, {}, 5);
            
            if (results && results.length > 0) {
                console.log(`📊 Top 3 results:`);
                results.slice(0, 3).forEach(([lang, score], index) => {
                    const marker = lang === langCode ? '👉' : '  ';
                    console.log(`${marker} ${index + 1}. ${lang}: ${score.toFixed(4)}`);
                });
                
                const [topLang, topScore] = results[0];
                if (topLang === langCode) {
                    console.log(`✅ SUCCESS: ${expectedName} detected at rank 1 (score: ${topScore.toFixed(4)})`);
                    passed++;
                } else {
                    // Check if target language is in results
                    const targetRank = results.findIndex(([lang]) => lang === langCode) + 1;
                    
                    if (targetRank > 0) {
                        console.log(`⚠️ PARTIAL: ${expectedName} detected at rank ${targetRank}`);
                    } else {
                        console.log(`❌ FAILED: ${expectedName} not detected`);
                    }
                }
            } else {
                console.log(`❌ FAILED: No results returned`);
            }
                
        } catch (error) {
            console.error(`❌ ERROR: ${error.message}`);
        }
    }
    
    console.log(`\n📈 Test Summary`);
    console.log('='.repeat(20));
    console.log(`Passed: ${passed}/${total} (${(passed/total*100).toFixed(1)}%)`);
    
    if (passed === total) {
        console.log('🎉 All tests passed! Enhanced detection is working correctly.');
    } else if (passed > 0) {
        console.log('⚠️ Some tests passed. Enhanced detection is partially working.');
    } else {
        console.log('❌ No tests passed. Enhanced detection needs debugging.');
    }
    
    return { passed, total };
}

function testCoverage() {
    console.log(`\n📊 Testing Detection Coverage`);
    console.log('='.repeat(30));
    
    try {
        const allCodes = getAvailableCodes();
        console.log(`Total languages with alphabet data: ${allCodes ? allCodes.length : 'undefined'}`);
        
        // Test a sample of languages to see detection coverage
        const sampleLanguages = ['ab', 'cop', 'vai', 'gez', 'ba', 'en', 'de', 'fr', 'zh', 'ar'];
        let detectable = 0;
        
        for (const lang of sampleLanguages) {
            if (allCodes && allCodes.includes(lang)) {
                // Try to detect with a simple test
                try {
                    const results = detectLanguages('test', [lang], {}, 1);
                    // Even if it doesn't detect (due to simple text), 
                    // the fact that it doesn't error means the language is supported
                    detectable++;
                } catch (error) {
                    // Language not supported
                }
            }
        }
        
        console.log(`Sample detection test: ${detectable}/${sampleLanguages.length} languages supported`);
        
    } catch (error) {
        console.error(`❌ Coverage test error: ${error.message}`);
    }
}

async function main() {
    const { passed, total } = await testEnhancedDetection();
    testCoverage();
    
    console.log(`\n🏁 Final Result: ${passed}/${total} tests passed`);
    process.exit(passed === total ? 0 : 1);
}

if (require.main === module) {
    main().catch(console.error);
}
