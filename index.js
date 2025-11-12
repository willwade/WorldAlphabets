const fs = require('fs/promises');
const path = require('path');

const LEGACY_ALPHABET_DIR = path.join(__dirname, 'data', 'alphabets');
const CANONICAL_DATA_DIR = path.join(__dirname, 'data');
const LEGACY_FREQ_DIR = path.join(__dirname, 'data', 'freq', 'top1000');

/**
 * Loads the alphabet data for a given language code and script.
 * @param {string} code - The ISO 639-1 language code.
 * @param {string} [script] - Optional ISO-15924 script code.
 * @returns {Promise<object>} A promise that resolves to the alphabet data.
 */
async function resolveEntries(code) {
  const data = await getIndexData();
  const needle = (code || '').toLowerCase();
  if (!needle) return [];
  return data.filter(
    (item) =>
      item.language === needle ||
      (item.iso639_1 && item.iso639_1.toLowerCase() === needle)
  );
}

function getAlphabetPath(entry) {
  const fileName = entry.file || `${entry.language}-${entry.script}.json`;
  const canonicalPath = path.join(
    CANONICAL_DATA_DIR,
    entry.language,
    'alphabet',
    fileName
  );
  return canonicalPath;
}

async function loadAlphabet(code, script) {
  const entries = await resolveEntries(code);
  const candidates = [];
  if (script) {
    candidates.push(
      ...entries.filter(
        (entry) => entry.script && entry.script.toLowerCase() === script.toLowerCase()
      )
    );
  }
  candidates.push(...entries);

  for (const entry of candidates) {
    const filePath = getAlphabetPath(entry);
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const parsed = JSON.parse(content);
      if (!parsed.script && entry.script) {
        parsed.script = entry.script;
      }
      return parsed;
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
  }

  // Fallback to legacy layout (for backward compatibility)
  const legacyCandidates = [];
  if (script) {
    legacyCandidates.push(path.join(LEGACY_ALPHABET_DIR, `${code}-${script}.json`));
  }
  legacyCandidates.push(path.join(LEGACY_ALPHABET_DIR, `${code}.json`));

  for (const filePath of legacyCandidates) {
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const parsed = JSON.parse(content);
      if (!parsed.script && script) {
        parsed.script = script;
      }
      return parsed;
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
  }

  throw new Error(`Alphabet data for code "${code}" not found.`);
}

/**
 * Gets the uppercase alphabet for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<string[]>} A promise that resolves to an array of uppercase letters.
 */
async function getUppercase(code, script) {
  const data = await loadAlphabet(code, script);
  return data.uppercase || [];
}

/**
 * Gets the lowercase alphabet for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<string[]>} A promise that resolves to an array of lowercase letters.
 */
async function getLowercase(code, script) {
  const data = await loadAlphabet(code, script);
  return data.lowercase || [];
}

/**
 * Gets the letter frequency for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<object>} A promise that resolves to an object with letter frequencies.
 */
async function getFrequency(code, script) {
  const data = await loadAlphabet(code, script);
  return data.frequency || {};
}

/**
 * Gets the digits for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @param {string} [script] - Optional ISO-15924 script code.
 * @returns {Promise<string[]>} A promise that resolves to an array of digit characters.
 */
async function getDigits(code, script) {
  const data = await loadAlphabet(code, script);
  return data.digits || [];
}

/**
 * Gets all available alphabet codes.
 * @returns {Promise<string[]>} A promise that resolves to an array of alphabet codes.
 */
async function getAvailableCodes() {
  const data = await getIndexData();
  const codes = data.map((item) => item.iso639_1 || item.language);
  return Array.from(new Set(codes)).sort();
}

/**
 * Loads the Top-1000 frequency tokens for a language.
 * @param {string} code - The ISO language code.
 * @returns {Promise<{language: string, tokens: string[], mode: 'word' | 'bigram'}>}
 */
