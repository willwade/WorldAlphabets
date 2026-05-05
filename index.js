const fs = require('fs/promises');
const path = require('path');

const DATA_DIR = path.join(__dirname, 'data', 'alphabets');
const FREQ_DIR = path.join(__dirname, 'data', 'freq', 'top1000');
const INFLECTION_DIR = path.join(__dirname, 'data', 'inflections');

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
  const codes = data.map((item) => item.language);
  return Array.from(new Set(codes)).sort();
}

/**
 * Loads the Top-1000 frequency tokens for a language.
 * @param {string} code - The ISO language code.
 * @returns {Promise<{language: string, tokens: string[], mode: 'word' | 'bigram'}>}
 */
async function loadFrequencyList(code) {
  const filePath = path.join(FREQ_DIR, `${code}.txt`);
  let content;
  try {
    content = await fs.readFile(filePath, 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new Error(`Frequency list for code "${code}" not found.`);
    }
    throw error;
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

  return { language: code, tokens, mode };
}

const inflectionCache = new Map();

function clearInflectionCache() {
  inflectionCache.clear();
}

async function loadInflectionIndex() {
  if (inflectionCache.has('__index__')) {
    return inflectionCache.get('__index__');
  }
  const filePath = path.join(INFLECTION_DIR, 'index.json');
  let data;
  try {
    const content = await fs.readFile(filePath, 'utf8');
    data = JSON.parse(content);
  } catch (error) {
    if (error.code === 'ENOENT') {
      data = { _type: 'inflection_index', _version: '0.1', locales: {} };
    } else {
      throw error;
    }
  }
  inflectionCache.set('__index__', data);
  return data;
}

async function getAvailableInflectionLocales() {
  const index = await loadInflectionIndex();
  const locales = index.locales || {};
  return Object.keys(locales).sort();
}

async function loadInflectionFile(locale, filename) {
  const cacheKey = `${locale}/${filename}`;
  if (inflectionCache.has(cacheKey)) {
    return inflectionCache.get(cacheKey);
  }
  let filePath = path.join(INFLECTION_DIR, locale, filename);
  let fallbackPath = null;
  if (locale.includes('-')) {
    fallbackPath = path.join(INFLECTION_DIR, locale.split('-')[0], filename);
  }
  let data;
  try {
    const content = await fs.readFile(filePath, 'utf8');
    data = JSON.parse(content);
  } catch (error) {
    if (error.code === 'ENOENT' && fallbackPath) {
      try {
        const content = await fs.readFile(fallbackPath, 'utf8');
        data = JSON.parse(content);
      } catch (fallbackError) {
        if (fallbackError.code !== 'ENOENT') throw fallbackError;
      }
    }
    if (!data) {
      if (error.code === 'ENOENT') {
        throw new Error(`Inflection data for locale "${locale}" not found.`);
      }
      throw error;
    }
  }
  inflectionCache.set(cacheKey, data);
  return data;
}

async function loadInflectionWords(locale) {
  return loadInflectionFile(locale, 'words.json');
}

async function loadInflectionRules(locale) {
  return loadInflectionFile(locale, 'rules.json');
}

async function loadInflectionData(locale) {
  return {
    words: await loadInflectionWords(locale),
    rules: await loadInflectionRules(locale),
  };
}

async function getWordForms(locale, word) {
  const words = await loadInflectionWords(locale);
  const entry = words[word];
  return entry && typeof entry === 'object' ? entry : null;
}

async function inflectWord(locale, word, inflection) {
  const entry = await getWordForms(locale, word);
  if (!entry) return null;
  if (inflection === 'base') return entry.base || word;
  const forms = entry.inflections || {};
  const value = forms[inflection];
  return typeof value === 'string' ? value : null;
}

async function getInflectionSummary(locale) {
  const wordsData = await loadInflectionWords(locale);
  const rulesData = await loadInflectionRules(locale);
  const posTypes = new Set();
  const inflectionKeys = new Set();
  let wordCount = 0;
  for (const [key, entry] of Object.entries(wordsData)) {
    if (key.startsWith('_') || typeof entry !== 'object' || !entry) continue;
    wordCount++;
    if (Array.isArray(entry.types)) posTypes.add(...entry.types);
    if (entry.inflections && typeof entry.inflections === 'object') {
      for (const k of Object.keys(entry.inflections)) {
        if (k !== 'regulars') inflectionKeys.add(k);
      }
    }
  }
  const rules = rulesData.rules || [];
  const tests = rulesData.tests || [];
  return {
    locale,
    wordCount,
    ruleCount: Array.isArray(rules) ? rules.length : 0,
    testCount: Array.isArray(tests) ? tests.length : 0,
    posTypes: [...posTypes].sort(),
    inflectionKeys: [...inflectionKeys].sort(),
  };
}

function itemMatches(check, item) {
  let label = String(item.word || '').toLowerCase();
  let matching = true;
  if (Array.isArray(check.words)) {
    matching = check.words.includes(label);
  } else if (typeof check.type === 'string') {
    matching = Array.isArray(item.types) && item.types.includes(check.type);
  }
  if (matching && typeof check.match === 'string') {
    matching = new RegExp(check.match).test(label);
  }
  if (matching && typeof check.non_match === 'string') {
    matching = !new RegExp(check.non_match).test(label);
  }
  return matching;
}

function matchesRule(rule, buttons) {
  const lookback = rule.lookback || [];
  if (!Array.isArray(lookback)) return false;
  let historyIdx = buttons.length - 1;
  let valid = true;
  const condenses = [];
  for (let idx = lookback.length - 1; idx >= 0; idx--) {
    const check = lookback[idx];
    const preCheck = idx > 0 ? lookback[idx - 1] : null;
    if (!check || typeof check !== 'object') return false;
    const item = historyIdx >= 0 ? buttons[historyIdx] : null;
    if (item === null || item === undefined) {
      if (!check.optional) valid = false;
    } else {
      let matching = itemMatches(check, item);
      const preMatching = preCheck && typeof preCheck === 'object' && itemMatches(preCheck, item);
      const preOptional = preCheck && typeof preCheck === 'object' ? preCheck.optional : null;
      if (matching && check.optional && preMatching && !preOptional) {
        matching = false;
      }
      if (matching) {
        if (check.condense) condenses.push(historyIdx);
        historyIdx--;
      } else if (!check.optional) {
        valid = false;
      }
    }
    if (!valid) break;
  }
  if (valid && condenses.length > 0) {
    return { condense_items: condenses };
  }
  return valid;
}

function buildWordList(wordsData) {
  const words = [];
  for (const [word, entry] of Object.entries(wordsData)) {
    if (word.startsWith('_') || typeof entry !== 'object' || !entry) continue;
    words.push({ ...entry, word });
  }
  return words;
}

function lookupWordSync(wordsData, rulesData, word, priorWords = '') {
  const words = buildWordList(wordsData);
  const rules = Array.isArray(rulesData.rules) ? rulesData.rules : [];

  const priorButtons = priorWords.split(/\s+/).filter(Boolean).map(part => {
    return words.find(w => w.word === part) || { word: part };
  });

  const foundWords = words.filter(w => w.word === word);
  if (foundWords.length === 0) {
    return { word, replacement: null, rule_id: null, rule_type: null, inflection: null, condense_items: null };
  }

  const foundTypes = {};
  const matchingRules = [];
  for (const rule of rules) {
    if (!rule || typeof rule !== 'object') continue;
    const ruleType = rule.type;
    if (typeof ruleType !== 'string') continue;
    if (foundTypes[ruleType] && ruleType !== 'override') continue;
    const matches = matchesRule(rule, priorButtons);
    if (matches) {
      const matched = { ...rule };
      if (typeof matches === 'object' && matches.condense_items) {
        matched.condense_items = matches.condense_items;
      }
      matchingRules.push(matched);
      foundTypes[ruleType] = true;
    }
  }

  const first = { ...foundWords[0] };
  const inflections = {};
  for (const rule of matchingRules) {
    if (rule.type === 'override' && rule.overrides && typeof rule.overrides === 'object') {
      for (const [key, value] of Object.entries(rule.overrides)) {
        if (!inflections[key]) {
          inflections[key] = { type: 'override', word: value, id: rule.id, condense_items: rule.condense_items };
        }
      }
    } else {
      const rt = rule.type;
      if (typeof rt === 'string') inflections[rt] = rule;
    }
  }

  let replacement = null;
  let ruleId = null;
  let ruleType = null;
  let inflection = null;
  let condenseItems = null;

  const wordValue = first.word;
  const direct = typeof wordValue === 'string' ? inflections[wordValue] : null;
  if (direct && typeof direct === 'object' && direct.word) {
    replacement = direct.word;
    ruleId = direct.id || null;
    condenseItems = direct.condense_items || null;
  } else {
    let replacementRule = null;
    const types = Array.isArray(first.types) ? first.types : [];
    for (const part of types) {
      if (inflections[part] && !replacementRule) {
        replacementRule = inflections[part];
      }
    }
    if (replacementRule && typeof replacementRule === 'object') {
      const forms = first.inflections || {};
      const infl = replacementRule.inflection;
      if (forms && typeof forms === 'object' && typeof infl === 'string') {
        replacement = forms[infl] || first.word;
        inflection = infl;
      } else {
        replacement = first.word;
      }
      ruleId = replacementRule.id || null;
      ruleType = infl || null;
      condenseItems = replacementRule.condense_items || null;
    }
  }

  return { word, replacement, rule_id: ruleId, rule_type: ruleType, inflection, condense_items: condenseItems };
}

async function lookupWord(locale, word, priorWords = '') {
  const wordsData = await loadInflectionWords(locale);
  const rulesData = await loadInflectionRules(locale);
  return lookupWordSync(wordsData, rulesData, word, priorWords);
}

async function applyRules(locale, text) {
  const tokens = text.split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return text;
  const wordsData = await loadInflectionWords(locale);
  const rulesData = await loadInflectionRules(locale);
  const results = [];
  for (let i = 0; i < tokens.length; i++) {
    const prior = tokens.slice(0, i).join(' ');
    const result = lookupWordSync(wordsData, rulesData, tokens[i], prior);
    if (result.replacement) {
      if (result.condense_items && result.condense_items.length > 0) {
        const kept = results.filter((_, idx) => !result.condense_items.includes(idx));
        results.length = 0;
        results.push(...kept);
        results.push(result.replacement);
      } else {
        results.push(result.replacement);
      }
    } else {
      results.push(tokens[i]);
    }
  }
  return results.join(' ');
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
  // Collect all unique scripts for this language across all entries
  const scripts = new Set();
  for (const entry of data) {
    if (entry.language === langCode) {
      if (entry.script) {
        scripts.add(entry.script);
      }
      if (entry.scripts) {
        for (const s of entry.scripts) {
          scripts.add(s);
        }
      }
    }
  }
  return Array.from(scripts).sort();
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
  // Inflections
  getAvailableInflectionLocales,
  loadInflectionWords,
  loadInflectionRules,
  loadInflectionData,
  getWordForms,
  inflectWord,
  getInflectionSummary,
  lookupWord,
  applyRules,
  clearInflectionCache,
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
