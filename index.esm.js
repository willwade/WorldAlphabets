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

  const response = await fetch('./data/index.json');
  if (!response.ok) throw new Error('Failed to load index data');

  indexCache = await response.json();
  return indexCache;
}

/**
 * Get character index data for candidate filtering
 */
let charIndexCache = null;
async function getCharIndexData() {
  if (charIndexCache) return charIndexCache;

  try {
    const response = await fetch('./data/char_index.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    charIndexCache = await response.json();
    return charIndexCache;
  } catch (error) {
    console.error('Failed to load char index data:', error);
    return {};
  }
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
    const response = await fetch(`./data/freq/top1000/${lang}.txt`);
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
    const response = await fetch(`./data/alphabets/${langCode}.json`);
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
 * Decompose a Hangul syllable into Jamo for better character-index matching
 */
function decomposeHangulSyllable(ch) {
  const code = ch.codePointAt(0);
  const SBase = 0xAC00;

  const LCount = 19;
  const VCount = 21;
  const TCount = 28;
  const NCount = VCount * TCount; // 588
  const SCount = LCount * NCount; // 11172

  if (code < SBase || code >= SBase + SCount) return [];
  const SIndex = code - SBase;
  const LIndex = Math.floor(SIndex / NCount);
  const VIndex = Math.floor((SIndex % NCount) / TCount);
  const TIndex = SIndex % TCount;

  // Compatibility jamo (the ones present in our char_index)
  const LComp = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
  const VComp = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"];
  const TComp = ["", "ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];

  const result = [LComp[LIndex], VComp[VIndex]];
  if (TIndex > 0) result.push(TComp[TIndex]);
  return result;
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
 * Get candidate languages using character-based filtering
 */
async function getCandidateLanguages(text, maxCandidates = 20) {
  const chars = tokenizeCharacters(text);
  const charIndex = await getCharIndexData();
  const charMap = (charIndex && charIndex.char_to_languages) ? charIndex.char_to_languages : charIndex;


  // Count how many characters each language supports
  const languageScores = new Map();

  for (const char of chars) {
    // Expand Hangul syllables into jamo to match our char_index keys
    const keys = [char];
    const code = char.codePointAt(0);
    if (code >= 0xAC00 && code <= 0xD7A3) {
      const jamo = decomposeHangulSyllable(char);
      keys.push(...jamo);
    }

    for (const key of keys) {
      const languages = (charMap && charMap[key]) ? charMap[key] : [];
      for (const lang of languages) {
        languageScores.set(lang, (languageScores.get(lang) || 0) + 1);
      }
    }
  }

  // Convert to array and sort by score
  const candidates = Array.from(languageScores.entries())
    .map(([lang, score]) => ({
      lang,
      score,
      coverage: score / chars.size
    }))
    .sort((a, b) => b.coverage - a.coverage)
    .slice(0, maxCandidates)
    .map(item => item.lang);

  return candidates.length > 0 ? candidates : ['en', 'es', 'fr', 'de', 'it']; // fallback
}

/**
 * Detect languages in text (same algorithm as Node.js version)
 */
export async function detectLanguages(text, candidateLangs = null, priors = {}, topk = 3) {
  // If no candidates provided, use smart filtering
  if (!candidateLangs || candidateLangs === null) {
    candidateLangs = await getCandidateLanguages(text, 20);
  }

  // Validate that candidateLangs is now an array
  if (!Array.isArray(candidateLangs)) {
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
