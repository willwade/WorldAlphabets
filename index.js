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

/**
 * Detect possible languages for a given text based on alphabet coverage.
 * @param {string} text - The text to analyze
 * @returns {Promise<string[]>} Array of language codes that could represent the text
 */
async function detectLanguages(text) {
  if (!text) return [];

  const letters = new Set(
    Array.from(text)
      .filter((ch) => /\p{L}/u.test(ch))
      .map((ch) => stripDiacritics(ch).toLowerCase())
  );
  if (letters.size === 0) return [];

  const data = await getIndexData();
  const candidates = [];
  for (const entry of data) {
    try {
      const alphabet = await loadAlphabet(entry.language, entry.script);
      if (!alphabet || !alphabet.lowercase) {
        continue;
      }
      const available = new Set(
        alphabet.lowercase.map((ch) => stripDiacritics(ch).toLowerCase())
      );
      let ok = true;
      for (const ch of letters) {
        if (!available.has(ch)) {
          ok = false;
          break;
        }
      }
      if (ok) candidates.push(entry.language);
    } catch (error) {
      // Skip languages that can't be loaded or have invalid data
      continue;
    }
  }
  return candidates;
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