async function loadFrequencyList(code) {
  const entries = await resolveEntries(code);
  const freqCode = entries.length > 0 ? entries[0].language : code;
  const canonicalPath = path.join(
    CANONICAL_DATA_DIR,
    freqCode,
    'frequency',
    'top1000.txt'
  );
  let filePath = canonicalPath;
  let content;
  try {
    content = await fs.readFile(filePath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      filePath = path.join(LEGACY_FREQ_DIR, `${freqCode}.txt`);
      try {
        content = await fs.readFile(filePath, 'utf8');
      } catch (innerError) {
        if (innerError.code === 'ENOENT') {
          throw new Error(`Frequency list for code "${code}" not found.`);
        }
        throw innerError;
      }
    } else {
      throw new Error(`Frequency list for code "${code}" not found.`);
    }
  }

  const tokens = [];
  let mode = 'word';

  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (tokens.length === 0 && trimmed.startsWith('#')) {
      if (trimmed.toLowerCase().includes('bigram')) {
        mode = 'bigram';
      }
      continue;
    }
    tokens.push(trimmed);
  }

  const returnCode =
    entries.length > 0
      ? entries[0].iso639_1 || entries[0].language
      : code;
  return { language: returnCode, tokens, mode };
}

const INDEX_FILE = path.join(__dirname, 'data', 'index.json');

let indexData = null;

/**
 * Loads the index.json data.
 * @returns {Promise<object[]>} A promise that resolves to the index data.
 */
async function getIndexData() {
  if (indexData) {
    return indexData;
  }
  const content = await fs.readFile(INDEX_FILE, 'utf8');
  indexData = JSON.parse(content);
  return indexData;
}

/**
 * Gets information for a specific language.
 * @param {string} langCode - The ISO 639-1 language code.
 * @returns {Promise<object|null>} A promise that resolves to the language information or null if not found.
 */
async function getLanguage(langCode, script) {
  const entries = await resolveEntries(langCode);
  if (!entries.length) {
    return null;
  }
  const chosenScript = script || entries[0].script;
  try {
    return await loadAlphabet(entries[0].language, chosenScript);
  } catch (_) {
    return null;
  }
}

/**
 * Lists available scripts for a language.
 * @param {string} langCode - The ISO 639-1 language code.
 * @returns {Promise<string[]>} A promise that resolves to an array of script codes.
 */
async function getScripts(langCode) {
  const entries = await resolveEntries(langCode);
  if (!entries.length) return [];
  return Array.from(new Set(entries.map((entry) => entry.script))).filter(Boolean);
}

// Special characters that don't decompose properly with NFD
// These need explicit mapping to their base forms
const SPECIAL_BASE = {
  Ł: 'L',
  ł: 'l',
  Đ: 'D',
  đ: 'd',
  Ø: 'O',
  ø: 'o',
  Ð: 'D', // Icelandic eth
  ð: 'd',
  Þ: 'T', // Icelandic thorn
  þ: 't',
  Ŋ: 'N', // Eng
  ŋ: 'n',
};

/**
 * Remove diacritic marks from text.
 * @param {string} text - The text to process
 * @returns {string} Text with diacritic marks removed
 */
function stripDiacritics(text) {
  if (!text) return text;

  return Array.from(text)
    .map((ch) => {
      // First check if it's a special character that needs explicit mapping
      if (SPECIAL_BASE[ch]) {
        return SPECIAL_BASE[ch];
      }
      // Use Unicode normalization to decompose and remove combining marks
      return ch.normalize('NFD').replace(/\p{M}/gu, '');
    })
    .join('');
}

/**
 * Check if a character contains diacritic marks.
 * @param {string} char - The character to check
 * @returns {boolean} True if the character has diacritics
 */
function hasDiacritics(char) {
  if (!char) return false;
  return stripDiacritics(char) !== char;
}

/**
 * Filter characters that contain diacritic marks.
 * @param {string[]} chars - Array of characters to filter
 * @returns {string[]} Characters that contain diacritic marks
 */
function charactersWithDiacritics(chars) {
  return chars.filter((ch) => ch && hasDiacritics(ch));
}

async function getDiacriticVariants(code, script) {
  const data = await loadAlphabet(code, script);

  const build = (chars = []) => {
    const groups = {};
    for (const ch of chars) {
      const base = stripDiacritics(ch);
      groups[base] = groups[base] || new Set();
      groups[base].add(ch);
    }
    return Object.fromEntries(
      Object.entries(groups)
        .filter(([, set]) => set.size > 1)
        .map(([b, set]) => [b, Array.from(set).sort()])
    );
  };

  return { ...build(data.uppercase), ...build(data.lowercase) };
}

