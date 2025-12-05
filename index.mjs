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
const SCANCODE_TO_CODE = {
  '01': 'Escape',
  '02': 'Digit1',
  '03': 'Digit2',
  '04': 'Digit3',
  '05': 'Digit4',
  '06': 'Digit5',
  '07': 'Digit6',
  '08': 'Digit7',
  '09': 'Digit8',
  '0A': 'Digit9',
  '0B': 'Digit0',
  '0C': 'Minus',
  '0D': 'Equal',
  '0E': 'Backspace',
  '0F': 'Tab',
  '10': 'KeyQ',
  '11': 'KeyW',
  '12': 'KeyE',
  '13': 'KeyR',
  '14': 'KeyT',
  '15': 'KeyY',
  '16': 'KeyU',
  '17': 'KeyI',
  '18': 'KeyO',
  '19': 'KeyP',
  '1A': 'BracketLeft',
  '1B': 'BracketRight',
  '1C': 'Enter',
  '1D': 'ControlLeft',
  '1E': 'KeyA',
  '1F': 'KeyS',
  '20': 'KeyD',
  '21': 'KeyF',
  '22': 'KeyG',
  '23': 'KeyH',
  '24': 'KeyJ',
  '25': 'KeyK',
  '26': 'KeyL',
  '27': 'Semicolon',
  '28': 'Quote',
  '29': 'Backquote',
  '2A': 'ShiftLeft',
  '2B': 'Backslash',
  '2C': 'KeyZ',
  '2D': 'KeyX',
  '2E': 'KeyC',
  '2F': 'KeyV',
  '30': 'KeyB',
  '31': 'KeyN',
  '32': 'KeyM',
  '33': 'Comma',
  '34': 'Period',
  '35': 'Slash',
  '36': 'ShiftRight',
  '37': 'NumpadMultiply',
  '38': 'AltLeft',
  '39': 'Space',
  '3A': 'CapsLock',
  '3B': 'F1',
  '3C': 'F2',
  '3D': 'F3',
  '3E': 'F4',
  '3F': 'F5',
  '40': 'F6',
  '41': 'F7',
  '42': 'F8',
  '43': 'F9',
  '44': 'F10',
  '45': 'NumLock',
  '46': 'ScrollLock',
  '47': 'Numpad7',
  '48': 'Numpad8',
  '49': 'Numpad9',
  '4A': 'NumpadSubtract',
  '4B': 'Numpad4',
  '4C': 'Numpad5',
  '4D': 'Numpad6',
  '4E': 'NumpadAdd',
  '4F': 'Numpad1',
  '50': 'Numpad2',
  '51': 'Numpad3',
  '52': 'Numpad0',
  '53': 'NumpadDecimal',
  '56': 'IntlBackslash',
  '57': 'F11',
  '58': 'F12',
  'E010': 'MediaPreviousTrack',
  'E019': 'MediaNextTrack',
  'E01C': 'NumpadEnter',
  'E01D': 'ControlRight',
  'E020': 'VolumeMute',
  'E021': 'LaunchApp2',
  'E022': 'MediaPlayPause',
  'E024': 'MediaStop',
  'E02E': 'VolumeDown',
  'E030': 'VolumeUp',
  'E032': 'BrowserHome',
  'E035': 'NumpadDivide',
  'E037': 'PrintScreen',
  'E038': 'AltRight',
  'E046': 'Pause',
  'E047': 'Home',
  'E048': 'ArrowUp',
  'E049': 'PageUp',
  'E04B': 'ArrowLeft',
  'E04D': 'ArrowRight',
  'E04F': 'End',
  'E050': 'ArrowDown',
  'E051': 'PageDown',
  'E052': 'Insert',
  'E053': 'Delete',
  'E05B': 'MetaLeft',
  'E05C': 'MetaRight',
  'E05D': 'ContextMenu',
  'E05F': 'Sleep',
  'E065': 'BrowserSearch',
  'E066': 'BrowserFavorites',
  'E067': 'BrowserRefresh',
  'E068': 'BrowserStop',
  'E069': 'BrowserForward',
  'E06A': 'BrowserBack',
  'E06B': 'LaunchApp1',
  'E06C': 'LaunchMail',
  'E06D': 'MediaSelect',
  'E11D': 'Pause',
};

