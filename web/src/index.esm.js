/**
 * WorldAlphabets Browser/ES Module Interface
 * 
 * This is the browser-compatible version that uses fetch() instead of fs
 * and exports ES modules instead of CommonJS.
 */

// Detection algorithm constants (same as Node.js version)
const PRIOR_WEIGHT = 0.65;
const FREQ_WEIGHT = 0.35;
const CHAR_WEIGHT = 0.2;

// Cache for loaded data
const frequencyCache = new Map();
const alphabetCache = new Map();
let indexCache = null;

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
 * Load frequency data for a language
 */
async function loadRankData(lang) {
  if (frequencyCache.has(lang)) {
    return frequencyCache.get(lang);
  }

  try {
    const response = await fetch(`/WorldAlphabets/data/freq/top1000/${lang}.txt`);
    if (!response.ok) {
      const data = { mode: 'word', ranks: new Map() };
      frequencyCache.set(lang, data);
      return data;
    }

    const text = await response.text();
    const lines = text.split(/\r?\n/).filter(Boolean);
    
    let mode = 'word';
    if (lines[0] && lines[0].startsWith('#')) {
      const header = lines.shift();
      if (header.includes('bigram')) mode = 'bigram';
    }

    const ranks = new Map();
    lines.forEach((token, i) => {
      if (!ranks.has(token)) ranks.set(token, i + 1);
    });

    const data = { mode, ranks };
    frequencyCache.set(lang, data);
    return data;
  } catch (error) {
    const data = { mode: 'word', ranks: new Map() };
    frequencyCache.set(lang, data);
    return data;
  }
}

/**
 * Load alphabet data for a language
 */
async function loadAlphabetData(langCode) {
  if (alphabetCache.has(langCode)) {
    return alphabetCache.get(langCode);
  }

  try {
    const response = await fetch(`/WorldAlphabets/data/alphabets/${langCode}.json`);
    if (!response.ok) {
      alphabetCache.set(langCode, null);
      return null;
    }

    const data = await response.json();
    alphabetCache.set(langCode, data);
    return data;
  } catch (error) {
    alphabetCache.set(langCode, null);
    return null;
  }
}

/**
 * Tokenize text into words (same as Node.js version)
 */
function tokenizeWords(text) {
  return new Set(text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || []);
}

/**
 * Tokenize text into bigrams (same as Node.js version)
 */
function tokenizeBigrams(text) {
  const letters = Array.from(text.normalize('NFKC').toLowerCase()).filter(ch => /\p{L}/u.test(ch));
  const bigrams = new Set();
  for (let i = 0; i < letters.length - 1; i++) {
    bigrams.add(letters[i] + letters[i + 1]);
  }
  return bigrams;
}

/**
 * Tokenize text into characters (same as Node.js version)
 */
function tokenizeCharacters(text) {
  const normalized = text.normalize('NFKC').toLowerCase();
  return new Set(Array.from(normalized).filter(ch => /\p{L}/u.test(ch)));
}

/**
 * Calculate overlap score (same as Node.js version)
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
 * Calculate character overlap (same as Node.js version)
 */
function characterOverlap(textChars, alphabetChars) {
  if (!textChars || !alphabetChars || textChars.size === 0 || alphabetChars.size === 0) {
    return 0.0;
  }

  const matchingChars = new Set([...textChars].filter(ch => alphabetChars.has(ch)));
  const nonMatchingChars = new Set([...textChars].filter(ch => !alphabetChars.has(ch)));

  if (matchingChars.size === 0) {
    return 0.0;
  }

  const coverage = matchingChars.size / textChars.size;
  const penalty = nonMatchingChars.size / textChars.size;
  const alphabetCoverage = matchingChars.size / alphabetChars.size;

  const score = coverage * 0.6 - penalty * 0.2 + alphabetCoverage * 0.2;
  return Math.max(0.0, score);
}

/**
 * Detect languages in text (same algorithm as Node.js version)
 */
export async function detectLanguages(text, candidateLangs, priors = {}, topk = 3) {
  // Ensure candidateLangs is iterable
  if (!candidateLangs || !Array.isArray(candidateLangs)) {
    throw new Error(`candidateLangs must be an array, got: ${typeof candidateLangs}`);
  }

  const wordTokens = tokenizeWords(text);
  const bigramTokens = tokenizeBigrams(text);
  const textChars = tokenizeCharacters(text);
  const results = [];
  const wordBasedLangs = new Set();

  for (const lang of candidateLangs) {
    // Try word-based detection first
    const data = await loadRankData(lang);
    const tokens = data.mode === 'bigram' ? bigramTokens : wordTokens;
    let wordOverlap = 0;
    
    if (data.ranks.size > 0 && tokens.size > 0) {
      wordOverlap = overlap(tokens, data.ranks);
      wordOverlap /= Math.sqrt(tokens.size + 3);
    }

    const wordScore = PRIOR_WEIGHT * (priors[lang] || 0) + FREQ_WEIGHT * wordOverlap;

    // If word-based detection succeeds, use it
    if (wordScore > 0.05) {
      results.push([lang, wordScore]);
      wordBasedLangs.add(lang);
      continue;
    }

    // Fallback to character-based detection
    if (textChars.size > 0) {
      const alphabetData = await loadAlphabetData(lang);
      if (alphabetData) {
        const lowercaseChars = new Set(alphabetData.lowercase || []);
        const charOverlapScore = characterOverlap(textChars, lowercaseChars);
        const charScore = PRIOR_WEIGHT * (priors[lang] || 0) + CHAR_WEIGHT * charOverlapScore;

        if (charScore > 0.02) {
          results.push([lang, charScore]);
        }
      }
    }
  }

  // Sort results, prioritizing word-based detections
  results.sort((a, b) => {
    const [langA, scoreA] = a;
    const [langB, scoreB] = b;
    const adjustedScoreA = wordBasedLangs.has(langA) ? scoreA + 0.1 : scoreA; // Increased boost
    const adjustedScoreB = wordBasedLangs.has(langB) ? scoreB + 0.1 : scoreB; // Increased boost
    return adjustedScoreB - adjustedScoreA;
  });

  return results.slice(0, topk);
}

/**
 * Get language information
 */
export async function getLanguage(langCode) {
  const data = await getIndexData();
  const entry = data.find(item => item.language === langCode);
  if (!entry) return null;
  
  try {
    return await loadAlphabetData(langCode);
  } catch (error) {
    return null;
  }
}

// Export all the same functions as the Node.js version
export {
  getIndexData,
  tokenizeWords,
  tokenizeBigrams,
  tokenizeCharacters,
  overlap,
  characterOverlap
};
