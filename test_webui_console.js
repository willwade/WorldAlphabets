/**
 * Console test for WebUI enhanced language detection
 * 
 * Instructions:
 * 1. Open http://localhost:5173/WorldAlphabets/ in browser
 * 2. Open browser console (F12)
 * 3. Copy and paste this entire script
 * 4. Run: testWebUIDetection()
 */

async function testWebUIDetection() {
    console.log('🧪 Testing WebUI Enhanced Language Detection');
    console.log('===========================================');

    // Test cases: [language_code, text, expected_name, expected_type]
    const testCases = [
        ['ab', 'Аҧсуа бызшәа', 'Abkhazian', 'character-based'],
        ['cop', 'ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ', 'Coptic', 'character-based'],
        ['ba', 'Башҡорт теле', 'Bashkir', 'character-based'],
        ['en', 'Hello world this is a test', 'English', 'word-based'],
        ['de', 'Hallo Welt das ist ein Test', 'German', 'word-based'],
        ['fr', 'Bonjour le monde', 'French', 'word-based']
    ];

    try {
        // Create and initialize the detection service
        console.log('📡 Initializing detection service...');
        
        // Import the service class
        const module = await import('./src/services/languageDetectionService.js');
        const LanguageDetectionService = module.default;
        
        const service = new LanguageDetectionService();
        await service.initialize();
        
        console.log(`✅ Service initialized with ${service.getAvailableLanguages().length} languages`);

        let passed = 0;
        let total = testCases.length;

        for (const [langCode, text, expectedName, expectedType] of testCases) {
            console.log(`\n🔍 Testing ${expectedName} (${langCode})`);
            console.log(`Text: "${text}"`);
            console.log(`Expected: ${expectedType} detection`);

            try {
                const results = await service.detectLanguages(text, { 
                    candidateLanguages: [langCode, 'en', 'de', 'fr', 'ru', 'es'], 
                    topK: 5 
                });

                if (results && results.length > 0) {
                    console.log(`📊 Top 3 results:`);
                    results.slice(0, 3).forEach((result, index) => {
                        const marker = result.language === langCode ? '👉' : '  ';
                        const confidence = (result.confidence * 100).toFixed(2);
                        const detectionType = result.detectionType || 'unknown';
                        console.log(`${marker} ${index + 1}. ${result.languageName || result.language} (${result.language}): ${confidence}% [${detectionType}]`);
                    });

                    const topResult = results[0];
                    if (topResult.language === langCode) {
                        console.log(`✅ SUCCESS: ${expectedName} detected at rank 1`);
                        passed++;
                    } else {
                        const targetRank = results.findIndex(r => r.language === langCode) + 1;
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
                console.error(`❌ ERROR testing ${expectedName}:`, error);
            }

            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        console.log(`\n📈 Test Summary`);
        console.log(`===============`);
        console.log(`Passed: ${passed}/${total} (${(passed/total*100).toFixed(1)}%)`);
        
        if (passed === total) {
            console.log(`🎉 All tests passed! Enhanced detection is working correctly.`);
        } else if (passed > 0) {
            console.log(`⚠️ Some tests passed. Enhanced detection is partially working.`);
        } else {
            console.log(`❌ No tests passed. Enhanced detection needs debugging.`);
        }

        return { passed, total, success: passed === total };

    } catch (error) {
        console.error('❌ Failed to initialize or run tests:', error);
        return { passed: 0, total: testCases.length, success: false };
    }
}

// Test individual detection
async function testSingleDetection(text, expectedLang, expectedName) {
    try {
        const module = await import('./src/services/languageDetectionService.js');
        const LanguageDetectionService = module.default;
        
        const service = new LanguageDetectionService();
        await service.initialize();
        
        console.log(`🔍 Testing: "${text}"`);
        const results = await service.detectLanguages(text, { topK: 5 });
        
        console.log('Results:', results.map(r => `${r.language}: ${(r.confidence*100).toFixed(2)}% [${r.detectionType}]`));
        
        return results;
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

// Make functions available globally
window.testWebUIDetection = testWebUIDetection;
window.testSingleDetection = testSingleDetection;

console.log('🧪 WebUI detection test loaded!');
console.log('Run: testWebUIDetection() - Full test suite');
console.log('Run: testSingleDetection("text", "lang", "name") - Single test');