const VK_TO_CODE = {
  VK_SPACE: 'Space',
  VK_ADD: 'NumpadAdd',
  VK_SUBTRACT: 'NumpadSubtract',
  VK_MULTIPLY: 'NumpadMultiply',
  VK_DIVIDE: 'NumpadDivide',
  VK_ABNT_C1: 'IntlBackslash',
  VK_ABNT_C2: 'NumpadDecimal',
  VK_OEM_1: 'Semicolon',
  VK_OEM_PLUS: 'Equal',
  VK_OEM_COMMA: 'Comma',
  VK_OEM_MINUS: 'Minus',
  VK_OEM_PERIOD: 'Period',
  VK_OEM_2: 'Slash',
  VK_OEM_3: 'Backquote',
  VK_OEM_4: 'BracketLeft',
  VK_OEM_5: 'Backslash',
  VK_OEM_6: 'BracketRight',
  VK_OEM_7: 'Quote',
  VK_OEM_8: 'IntlBackslash',
  VK_OEM_102: 'IntlBackslash',
};

const CODE_TO_HID = (() => {
  const map = {
    Escape: 0x29,
    Backspace: 0x2A,
    Tab: 0x2B,
    Space: 0x2C,
    Minus: 0x2D,
    Equal: 0x2E,
    BracketLeft: 0x2F,
    BracketRight: 0x30,
    Backslash: 0x31,
    NonUSHash: 0x32,
    Semicolon: 0x33,
    Quote: 0x34,
    Backquote: 0x35,
    Comma: 0x36,
    Period: 0x37,
    Slash: 0x38,
    CapsLock: 0x39,
    Enter: 0x28,
    IntlBackslash: 0x64,
    NumpadDivide: 0x54,
    NumpadMultiply: 0x55,
    NumpadSubtract: 0x56,
    NumpadAdd: 0x57,
    NumpadEnter: 0x58,
    Numpad1: 0x59,
    Numpad2: 0x5A,
    Numpad3: 0x5B,
    Numpad4: 0x5C,
    Numpad5: 0x5D,
    Numpad6: 0x5E,
    Numpad7: 0x5F,
    Numpad8: 0x60,
    Numpad9: 0x61,
    Numpad0: 0x62,
    NumpadDecimal: 0x63,
  };
  for (let i = 0; i < 26; i += 1) {
    map[`Key${String.fromCharCode(65 + i)}`] = 0x04 + i;
  }
  for (let i = 1; i <= 9; i += 1) {
    map[`Digit${i}`] = 0x1D + i;
  }
  map.Digit0 = 0x27;
  return map;
})();

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

function sanitizeIdentifier(value) {
  const cleaned = String(value || '').replace(/[^A-Za-z0-9_]/g, '_');
  if (!cleaned) return 'layout';
  if (/^[0-9]/.test(cleaned)) return `layout_${cleaned}`;
  return cleaned;
}

