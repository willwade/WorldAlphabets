#!/usr/bin/env node

/**
 * Performance test for language detection
 * Measures baseline performance before optimizations
 */

const { performance } = require('perf_hooks');
const fs = require('fs');
const path = require('path');

// Test texts in different languages
const testTexts = [
  {
    text: "Hello world, this is a test in English. The quick brown fox jumps over the lazy dog.",
    expected: "en",
    name: "English"
  },
  {
    text: "Bonjour le monde, ceci est un test en français. Le renard brun et rapide saute par-dessus le chien paresseux.",
    expected: "fr", 
    name: "French"
  },
  {
    text: "Hola mundo, esta es una prueba en español. El zorro marrón rápido salta sobre el perro perezoso.",
    expected: "es",
    name: "Spanish"
  },
  {
    text: "Hallo Welt, das ist ein Test auf Deutsch. Der schnelle braune Fuchs springt über den faulen Hund.",
    expected: "de",
    name: "German"
  },
  {
    text: "Привет мир, это тест на русском языке. Быстрая коричневая лиса прыгает через ленивую собаку.",
    expected: "ru",
    name: "Russian"
  },
  {
    text: "你好世界，这是中文测试。快速的棕色狐狸跳过懒惰的狗。",
    expected: "zh",
    name: "Chinese"
  },
  {
    text: "こんにちは世界、これは日本語のテストです。素早い茶色のキツネが怠惰な犬を飛び越えます。",
    expected: "ja",
    name: "Japanese"
  }
];

// Import the Node.js detection function
async function testNodeJSPerformance() {
  console.log('🔍 Testing Node.js Language Detection Performance\n');

  // Import the CommonJS module
  const { detectLanguages } = require('./index.js');
  
  // Get available languages from index
  const indexPath = path.join(process.cwd(), 'data', 'index.json');
  const indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  const candidateLanguages = [...new Set(indexData.map(item => item.language))];
  
  console.log(`Testing with ${candidateLanguages.length} candidate languages\n`);
  
  const results = [];
  
  for (const testCase of testTexts) {
    console.log(`Testing ${testCase.name}...`);
    
    const startTime = performance.now();
    const detectionResults = detectLanguages(testCase.text, candidateLanguages, {}, 5);
    const endTime = performance.now();
    
    const duration = endTime - startTime;
    const topResult = detectionResults[0];
    const isCorrect = topResult && topResult[0] === testCase.expected;
    
    console.log(`  Duration: ${duration.toFixed(2)}ms`);
    console.log(`  Top result: ${topResult ? topResult[0] : 'none'} (${topResult ? (topResult[1] * 100).toFixed(1) : 0}%)`);
    console.log(`  Correct: ${isCorrect ? '✅' : '❌'}`);
    console.log('');
    
    results.push({
      name: testCase.name,
      duration,
      correct: isCorrect,
      topResult: topResult ? topResult[0] : null,
      confidence: topResult ? topResult[1] : 0
    });
  }
  
  // Summary statistics
  const totalTime = results.reduce((sum, r) => sum + r.duration, 0);
  const avgTime = totalTime / results.length;
  const correctCount = results.filter(r => r.correct).length;
  const accuracy = (correctCount / results.length) * 100;
  
  console.log('📊 Summary Statistics:');
  console.log(`  Total time: ${totalTime.toFixed(2)}ms`);
  console.log(`  Average time per detection: ${avgTime.toFixed(2)}ms`);
  console.log(`  Accuracy: ${accuracy.toFixed(1)}% (${correctCount}/${results.length})`);
  console.log(`  Fastest: ${Math.min(...results.map(r => r.duration)).toFixed(2)}ms`);
  console.log(`  Slowest: ${Math.max(...results.map(r => r.duration)).toFixed(2)}ms`);
  
  return {
    totalTime,
    avgTime,
    accuracy,
    results
  };
}

// Run the test
testNodeJSPerformance().catch(console.error);
