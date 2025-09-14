/**
 * Test script for enhanced language detection in WebUI
 * Run this in the browser console after the page loads
 */

async function testEnhancedDetection() {
    console.log('🧪 Testing Enhanced Language Detection');
    console.log('=====================================');

    // Test cases: [language_code, text, expected_name, detection_type]
    const testCases = [
        ['ab', 'Аҧсуа бызшәа', 'Abkhazian', 'character-based'],
        ['cop', 'ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ', 'Coptic', 'character-based'],
        ['vai', '𖤍𖤘𖤧𖤃𖤉𖤍', 'Vai', 'character-based'],
        ['gez', 'ግዕዝ', 'Ge\'ez', 'character-based'],
        ['ba', 'Башҡорт теле', 'Bashkir', 'character-based'],
        ['en', 'Hello world this is a test', 'English', 'word-based'],
        ['de', 'Hallo Welt das ist ein Test', 'German', 'word-based'],
        ['fr', 'Bonjour le monde ceci est un test', 'French', 'word-based']
    ];

    let passed = 0;
    let total = testCases.length;

    for (const [langCode, text, expectedName, expectedType] of testCases) {
        console.log(`\n🔍 Testing ${expectedName} (${langCode})`);
        console.log(`Text: "${text}"`);
        console.log(`Expected detection type: ${expectedType}`);

        try {
            // Use the global detection service if available
            let results;
            if (window.languageDetectionService) {
                results = await window.languageDetectionService.detectLanguages(text, { topK: 5 });
            } else {
                console.log('⚠️ Global detection service not found, trying to create one...');
                // Try to import and create the service
                const { default: LanguageDetectionService } = await import('./src/services/languageDetectionService.js');
                const service = new LanguageDetectionService();
                await service.initialize();
                results = await service.detectLanguages(text, { topK: 5 });
            }

            if (results && results.length > 0) {
                const topResult = results[0];
                const isCorrect = topResult.language === langCode;
                const detectionType = topResult.detectionType || 'unknown';

                console.log(`📊 Results (top 3):`);
                results.slice(0, 3).forEach((result, index) => {
                    const marker = result.language === langCode ? '👉' : '  ';
                    console.log(`${marker} ${index + 1}. ${result.languageName || result.language} (${result.language}): ${(result.confidence * 100).toFixed(2)}% [${result.detectionType || 'unknown'}]`);
                });

                if (isCorrect) {
                    console.log(`✅ SUCCESS: ${expectedName} detected at rank 1 using ${detectionType} detection`);
                    passed++;
                } else {
                    const targetRank = results.findIndex(r => r.language === langCode) + 1;
                    if (targetRank > 0) {
                        console.log(`⚠️ PARTIAL: ${expectedName} detected at rank ${targetRank} using ${detectionType} detection`);
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
}

// Make the test function available globally
window.testEnhancedDetection = testEnhancedDetection;

console.log('🧪 Enhanced detection test loaded. Run testEnhancedDetection() to start testing.');