function escapeCString(value) {
  return String(value || '')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

function resolveDomCode(key) {
  if (key.pos) return key.pos;
  if (key.vk && VK_TO_CODE[key.vk]) return VK_TO_CODE[key.vk];
  if (key.sc) {
    const scKey = key.sc.toUpperCase();
    if (SCANCODE_TO_CODE[scKey]) {
      return SCANCODE_TO_CODE[scKey];
    }
  }
  return null;
}

function codeToHidUsage(code) {
  if (!code) return null;
  if (Object.prototype.hasOwnProperty.call(CODE_TO_HID, code)) {
    return CODE_TO_HID[code];
  }
  return null;
}

function buildLayerEntries(layout, layers) {
  const targetLayers = layers || DEFAULT_LAYERS;
  const built = [];
  for (const layer of targetLayers) {
    const entries = new Map();
    for (const key of layout.keys || []) {
      if (!key || !key.legends) continue;
      const legend = key.legends[layer];
      if (!legend) continue;
      const domCode = resolveDomCode(key);
      if (!domCode) {
        throw new Error(
          `Unable to resolve key code for layer '${layer}' in layout '${layout.id}'.`
        );
      }
      const usage = codeToHidUsage(domCode);
      if (usage === null) {
        throw new Error(
          `Unsupported key code '${domCode}' in layout '${layout.id}'.`
        );
      }
      entries.set(usage, legend);
    }
    if (entries.size > 0) {
      const sorted = Array.from(entries.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([usage, value]) => ({ usage, value }));
      built.push({ name: layer, entries: sorted });
    }
  }
  return built;
}

function formatHex(value) {
  return `0x${value.toString(16).toUpperCase().padStart(2, '0')}`;
}

export async function generateCHeader(layoutId, options = {}) {
  const { layers = DEFAULT_LAYERS, guard = true, symbolName } = options;
  const layout = await loadKeyboard(layoutId);
  const layerEntries = buildLayerEntries(layout, layers);
  if (layerEntries.length === 0) {
    throw new Error(`No legends found for layout '${layout.id}'.`);
  }

  const symbolBase = sanitizeIdentifier(
    symbolName || `layout_${layout.id || layoutId}`
  );
  const guardName = `${symbolBase.toUpperCase()}_H`;

  const lines = [];
  if (guard) {
    lines.push(`#ifndef ${guardName}`);
    lines.push(`#define ${guardName}`);
    lines.push('');
  }

  lines.push('#include <stddef.h>');
  lines.push('#include <stdint.h>');
  lines.push('');
  lines.push('typedef struct {');
  lines.push('  uint16_t keycode;');
  lines.push('  const char *value;');
  lines.push('} keyboard_mapping_t;');
  lines.push('');
  lines.push('typedef struct {');
  lines.push('  const char *name;');
  lines.push('  const keyboard_mapping_t *entries;');
  lines.push('  size_t entry_count;');
  lines.push('} keyboard_layer_t;');
  lines.push('');
  lines.push('typedef struct {');
  lines.push('  const char *name;');
  lines.push('  const char *display_name;');
  lines.push('  const keyboard_layer_t *layers;');
  lines.push('  size_t layer_count;');
  lines.push('} keyboard_layout_t;');
  lines.push('');

  for (const layer of layerEntries) {
    const entryName = `${symbolBase}_${layer.name}_entries`;
    lines.push(`static const keyboard_mapping_t ${entryName}[] = {`);
    for (const entry of layer.entries) {
      lines.push(
        `  { ${formatHex(entry.usage)}, "${escapeCString(entry.value)}" },`
      );
    }
    lines.push('};');
    lines.push('');
    lines.push(`static const keyboard_layer_t ${symbolBase}_${layer.name} = {`);
    lines.push(`  .name = "${layer.name}",`);
    lines.push(`  .entries = ${entryName},`);
    lines.push(`  .entry_count = ${layer.entries.length}u,`);
    lines.push('};');
    lines.push('');
  }

  lines.push(`static const keyboard_layer_t ${symbolBase}_layers[] = {`);
  for (const layer of layerEntries) {
    lines.push(`  ${symbolBase}_${layer.name},`);
  }
  lines.push('};');
  lines.push('');
  lines.push(`static const keyboard_layout_t ${symbolBase} = {`);
  lines.push(`  .name = "${escapeCString(layout.id)}",`);
  lines.push(
    `  .display_name = "${escapeCString(layout.name || layout.id)}",`
  );
  lines.push(`  .layers = ${symbolBase}_layers,`);
  lines.push(`  .layer_count = ${layerEntries.length}u,`);
  lines.push('};');
  if (guard) {
    lines.push('');
    lines.push(`#endif /* ${guardName} */`);
  }

  return lines.join('\n');
}

export { DEFAULT_LAYERS };

// Utility exports mirroring helpers from Node build
export { getIndexData, tokenizeWords, tokenizeBigrams, tokenizeCharacters, overlap, characterOverlap, detectDominantScript };
