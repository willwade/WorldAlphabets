#!/usr/bin/env node
/**
 * Test language detection for languages without frequency data in Node.js
 */

const { detectLanguages, getAvailableCodes } = require('./index.js');
const fs = require('fs');
const path = require('path');

async function getLanguagesWithoutFreqData() {
    // Get all available language codes from alphabet data
    const allCodes = await getAvailableCodes();
    
    // Get languages with frequency data
    const freqDir = path.join(__dirname, 'data', 'freq', 'top200');
    const freqCodes = new Set();
    
    if (fs.existsSync(freqDir)) {
        const freqFiles = fs.readdirSync(freqDir).filter(f => f.endsWith('.txt'));
        freqFiles.forEach(file => {
            freqCodes.add(path.basename(file, '.txt'));
        });
    }
    
    // Find languages without frequency data
    const withoutFreq = allCodes.filter(code => !freqCodes.has(code));
    
    console.log(`Total languages with alphabet data: ${allCodes.length}`);
    console.log(`Languages with frequency data: ${freqCodes.size}`);
    console.log(`Languages WITHOUT frequency data: ${withoutFreq.length}`);
    console.log(`\nFirst 20 languages without frequency data: ${withoutFreq.slice(0, 20)}`);
    
    return withoutFreq;
}

async function testDetectionWithoutFreq(testLang, testText, candidateLangs = null) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Testing detection for language: ${testLang}`);
    console.log(`Test text: '${testText}'`);
    console.log(`${'='.repeat(60)}`);
    
    if (candidateLangs === null) {
        // Use a small set of candidates including the test language
        candidateLangs = [testLang, 'en', 'es', 'fr', 'de', 'it'];
    }
    
    console.log(`Candidate languages: ${candidateLangs}`);
    
    try {
        const results = detectLanguages(testText, candidateLangs, {}, candidateLangs.length);
        
        console.log(`\nDetection results:`);
        if (results.length > 0) {
            results.forEach((result, i) => {
                console.log(`  ${i + 1}. ${result[0]}: ${result[1].toFixed(4)}`);
            });
        } else {
            console.log("  No languages detected (all scores below threshold)");
        }
        
        // Check if our target language was detected
        const detectedLangs = results.map(r => r[0]);
        if (detectedLangs.includes(testLang)) {
            const rank = detectedLangs.indexOf(testLang) + 1;
            const score = results[detectedLangs.indexOf(testLang)][1];
            console.log(`\n✓ Target language '${testLang}' detected at rank ${rank} with score ${score.toFixed(4)}`);
        } else {
            console.log(`\n✗ Target language '${testLang}' NOT detected`);
        }
        
    } catch (error) {
        console.log(`Error during detection: ${error.message}`);
        console.error(error);
    }
}

async function main() {
    console.log("WorldAlphabets Language Detection Test (Node.js)");
    console.log("Testing detection for languages without frequency data");
    
    // Find languages without frequency data
    const withoutFreq = await getLanguagesWithoutFreqData();
    
    if (withoutFreq.length === 0) {
        console.log("All languages have frequency data!");
        return;
    }
    
    // Test a few specific languages without frequency data
    const testCases = [
        ["ab", "Аҧсуа бызшәа"],   // Abkhazian - Cyrillic script
        ["cop", "ⲧⲙⲛⲧⲣⲙⲛⲕⲏⲙⲉ"],  // Coptic - distinctive script
        ["gez", "ግዕዝ"],           // Ge'ez - Ethiopic script
        ["vai", "ꕙꔤ"],            // Vai - distinctive script
    ];
    
    for (const [langCode, sampleText] of testCases) {
        if (withoutFreq.includes(langCode)) {
            await testDetectionWithoutFreq(langCode, sampleText);
        } else {
            console.log(`\nSkipping ${langCode} - it has frequency data`);
        }
    }
    
    // Test with a broader candidate set for one case
    if (withoutFreq.includes("ab")) {
        console.log(`\n${'='.repeat(60)}`);
        console.log("Testing Abkhazian with broader candidate set");
        console.log(`${'='.repeat(60)}`);
        
        // Include other Cyrillic languages as candidates
        const cyrillicCandidates = ["ab", "ru", "bg", "mk", "sr", "uk", "be"];
        await testDetectionWithoutFreq("ab", "Аҧсуа бызшәа", cyrillicCandidates);
    }
}

main().catch(console.error);
