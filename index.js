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
      const entry = data.find((item) => item.language === code);
      if (entry && entry.scripts && entry.scripts.length > 0) {
        script = entry.scripts[0];
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

const keyboards = require('./keyboards');

module.exports = {
  // Alphabets
  loadAlphabet,
  getUppercase,
  getLowercase,
  getFrequency,
  getAvailableCodes,
  getIndexData,
  getLanguage,
  getScripts,
  // Keyboards
  ...keyboards,
};
