#!/usr/bin/env node
/**
 * Debug Node.js language detection
 */

const { detectLanguages } = require('./index.js');
const fs = require('fs');
const path = require('path');

function debugDetection(text, langCode) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Debugging detection for: ${langCode}`);
    console.log(`Text: '${text}'`);
    console.log(`${'='.repeat(60)}`);
    
    // Check if frequency file exists
    const DEFAULT_FREQ_DIR = path.join(__dirname, 'data', 'freq', 'top200');
    const freqFile = path.join(DEFAULT_FREQ_DIR, `${langCode}.txt`);
    
    console.log(`Frequency file path: ${freqFile}`);
    console.log(`Frequency file exists: ${fs.existsSync(freqFile)}`);
    
    if (fs.existsSync(freqFile)) {
        try {
            const content = fs.readFileSync(freqFile, 'utf8');
            const lines = content.split(/\r?\n/).filter(Boolean);
            console.log(`Frequency file lines: ${lines.length}`);
            console.log(`First 5 words: ${lines.slice(0, 5)}`);
        } catch (error) {
            console.log(`Error reading frequency file: ${error.message}`);
        }
    }
    
    // Test detection
    try {
        const results = detectLanguages(text, [langCode], {}, 1);
        console.log(`Detection results: ${JSON.stringify(results)}`);
    } catch (error) {
        console.log(`Detection error: ${error.message}`);
    }
}

async function main() {
    console.log("Node.js Language Detection Debug Tool");
    
    // Test cases
    const testCases = [
        ["de", "Hallo Welt das ist ein Test"],
        ["pl", "Żółć gęś jaźń"],
        ["en", "Hello world this is a test"],
    ];
    
    for (const [langCode, text] of testCases) {
        debugDetection(text, langCode);
    }
}

main().catch(console.error);
