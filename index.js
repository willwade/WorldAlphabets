const fs = require('fs/promises');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'alphabets');

/**
 * Loads the alphabet data for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<object>} A promise that resolves to the alphabet data.
 */
async function loadAlphabet(code) {
  const filePath = path.join(DATA_DIR, `${code}.json`);
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new Error(`Alphabet data for code "${code}" not found.`);
    }
    throw error;
  }
}

/**
 * Gets the uppercase alphabet for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<string[]>} A promise that resolves to an array of uppercase letters.
 */
async function getUppercase(code) {
  const data = await loadAlphabet(code);
  return data.uppercase || [];
}

/**
 * Gets the lowercase alphabet for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<string[]>} A promise that resolves to an array of lowercase letters.
 */
async function getLowercase(code) {
  const data = await loadAlphabet(code);
  return data.lowercase || [];
}

/**
 * Gets the letter frequency for a given language code.
 * @param {string} code - The ISO 639-1 language code.
 * @returns {Promise<object>} A promise that resolves to an object with letter frequencies.
 */
async function getFrequency(code) {
  const data = await loadAlphabet(code);
  return data.frequency || {};
}

/**
 * Gets all available alphabet codes.
 * @returns {Promise<string[]>} A promise that resolves to an array of alphabet codes.
 */
async function getAvailableCodes() {
    const files = await fs.readdir(DATA_DIR);
    return files.map(file => file.replace('.json', ''));
}

module.exports = {
  loadAlphabet,
  getUppercase,
  getLowercase,
  getFrequency,
  getAvailableCodes,
};
