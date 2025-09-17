/**
 * Simplified Browser-compatible ES module for WorldAlphabets language detection
 * No caching, simplified logic for debugging
 */

/**
 * Load and return index data
 */
async function getIndexData() {
  const response = await fetch('/WorldAlphabets/data/index.json');
  if (!response.ok) throw new Error('Failed to load index data');
  return await response.json();
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
 * Load frequency data for a language (no caching)
 */
async function loadRankData(lang) {
  try {
    const response = await fetch(`/WorldAlphabets/data/freq/top1000/${lang}.txt`);
    if (!response.ok) {
      return { mode: 'word', ranks: new Map() };
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
    
    return { mode, ranks };
  } catch (error) {
    return { mode: 'word', ranks: new Map() };
  }
}

/**
 * Tokenize text into words
 */
function tokenizeWords(text) {
  return new Set(text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || []);
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
 * Simplified detect languages function
 */
export async function detectLanguages(text, candidateLangs, priors = {}, topk = 3) {
  console.log('🔍 detectLanguages called with:', { text, candidateLangs, topk });
  
  // Validate input
  if (!candidateLangs || !Array.isArray(candidateLangs)) {
    throw new Error(`candidateLangs must be an array, got: ${typeof candidateLangs}`);
  }
  
  if (candidateLangs.length === 0) {
    throw new Error('candidateLangs cannot be empty');
  }
  
  console.log('✅ Input validation passed');
  
  const wordTokens = tokenizeWords(text);
  console.log('📝 Word tokens:', Array.from(wordTokens));
  
  const results = [];
  const PRIOR_WEIGHT = 0.65;
  const FREQ_WEIGHT = 0.35;

  for (const lang of candidateLangs) {
    console.log(`🔍 Processing language: ${lang}`);
    
    try {
      const data = await loadRankData(lang);
      console.log(`📊 ${lang}: loaded ${data.ranks.size} words, mode: ${data.mode}`);
      
      let wordOverlap = 0;
      if (data.ranks.size > 0 && wordTokens.size > 0) {
        wordOverlap = overlap(wordTokens, data.ranks);
        wordOverlap /= Math.sqrt(wordTokens.size + 3);
        console.log(`📈 ${lang}: overlap = ${wordOverlap.toFixed(4)}`);
      }

      const prior = priors[lang] || 0;
      let score = PRIOR_WEIGHT * prior + FREQ_WEIGHT * wordOverlap;
      
      // Add word-based boost if we have good word coverage
      if (score > 0.05) {
        score += 0.1; // Word-based boost
        console.log(`🎯 ${lang}: word-based score = ${score.toFixed(4)} (boosted)`);
      } else {
        // Fallback character-based score (simplified)
        score = 0.03;
        console.log(`🔤 ${lang}: character-based score = ${score.toFixed(4)}`);
      }
      
      results.push([lang, score]);
      
    } catch (error) {
      console.error(`❌ Error processing ${lang}:`, error);
      results.push([lang, 0.01]); // Minimal score for failed languages
    }
  }

  // Sort by score (descending)
  results.sort((a, b) => b[1] - a[1]);
  
  console.log('🏆 Final results:', results);
  
  return results.slice(0, topk);
}

console.log('📦 Simplified ES module loaded');