const PRIOR_WEIGHT = Number(process.env.WA_FREQ_PRIOR_WEIGHT ?? 0.65);
const FREQ_WEIGHT = Number(process.env.WA_FREQ_OVERLAP_WEIGHT ?? 0.35);
const CHAR_WEIGHT = 0.2; // Weight for character-based detection fallback
const DEFAULT_FREQ_DIR =
  process.env.WORLDALPHABETS_FREQ_DIR ??
  require('path').resolve(__dirname, 'data', 'freq', 'top1000');

function tokenizeWords(text) {
  return new Set(text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || []);
}

function tokenizeBigrams(text) {
  const letters = Array.from(text.normalize('NFKC').toLowerCase()).filter((ch) =>
    /\p{L}/u.test(ch)
  );
  const bigrams = new Set();
  for (let i = 0; i < letters.length - 1; i++) {
    bigrams.add(letters[i] + letters[i + 1]);
  }
  return bigrams;
}

function loadRankData(lang, dir) {
  const fs = require('fs');
  const path = require('path');
  try {
    const lines = fs
      .readFileSync(path.join(dir, `${lang}.txt`), 'utf8')
      .split(/\r?\n/)
      .filter(Boolean);
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
  } catch {
    return { mode: 'word', ranks: new Map() };
  }
}

function overlap(tokens, ranks) {
  let score = 0;
  for (const t of tokens) {
    const r = ranks.get(t);
    if (r) score += 1 / Math.log2(r + 1.5);
  }
  return score;
}

function tokenizeCharacters(text) {
  const normalized = text.normalize('NFKC').toLowerCase();
  return new Set(Array.from(normalized).filter(ch => /\p{L}/u.test(ch)));
}

function characterOverlap(textChars, alphabetChars) {
  if (!textChars || !alphabetChars || textChars.size === 0 || alphabetChars.size === 0) {
    return 0.0;
  }

  // Characters that are in the text and in the alphabet
  const matchingChars = new Set([...textChars].filter(ch => alphabetChars.has(ch)));
  // Characters that are in the text but NOT in the alphabet
  const nonMatchingChars = new Set([...textChars].filter(ch => !alphabetChars.has(ch)));

  if (matchingChars.size === 0) {
    return 0.0;
  }

  // Base score: how well the alphabet covers the text
  const coverage = matchingChars.size / textChars.size;

  // Penalty for characters that don't belong to this alphabet
  const penalty = nonMatchingChars.size / textChars.size;

  // Bonus for using distinctive characters (less common across alphabets)
  const alphabetCoverage = matchingChars.size / alphabetChars.size;

  // Combine: high coverage, low penalty, bonus for distinctive usage
  const score = coverage * 0.6 - penalty * 0.2 + alphabetCoverage * 0.2;

  return Math.max(0.0, score); // Ensure non-negative
}

function frequencyOverlap(textChars, charFrequencies) {
  if (!textChars || !charFrequencies || textChars.size === 0 || Object.keys(charFrequencies).length === 0) {
    return 0.0;
  }

  let score = 0.0;
  let totalFreq = 0.0;

  for (const char of textChars) {
    const freq = charFrequencies[char] || 0.0;
    if (freq > 0) {
      // Weight by frequency (more common chars get higher scores)
      score += freq;
      totalFreq += freq;
    }
  }

  // Normalize by the total frequency of matched characters
  return totalFreq > 0 ? score / Math.max(totalFreq, 0.001) : 0.0;
}

