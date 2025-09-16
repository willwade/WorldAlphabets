/**
 * Lightweight Browser-compatible ES module for WorldAlphabets language detection
 * Uses pre-compiled candidate lists to avoid loading large index files
 */

// Cache for loaded data
let indexCache = null;
let frequencyCache = new Map();

// Pre-compiled candidate lists for common scripts/regions
const SCRIPT_CANDIDATES = {
  // Latin script languages (most common)
  latin: ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'cs', 'sk', 'hr', 'sl', 'et', 'lv', 'lt', 'da', 'sv', 'no', 'fi', 'hu', 'ro', 'bg', 'mk', 'sr', 'bs', 'sq', 'eu', 'ca', 'gl', 'ast', 'oc', 'co', 'fur', 'lij', 'lmo', 'scn', 'vec', 'mt', 'ga', 'gd', 'cy', 'br', 'is', 'fo', 'lb', 'rm'],
  
  // Cyrillic script languages
  cyrillic: ['ru', 'uk', 'bg', 'mk', 'sr', 'bs', 'hr', 'me', 'be', 'kk', 'ky', 'mn', 'tg', 'uz', 'az'],
  
  // Arabic script languages
  arabic: ['ar', 'fa', 'ur', 'ps', 'ckb', 'sd', 'bal'],
  
  // Asian languages
  cjk: ['zh', 'ja', 'ko'],
  devanagari: ['hi', 'ne', 'mr', 'bn', 'gu', 'pa', 'or', 'as', 'mai', 'bho', 'mni'],
  
  // Other scripts
  greek: ['el'],
  hebrew: ['he'],
  thai: ['th'],
  georgian: ['ka'],
  armenian: ['hy'],
  ethiopic: ['am', 'ti', 'tig']
};

// Common languages to always check (high frequency worldwide)
const PRIORITY_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ar', 'hi'];

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
 * Get available language codes
 */
export async function getAvailableCodes() {
  const data = await getIndexData();
  return data.map(item => item.language).sort();
}

/**
 * Export getIndexData for service compatibility
 */
export { getIndexData };

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
 * Detect script type from text to narrow down candidates
 */
function detectScriptType(text) {
  const chars = Array.from(text.normalize('NFKC'));
  const scripts = new Set();
  
  for (const char of chars) {
    const code = char.codePointAt(0);
    
    // Latin (including extended)
    if ((code >= 0x0041 && code <= 0x007A) || 
        (code >= 0x00C0 && code <= 0x024F) ||
        (code >= 0x1E00 && code <= 0x1EFF)) {
      scripts.add('latin');
    }
    // Cyrillic
    else if (code >= 0x0400 && code <= 0x04FF) {
      scripts.add('cyrillic');
    }
    // Arabic
    else if (code >= 0x0600 && code <= 0x06FF) {
      scripts.add('arabic');
    }
    // CJK
    else if ((code >= 0x4E00 && code <= 0x9FFF) ||  // CJK Unified
             (code >= 0x3400 && code <= 0x4DBF) ||  // CJK Extension A
             (code >= 0x3040 && code <= 0x309F) ||  // Hiragana
             (code >= 0x30A0 && code <= 0x30FF) ||  // Katakana
             (code >= 0xAC00 && code <= 0xD7AF)) {  // Hangul
      scripts.add('cjk');
    }
    // Devanagari
    else if (code >= 0x0900 && code <= 0x097F) {
      scripts.add('devanagari');
    }
    // Greek
    else if (code >= 0x0370 && code <= 0x03FF) {
      scripts.add('greek');
    }
    // Hebrew
    else if (code >= 0x0590 && code <= 0x05FF) {
      scripts.add('hebrew');
    }
    // Thai
    else if (code >= 0x0E00 && code <= 0x0E7F) {
      scripts.add('thai');
    }
    // Georgian
    else if (code >= 0x10A0 && code <= 0x10FF) {
      scripts.add('georgian');
    }
    // Armenian
    else if (code >= 0x0530 && code <= 0x058F) {
      scripts.add('armenian');
    }
    // Ethiopic
    else if (code >= 0x1200 && code <= 0x137F) {
      scripts.add('ethiopic');
    }
  }
  
  return Array.from(scripts);
}

/**
 * Get candidate languages using lightweight script detection
 */
async function getCandidateLanguages(text, maxCandidates = 20) {
  console.log('🔍 Getting candidate languages using script detection...');
  
  const scripts = detectScriptType(text);
  console.log('📝 Detected scripts:', scripts);
  
  const candidates = new Set();
  
  // Add priority languages first
  PRIORITY_LANGUAGES.forEach(lang => candidates.add(lang));
  
  // Add script-specific candidates
  for (const script of scripts) {
    const scriptCandidates = SCRIPT_CANDIDATES[script] || [];
    scriptCandidates.forEach(lang => candidates.add(lang));
  }
  
  // Convert to array and limit
  const candidateArray = Array.from(candidates).slice(0, maxCandidates);
  
  console.log(`📋 Selected ${candidateArray.length} candidate languages:`, candidateArray);
  
  return candidateArray;
}

/**
 * Lightweight detect languages function
 */
export async function detectLanguages(text, candidateLangs = null, priors = {}, topk = 3) {
  console.log('🔍 Lightweight detectLanguages called');
  
  // If no candidates provided, use script-based filtering
  if (!candidateLangs) {
    candidateLangs = await getCandidateLanguages(text, 20);
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

  // Process candidates sequentially to avoid overwhelming the browser
  for (const lang of candidateLangs) {
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
      } else {
        // Fallback to character-based detection
        score = 0.03; // Simplified character score
        console.log(`🔤 ${lang}: character-based score = ${score.toFixed(4)}`);
      }
      
      results.push([lang, score]);
    } catch (error) {
      console.error(`❌ Error processing ${lang}:`, error);
      results.push([lang, 0.01]);
    }
  }

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

console.log('📦 Lightweight ES module loaded');
