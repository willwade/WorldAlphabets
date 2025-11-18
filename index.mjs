/**
 * WorldAlphabets Browser/ES Module Interface
 *
 * This is the browser-compatible version that imports packaged JSON assets
 * (no fs, no fetch) and exports ES modules.
 */
import indexDataJson from './data/index.json';
import charIndexJson from './data/char_index.json';
import { ALPHABETS } from './dist/browser-alphabets.mjs';
import { LAYOUTS, AVAILABLE_LAYOUTS } from './dist/browser-layouts.mjs';
import { FREQ_RANKS } from './dist/browser-freq.mjs';


// Detection algorithm constants (same as Node.js version)
const PRIOR_WEIGHT = 0.65;
const FREQ_WEIGHT = 0.35;
const CHAR_WEIGHT = 0.2;

const DEFAULT_LAYERS = ['base', 'shift', 'caps', 'altgr', 'shift_altgr', 'ctrl', 'alt'];

// Cache for loaded data
const frequencyCache = new Map();
const alphabetCache = new Map();
let indexCache = null;

/**
 * Load and cache index data
 */
async function getIndexData() {
  if (indexCache) return indexCache;
  indexCache = indexDataJson;
  return indexCache;
}

/**
 * Get character index data for candidate filtering
 */
let charIndexCache = null;
async function getCharIndexData() {
  if (charIndexCache) return charIndexCache;
  try {
    charIndexCache = charIndexJson || {};
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
  const codes = data.map(item => item.language);
  return Array.from(new Set(codes)).sort();
}

/**
 * Load Top-1000 frequency tokens for a language from embedded data.
 */
export async function loadFrequencyList(code) {
  const entry = FREQ_RANKS[code];
  if (!entry || !Array.isArray(entry.tokens)) {
    throw new Error(`Frequency list for code "${code}" not found.`);
  }
  const mode = entry.mode === 'bigram' ? 'bigram' : 'word';
  const tokens = entry.tokens
    .map(token => (typeof token === 'string' ? token.trim() : ''))
    .filter(Boolean);
  return { language: code, tokens, mode };
}

/**
 * Load frequency data for a language (browser: static embedded ranks)
 */
async function loadRankData(lang) {
  if (frequencyCache.has(lang)) {
    return frequencyCache.get(lang);
  }
  const entry = FREQ_RANKS[lang];
  if (!entry || !Array.isArray(entry.tokens)) {
    const data = { mode: 'word', ranks: new Map() };
    frequencyCache.set(lang, data);
    return data;
  }
  const ranks = new Map();
  entry.tokens.forEach((token, i) => {
    if (!ranks.has(token)) ranks.set(token, i + 1);
  });
  const data = { mode: entry.mode || 'word', ranks };
  frequencyCache.set(lang, data);
  return data;
}

/**
 * Load alphabet data for a language (optionally for a specific script) via static imports
 */
async function loadAlphabetData(langCode, script) {
  const cacheKey = script ? `${langCode}-${script}` : langCode;
  if (alphabetCache.has(cacheKey)) {
    return alphabetCache.get(cacheKey);
  }
  const index = await getIndexData();
  let entry = null;
  if (script) {
    entry = index.find(item => item.language === langCode && item.script === script);
  }
  if (!entry) {
    entry = index.find(item => item.language === langCode);
  }
  if (entry && entry.file) {
    const key = entry.file.replace('.json', '');
    const json = ALPHABETS[key] || null;
    alphabetCache.set(cacheKey, json);
    return json;
  }
  alphabetCache.set(cacheKey, null);
  return null;
}

/**
 * Load alphabet data for consumers (mirrors CommonJS loadAlphabet)
 */
export async function loadAlphabet(langCode, script = null) {
  const data = await loadAlphabetData(langCode, script);
  if (!data) {
    throw new Error(`Alphabet data for code "${langCode}" not found.`);
  }
  return data;
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
 * Detect dominant script in text using Unicode Script properties
 */
function detectDominantScript(text) {
  const patterns = [
    ['Latn', /\p{Script=Latin}/u],
    ['Cyrl', /\p{Script=Cyrillic}/u],
    ['Grek', /\p{Script=Greek}/u],
    ['Arab', /\p{Script=Arabic}/u],
    ['Hebr', /\p{Script=Hebrew}/u],
    ['Deva', /\p{Script=Devanagari}/u],
    ['Beng', /\p{Script=Bengali}/u],
    ['Guru', /\p{Script=Gurmukhi}/u],
    ['Gujr', /\p{Script=Gujarati}/u],
    ['Orya', /\p{Script=Oriya}/u],
    ['Taml', /\p{Script=Tamil}/u],
    ['Telu', /\p{Script=Telugu}/u],
    ['Knda', /\p{Script=Kannada}/u],
    ['Mlym', /\p{Script=Malayalam}/u],
    ['Sinh', /\p{Script=Sinhala}/u],
    ['Thai', /\p{Script=Thai}/u],
    ['Laoo', /\p{Script=Lao}/u],
    ['Tibt', /\p{Script=Tibetan}/u],
    ['Mymr', /\p{Script=Myanmar}/u],
    ['Geor', /\p{Script=Georgian}/u],
    ['Armn', /\p{Script=Armenian}/u],
    ['Ethi', /\p{Script=Ethiopic}/u],
    ['Hang', /\p{Script=Hangul}/u],
    ['Kana', /\p{Script=Katakana}/u],
    ['Hira', /\p{Script=Hiragana}/u],
    ['Hani', /\p{Script=Han}/u],
  ];
  const counts = new Map();
  for (const ch of text) {
    if (!/\p{L}/u.test(ch)) continue;
    for (const [script, re] of patterns) {
      if (re.test(ch)) {
        counts.set(script, (counts.get(script) || 0) + 1);
        break;
      }
    }
  }
  let best = null;
  let bestCount = 0;
  for (const [script, count] of counts.entries()) {
    if (count > bestCount) {
      best = script;
      bestCount = count;
    }
  }
  return best;
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

  // Character fallback: remove size bonus to avoid bias toward small alphabets
  const score = coverage * 0.7 - penalty * 0.3;
  return Math.max(0.0, score);
}

/**
 * Get candidate languages using character-based filtering, then pad by dominant script
 */
async function getCandidateLanguages(text, maxCandidates = 20) {
  const chars = tokenizeCharacters(text);
  const wordTokens = tokenizeWords(text);
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

  // Sort by coverage
  const initial = Array.from(languageScores.entries())
    .map(([lang, score]) => ({ lang, coverage: score / Math.max(1, chars.size) }))
    .sort((a, b) => b.coverage - a.coverage)
    .map(item => item.lang);

  const seen = new Set();
  const out = [];

  // Determine dominant script and seed primaries FIRST
  const dom = detectDominantScript(text);
  if (dom) {
    const primaryByScript = {
      Latn: ['en','es','fr','de','pt','it','nl','af'],
      Cyrl: ['ru','uk','sr','bg'],
      Grek: ['el'],
      Arab: ['ar','fa','ur','ps'],
      Hebr: ['he','yi'],
      Deva: ['hi','mr','ne'],
      Beng: ['bn','as'],
      Ethi: ['am','ti','gez'],
      Hang: ['ko'],
      Hira: ['ja'],
      Kana: ['ja'],
      Hani: ['zh','ja','yue','wuu']
    };
    const primaries = primaryByScript[dom] || [];
    for (const lang of primaries) {
      if (!seen.has(lang)) {
        out.push(lang);
        seen.add(lang);
      }
    }
  }

  // Then add char-based candidates until we fill up
  for (const lang of initial) {
    if (!seen.has(lang)) {
      out.push(lang);
      seen.add(lang);
    }
    if (out.length >= maxCandidates) break;
  }

  // Add more by script if we still have room
  if (dom && out.length < maxCandidates) {
    const index = await getIndexData();
    for (const item of index) {
      if (item.script === dom && !seen.has(item.language)) {
        out.push(item.language);
        seen.add(item.language);
        if (out.length >= maxCandidates) break;
      }
    }
  }

  // Word-frequency-based candidate expansion: check if input words are in any language's top-1000 words
  if (wordTokens.size > 0) {
    const availableLangs = Object.keys(FREQ_RANKS);
    for (const lang of availableLangs) {
      if (seen.has(lang)) continue;
      const entry = FREQ_RANKS[lang];
      if (!entry || !Array.isArray(entry.tokens)) continue;

      // Check if any input word is in this language's top-1000 words
      let matches = 0;
      for (const token of wordTokens) {
        if (entry.tokens.includes(token)) {
          matches++;
        }
      }

      // If we have word matches, add this language to candidates
      if (matches > 0) {
        out.unshift(lang);  // Add to front since word matches are strong signals
        seen.add(lang);
      }
    }
  }

  // Short-text heuristic: if very few tokens, add languages whose hello samples overlap
  if (wordTokens.size > 0 && wordTokens.size <= 6) {
    const index = await getIndexData();
    for (const item of index) {
      const key = (item.file || '').replace('.json', '');
      const sample = ALPHABETS[key] && ALPHABETS[key].hello_how_are_you ? ALPHABETS[key].hello_how_are_you : null;
      if (!sample) continue;
      const sampTokens = tokenizeWords(sample);
      let matches = 0;
      for (const t of wordTokens) {
        if (t.length >= 3 && sampTokens.has(t)) matches++;
      }
      const perLangThreshold = Math.min((dom === 'Latn' ? 2 : 1), Math.max(1, sampTokens.size));
      if (matches >= perLangThreshold && !seen.has(item.language)) {
        out.unshift(item.language);
        seen.add(item.language);
      }
    }
  }

  if (out.length === 0) return ['en', 'es', 'fr', 'de', 'it'];
  return out.slice(0, maxCandidates);
}

/**
 * Detect languages in text (same algorithm as Node.js version)
 */
export async function detectLanguages(text, candidateLangs = null, priors = {}, topk = 3) {
  // If no candidates provided, use smart filtering
  if (!candidateLangs || candidateLangs === null) {
    candidateLangs = await getCandidateLanguages(text, 50);
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
  const exactMatchLangs = new Set();
  const phraseScript = detectDominantScript(text);

  for (const lang of candidateLangs) {
    let baseScore = 0;
    let usedWord = false;

    // Try word-based detection first
    const data = await loadRankData(lang);
    const tokens = data.mode === 'bigram' ? bigramTokens : wordTokens;
    let wordOverlap = 0;

    if (data.ranks.size > 0 && tokens.size > 0) {
      wordOverlap = overlap(tokens, data.ranks);
      wordOverlap /= Math.sqrt(tokens.size + 3);
    }

    const wordScore = PRIOR_WEIGHT * (priors[lang] || 0) + FREQ_WEIGHT * wordOverlap;

    if (wordScore > 0.05) {
      baseScore = wordScore;
      usedWord = true;
    } else if (textChars.size > 0) {
      // Fallback to character-based detection
      const alphabetData = await loadAlphabetData(lang);
      if (alphabetData) {
        const lowercaseChars = new Set(alphabetData.lowercase || []);
        const charOverlapScore = characterOverlap(textChars, lowercaseChars);
        const charScore = PRIOR_WEIGHT * (priors[lang] || 0) + CHAR_WEIGHT * charOverlapScore;
        if (charScore > 0.02) {
          baseScore = charScore;
        }
      }
    }

    // Phrase-based gentle boost: if input overlaps with the language's hello phrase
    let bonus = 0;
    try {
      const langData = await loadAlphabetData(lang);
      const sample = langData && langData.hello_how_are_you ? langData.hello_how_are_you : null;
      if (sample) {
        const sampTokens = tokenizeWords(sample);
        let matches = 0;
        for (const t of wordTokens) {
          if (sampTokens.has(t)) matches++;
        }
        if (matches > 0) {
          bonus = Math.min(0.05, matches * 0.02); // gentle boost, cap at 0.05
        }
        // Extra boost for near-exact phrase match (ignoring punctuation/case)
        const norm = s => s.normalize('NFKC').toLowerCase().replace(/[^\p{L}]+/gu, ' ').trim();
        if (norm(text) && norm(sample) && norm(text) === norm(sample)) {
          bonus = Math.max(bonus, 0.3); // exact phrase match gets 0.3 boost
          exactMatchLangs.add(lang);
        }
      }
    } catch (e) {
      // ignore boosting errors
    }

    // If we had no baseScore but we have a phrase match, still include it with the bonus
    if (baseScore > 0 || bonus > 0) {
      results.push([lang, baseScore + bonus]);
      if (usedWord) wordBasedLangs.add(lang);
    }
  }

  // Build index position map for deterministic tie-breaking on exact matches
  const indexData = await getIndexData();
  const indexPos = new Map();
  for (let i = 0; i < indexData.length; i++) {
    indexPos.set(indexData[i].language, i);
  }

  // Sort results, with a light preference for word-based and exact matches
  results.sort((a, b) => {
    const [langA, scoreA] = a;
    const [langB, scoreB] = b;
    let adjustedA = scoreA + (wordBasedLangs.has(langA) ? 0.15 : 0) + (exactMatchLangs.has(langA) ? 0.05 : 0);
    let adjustedB = scoreB + (wordBasedLangs.has(langB) ? 0.15 : 0) + (exactMatchLangs.has(langB) ? 0.05 : 0);

    if (exactMatchLangs.has(langA) && exactMatchLangs.has(langB)) {
      const posA = indexPos.has(langA) ? indexPos.get(langA) : Number.MAX_SAFE_INTEGER;
      const posB = indexPos.has(langB) ? indexPos.get(langB) : Number.MAX_SAFE_INTEGER;
      if (posA !== posB) {
        // For Latin phrases prefer later index (e.g., 'zu' over 'ss'); otherwise earlier (e.g., 'mk' over 'sr')
        if (phraseScript === 'Latn') return posB - posA;
        return posA - posB;
      }
    }

    return adjustedB - adjustedA;
  });

  return results.slice(0, topk);
}

/**
 * Get language information
 */
export async function getLanguage(langCode, script = null) {
  const data = await getIndexData();
  let entry = null;
  if (script) {
    entry = data.find(item => item.language === langCode && (item.script === script));
  }
  if (!entry) {
    entry = data.find(item => item.language === langCode);
  }
  if (!entry) return null;
  try {
    return await loadAlphabetData(langCode, script || entry.script);
  } catch (error) {
    return null;
  }
}

/**
 * Browser helpers mirroring the Node API
 */
export async function getScripts(langCode) {
  const data = await getIndexData();
  const entry = data.find(item => item.language === langCode);
  if (!entry) return [];
  if (Array.isArray(entry.scripts)) return entry.scripts;
  if (entry.script) return [entry.script];
  return [];
}

export async function getUppercase(langCode, script = null) {
  const data = await loadAlphabetData(langCode, script);
  return (data && data.uppercase) ? data.uppercase : [];
}

export async function getLowercase(langCode, script = null) {
  const data = await loadAlphabetData(langCode, script);
  return (data && data.lowercase) ? data.lowercase : [];
}

export async function getDigits(langCode, script = null) {
  const data = await loadAlphabetData(langCode, script);
  return (data && data.digits) ? data.digits : [];
}

export async function getFrequency(langCode, script = null) {
  const data = await loadAlphabetData(langCode, script);
  return (data && data.frequency) ? data.frequency : {};
}


/**
 * Keyboards (browser) using shipped layouts manifest
 */
export async function getAvailableLayouts() {
  return AVAILABLE_LAYOUTS;
}

export async function loadKeyboard(layoutId) {
  const kb = LAYOUTS[layoutId];
  if (!kb) throw new Error(`Keyboard layout '${layoutId}' not found.`);
  return kb;
}

export function getUnicode(keyEntry, layer) {
  if (!keyEntry || !keyEntry.legends) return null;
  const char = keyEntry.legends[layer];
  if (char) {
    return `U+${char.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`;
  }
  return null;
}

export function extractLayers(layout, layers = DEFAULT_LAYERS) {
  if (!layout || !Array.isArray(layout.keys)) {
    return {};
  }

  const result = {};
  for (const layer of layers) {
    const layerEntries = {};
    for (const key of layout.keys) {
      if (!key || !key.legends) continue;
      const value = key.legends[layer];
      if (!value) continue;
      const pos = key.pos || key.vk || key.sc;
      if (pos) {
        layerEntries[String(pos)] = value;
      }
    }
    if (Object.keys(layerEntries).length > 0) {
      result[layer] = layerEntries;
    }
  }

  return result;
}

export { DEFAULT_LAYERS };

// Utility exports mirroring helpers from Node build
export { getIndexData, tokenizeWords, tokenizeBigrams, tokenizeCharacters, overlap, characterOverlap, detectDominantScript };