function loadAlphabetSync(langCode, script) {
  const fs = require('fs');
  const path = require('path');

  // Try script-specific file first
  if (script) {
    const scriptFile = path.resolve(__dirname, 'data', 'alphabets', `${langCode}-${script}.json`);
    try {
      const content = fs.readFileSync(scriptFile, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      // Fall through to legacy file
    }
  }

  // Try legacy file
  const legacyFile = path.resolve(__dirname, 'data', 'alphabets', `${langCode}.json`);
  try {
    const content = fs.readFileSync(legacyFile, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    return null;
  }
}

function getLanguageSync(langCode, script) {
  const fs = require('fs');
  const path = require('path');

  // Load index data synchronously
  try {
    const indexPath = path.resolve(__dirname, 'data', 'index.json');
    const indexContent = fs.readFileSync(indexPath, 'utf8');
    const data = JSON.parse(indexContent);

    const entry = data.find((item) => item.language === langCode);
    if (!entry) {
      return null;
    }

    // Handle both old format (scripts array) and new format (single script)
    let chosenScript = script;
    if (!chosenScript) {
      if (entry.script) {
        chosenScript = entry.script;
      } else if (entry.scripts && entry.scripts.length > 0) {
        chosenScript = entry.scripts[0];
      }
    }

    return loadAlphabetSync(langCode, chosenScript);
  } catch (error) {
    return null;
  }
}

function detectLanguages(text, candidateLangs, priors = {}, topk = 3) {
  const dir = process.env.WORLDALPHABETS_FREQ_DIR ?? DEFAULT_FREQ_DIR;
  const wordTokens = tokenizeWords(text);
  const bigramTokens = tokenizeBigrams(text);
  const textChars = tokenizeCharacters(text);
  const results = [];
  const wordBasedLangs = new Set(); // Track which languages used word-based detection

  for (const lang of candidateLangs) {
    // Try word-based detection first
    const data = loadRankData(lang, dir);
    const tokens = data.mode === 'bigram' ? bigramTokens : wordTokens;
    let wordOverlap = 0;
    if (data.ranks.size > 0 && tokens.size > 0) {
      wordOverlap = overlap(tokens, data.ranks);
      wordOverlap /= Math.sqrt(tokens.size + 3);
    }

    // Calculate word-based score
    const wordScore = PRIOR_WEIGHT * (priors[lang] || 0) + FREQ_WEIGHT * wordOverlap;

    // If word-based detection succeeds, use it and mark as word-based
    if (wordScore > 0.05) {
      results.push([lang, wordScore]);
      wordBasedLangs.add(lang);
      continue;
    }

    // Fallback to character-based detection
    if (textChars.size > 0) {
      try {
        // Load alphabet data for this language
        const alphabetData = getLanguageSync(lang);
        if (alphabetData) {
          // Get character sets
          const lowercaseChars = new Set(alphabetData.lowercase || []);
          const charFrequencies = alphabetData.frequency || {};

          // Calculate character-based scores
          const charOverlapScore = characterOverlap(textChars, lowercaseChars);
          const freqOverlapScore = frequencyOverlap(textChars, charFrequencies);

          // Combine character overlap and frequency overlap
          const charScore = charOverlapScore * 0.6 + freqOverlapScore * 0.4;

          // Apply character-based weight
          const finalCharScore = PRIOR_WEIGHT * (priors[lang] || 0) + CHAR_WEIGHT * charScore;

          // Use a lower threshold for character-based detection
          if (finalCharScore > 0.02) {
            results.push([lang, finalCharScore]);
          }
        }
      } catch (error) {
        // If alphabet loading fails, skip this language
        continue;
      }
    }
  }

  // Sort results, but prioritize word-based detections over character-based ones
  results.sort((a, b) => {
    const [langA, scoreA] = a;
    const [langB, scoreB] = b;
    const adjustedScoreA = wordBasedLangs.has(langA) ? scoreA + 0.15 : scoreA; // Increased boost
    const adjustedScoreB = wordBasedLangs.has(langB) ? scoreB + 0.15 : scoreB; // Increased boost
    return adjustedScoreB - adjustedScoreA;
  });

  return results.slice(0, topk);
}

const keyboards = require('./keyboards');

module.exports = {
  // Alphabets
  loadAlphabet,
  getUppercase,
  getLowercase,
  getFrequency,
  getDigits,
  getAvailableCodes,
  loadFrequencyList,
  getIndexData,
  getLanguage,
  getScripts,
  // Diacritics
  stripDiacritics,
  hasDiacritics,
  charactersWithDiacritics,
  getDiacriticVariants,
  // Language detection
  detectLanguages,
  // Keyboards
  ...keyboards,
};
