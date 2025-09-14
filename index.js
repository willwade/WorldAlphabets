const fs = require('fs/promises');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'alphabets');

/**
 * Loads the alphabet data for a given language code and script.
 * @param {string} code - The ISO 639-1 language code.
 * @param {string} [script] - Optional ISO-15924 script code.
 * @returns {Promise<object>} A promise that resolves to the alphabet data.
 */
async function loadAlphabet(code, script) {
  const candidates = [];
  if (!script) {
    try {
      const data = await getIndexData();
      const entries = data.filter((item) => item.language === code);
      if (entries.length > 0) {
        // Use the first available script as default
        script = entries[0].script;
      }
    } catch (_) {
      /* ignore */
    }
  }
  if (script) {
    candidates.push(path.join(DATA_DIR, `${code}-${script}.json`));
  }
  candidates.push(path.join(DATA_DIR, `${code}.json`));

  for (const filePath of candidates) {
    try {
      const content = await fs.readFile(filePath, 'utf8');
      return JSON.parse(content);
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
  return data.map((item) => item.language).sort();
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
  const data = await getIndexData();
  const entry = data.find((item) => item.language === langCode);
  if (!entry) {
    return null;
  }
  const scripts = entry.scripts || [];
  const chosen = script || scripts[0];
  try {
    return await loadAlphabet(langCode, chosen);
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
  const data = await getIndexData();
  const entry = data.find((item) => item.language === langCode);
  return entry && entry.scripts ? entry.scripts : [];
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
const DEFAULT_FREQ_DIR =
  process.env.WORLDALPHABETS_FREQ_DIR ??
  require('path').resolve(__dirname, 'data', 'freq', 'top200');

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

function detectLanguages(text, candidateLangs, priors = {}, topk = 3) {
  const dir = process.env.WORLDALPHABETS_FREQ_DIR ?? DEFAULT_FREQ_DIR;
  const wordTokens = tokenizeWords(text);
  const bigramTokens = tokenizeBigrams(text);
  const results = [];
  for (const lang of candidateLangs) {
    const data = loadRankData(lang, dir);
    const tokens = data.mode === 'bigram' ? bigramTokens : wordTokens;
    let ov = 0;
    if (data.ranks.size > 0 && tokens.size > 0) {
      ov = overlap(tokens, data.ranks);
      ov /= Math.sqrt(tokens.size + 3);
    }
    const score = PRIOR_WEIGHT * (priors[lang] || 0) + FREQ_WEIGHT * ov;
    if (score > 0.05) results.push([lang, score]);
  }
  results.sort((a, b) => b[1] - a[1]);
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
