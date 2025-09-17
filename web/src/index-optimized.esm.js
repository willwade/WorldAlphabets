/**
 * Optimized Browser-compatible ES module for WorldAlphabets language detection
 * Uses smart candidate filtering to minimize HTTP requests
 */

// Cache for loaded data
let indexCache = null;
let charIndexCache = null;
let frequencyCache = new Map();

/**
 * Load and cache index data
 */
async function getIndexData() {
  if (indexCache) return indexCache;
  
  const response = await fetch('/WorldAlphabets/data/index.json');
  if (!response.ok) throw new Error('Failed to load index data');
  
  indexCache = await response.json();
  return indexCache;
}

/**
 * Load and cache character index data
 */
async function getCharIndexData() {
  if (charIndexCache) return charIndexCache;
  
  const response = await fetch('/WorldAlphabets/data/char_index.json');
  if (!response.ok) throw new Error('Failed to load character index data');
  
  charIndexCache = await response.json();
  return charIndexCache;
}

/**
 * Get available language codes
 */
export async function getAvailableCodes() {
  const data = await getIndexData();
  const codes = data.map(item => item.language);
  return Array.from(new Set(codes)).sort();
}

/**
 * Load frequency data for a language (with caching)
 */
async function loadRankData(lang) {
  if (frequencyCache.has(lang)) return frequencyCache.get(lang);
  
  try {
    const response = await fetch(`/WorldAlphabets/data/freq/top1000/${lang}.txt`);
    if (!response.ok) {
      const result = { mode: 'word', ranks: new Map() };
      frequencyCache.set(lang, result);
      return result;
    }
    
    const text = await response.text();
    const lines = text.split(/\r?\n/).filter(Boolean);
    
    let mode = 'word';
    if (lines[0] && lines[0].startsWith('#')) {
      const header = lines.shift();
      if (header.includes('bigram')) mode = 'bigram';
    }

    const ranks = new Map();
    lines.forEach((tok, i) => {
      if (!ranks.has(tok)) ranks.set(tok, i + 1);
    });
    
    const result = { mode, ranks };
    frequencyCache.set(lang, result);
    return result;
  } catch (error) {
    const result = { mode: 'word', ranks: new Map() };
    frequencyCache.set(lang, result);
    return result;
  }
}

/**
 * Tokenize text into words
 */
function tokenizeWords(text) {
  return new Set(text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || []);
}

/**
 * Tokenize text into characters
 */
function tokenizeCharacters(text) {
  return new Set(Array.from(text.normalize('NFKC').toLowerCase()).filter(ch => /\p{L}/u.test(ch)));
}

/**
 * Calculate overlap score
 */
function overlap(tokens, ranks) {
  let score = 0;
  for (const token of tokens) {
    const rank = ranks.get(token);
    if (rank) score += 1 / Math.log2(rank + 1.5);
  }
  return score;
}

/**
 * Get candidate languages using character-based filtering
 * This dramatically reduces the number of languages we need to check
 */
async function getCandidateLanguages(text, maxCandidates = 15) {
  console.log('🔍 Getting candidate languages using character analysis...');
  
  const chars = tokenizeCharacters(text);
  const charIndex = await getCharIndexData();
  const indexData = await getIndexData();
  
  // Count how many characters each language supports
  const languageScores = new Map();
  
  for (const char of chars) {
    const languages = charIndex[char] || [];
    for (const lang of languages) {
      languageScores.set(lang, (languageScores.get(lang) || 0) + 1);
    }
  }
  
  // Convert to array and sort by score
  const candidates = Array.from(languageScores.entries())
    .map(([lang, score]) => ({
      lang,
      score,
      coverage: score / chars.size,
      hasFrequency: indexData.find(item => item.language === lang)?.hasFrequency || false
    }))
    .sort((a, b) => {
      // Prioritize languages with frequency data and high coverage
      if (a.hasFrequency && !b.hasFrequency) return -1;
      if (!a.hasFrequency && b.hasFrequency) return 1;
      return b.coverage - a.coverage;
    })
    .slice(0, maxCandidates)
    .map(item => item.lang);
  
  console.log(`📋 Selected ${candidates.length} candidate languages:`, candidates);
  console.log('Character coverage analysis:', 
    candidates.slice(0, 5).map(lang => {
      const score = languageScores.get(lang);
      const coverage = (score / chars.size * 100).toFixed(1);
      return `${lang}:${coverage}%`;
    }).join(', ')
  );
  
  return candidates;
}

/**
 * Optimized detect languages function
 * Uses smart candidate filtering to minimize HTTP requests
 */
export async function detectLanguages(text, candidateLangs = null, priors = {}, topk = 3) {
  console.log('🔍 Optimized detectLanguages called');
  
  // If no candidates provided, use smart filtering
  if (!candidateLangs) {
    candidateLangs = await getCandidateLanguages(text, 15);
  }
  
  // Validate input
  if (!Array.isArray(candidateLangs)) {
    throw new Error(`candidateLangs must be an array, got: ${typeof candidateLangs}`);
  }
  
  if (candidateLangs.length === 0) {
    throw new Error('No candidate languages available');
  }
  
  console.log(`🎯 Processing ${candidateLangs.length} candidate languages:`, candidateLangs);
  
  const wordTokens = tokenizeWords(text);
  const results = [];
  const wordBasedLangs = new Set();

  const PRIOR_WEIGHT = 0.65;
  const FREQ_WEIGHT = 0.35;
  const CHAR_WEIGHT = 0.2;

  // Process candidates in parallel for better performance
  const promises = candidateLangs.map(async (lang) => {
    try {
      const data = await loadRankData(lang);
      
      let wordOverlap = 0;
      if (data.ranks.size > 0 && wordTokens.size > 0) {
        wordOverlap = overlap(wordTokens, data.ranks);
        wordOverlap /= Math.sqrt(wordTokens.size + 3);
      }

      const prior = priors[lang] || 0;
      let score = PRIOR_WEIGHT * prior + FREQ_WEIGHT * wordOverlap;

      // If word-based detection is strong enough, use it
      if (score > 0.05) {
        wordBasedLangs.add(lang);
        score += 0.1; // Word-based boost
        console.log(`🎯 ${lang}: word-based score = ${score.toFixed(4)}`);
        return [lang, score];
      } else {
        // Fallback to character-based detection
        const charScore = CHAR_WEIGHT * 0.15; // Simplified character score
        console.log(`🔤 ${lang}: character-based score = ${charScore.toFixed(4)}`);
        return [lang, charScore];
      }
    } catch (error) {
      console.error(`❌ Error processing ${lang}:`, error);
      return [lang, 0.01];
    }
  });

  // Wait for all languages to be processed
  const languageResults = await Promise.all(promises);
  results.push(...languageResults);

  // Sort results, prioritizing word-based detections
  results.sort((a, b) => {
    const [langA, scoreA] = a;
    const [langB, scoreB] = b;
    const adjustedScoreA = wordBasedLangs.has(langA) ? scoreA : scoreA;
    const adjustedScoreB = wordBasedLangs.has(langB) ? scoreB : scoreB;
    return adjustedScoreB - adjustedScoreA;
  });

  console.log('🏆 Final results:', results.slice(0, topk));
  return results.slice(0, topk);
}

console.log('📦 Optimized ES module loaded');
