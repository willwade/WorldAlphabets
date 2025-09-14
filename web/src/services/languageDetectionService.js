/**
 * Language Detection Service for WorldAlphabets WebUI
 * Client-side implementation of frequency-based language detection
 */

const PRIOR_WEIGHT = 0.65;
const FREQ_WEIGHT = 0.35;
const DETECTION_THRESHOLD = 0.01; // Lowered for testing

class LanguageDetectionService {
  constructor() {
    this.frequencyCache = new Map();
    this.languageNames = new Map();
    this.availableLanguages = [];
  }

  /**
   * Initialize the service by loading available languages and language names
   */
  async initialize() {
    try {
      console.log('Starting language detection service initialization...');

      // Load language registry for language names
      console.log('Loading language registry...');
      const response = await fetch('./data/language_scripts.json');
      if (!response.ok) {
        throw new Error(`Failed to load language registry: ${response.status}`);
      }
      const languageData = await response.json();
      console.log('Language registry loaded:', Object.keys(languageData).length, 'languages');

      // Build language name mapping
      for (const [code, data] of Object.entries(languageData)) {
        this.languageNames.set(code, data.name || code);
      }

      // Use a curated list of languages we know have frequency data
      // This is more reliable than trying to parse build reports
      this.availableLanguages = [
        'af', 'am', 'ar', 'ast', 'ay', 'ban', 'bg', 'bn', 'bo', 'ca', 'ceb', 'chr',
        'ckb', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa',
        'fi', 'fo', 'fr', 'fur', 'ga', 'gd', 'gl', 'gn', 'gu', 'haw', 'he', 'hr',
        'hu', 'ie', 'is', 'it', 'ja', 'jv', 'ka', 'kab', 'km', 'kn', 'ko', 'ksh',
        'la', 'lij', 'lo', 'lt', 'lv', 'lzh', 'mk', 'ml', 'mn', 'my', 'nds', 'nn',
        'no', 'oc', 'or', 'pl', 'ps', 'pt', 'ro', 'ru', 'si', 'sl', 'so', 'sr',
        'su', 'sv', 'szl', 'ta', 'te', 'th', 'ti', 'tl', 'tn', 'tr', 'uk', 'ur',
        'vec', 'zh'
      ];

      console.log(`Language detection initialized with ${this.availableLanguages.length} languages`);

      // Test loading a sample frequency file to verify data access
      console.log('Testing frequency data access...');
      const testResult = await this.loadFrequencyData('de');
      console.log('Test frequency data loaded:', testResult.mode, 'mode,', testResult.ranks.size, 'tokens');

    } catch (error) {
      console.error('Failed to initialize language detection service:', error);
      throw error;
    }
  }

  /**
   * Tokenize text into words (for most languages)
   */
  tokenizeWords(text) {
    const normalized = text.normalize('NFKC').toLowerCase();
    const matches = normalized.match(/\p{L}+/gu) || [];
    return new Set(matches);
  }

  /**
   * Tokenize text into character bigrams (for CJK languages)
   */
  tokenizeBigrams(text) {
    const normalized = text.normalize('NFKC').toLowerCase();
    const letters = Array.from(normalized).filter(ch => /\p{L}/u.test(ch));
    const bigrams = new Set();
    for (let i = 0; i < letters.length - 1; i++) {
      bigrams.add(letters[i] + letters[i + 1]);
    }
    return bigrams;
  }

  /**
   * Load frequency data for a specific language
   */
  async loadFrequencyData(languageCode) {
    if (this.frequencyCache.has(languageCode)) {
      return this.frequencyCache.get(languageCode);
    }

    try {
      const response = await fetch(`./data/freq/top200/${languageCode}.txt`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const text = await response.text();
      const lines = text.split(/\r?\n/).filter(line => line.trim());
      
      let mode = 'word';
      let startIndex = 0;
      
      // Check for header indicating bigram mode
      if (lines[0] && lines[0].startsWith('#')) {
        const header = lines[0];
        if (header.includes('bigram')) {
          mode = 'bigram';
        }
        startIndex = 1;
      }
      
      // Build rank map
      const ranks = new Map();
      for (let i = startIndex; i < lines.length; i++) {
        const token = lines[i].trim();
        if (token && !ranks.has(token)) {
          ranks.set(token, i - startIndex + 1);
        }
      }
      
      const data = { mode, ranks };
      this.frequencyCache.set(languageCode, data);
      return data;
    } catch (error) {
      console.warn(`Failed to load frequency data for ${languageCode}:`, error);
      const emptyData = { mode: 'word', ranks: new Map() };
      this.frequencyCache.set(languageCode, emptyData);
      return emptyData;
    }
  }

  /**
   * Calculate overlap score between tokens and frequency ranks
   */
  calculateOverlap(tokens, ranks) {
    let score = 0;
    for (const token of tokens) {
      const rank = ranks.get(token);
      if (rank) {
        score += 1 / Math.log2(rank + 1.5);
      }
    }
    return score;
  }

  /**
   * Detect languages in the given text
   */
  async detectLanguages(text, options = {}) {
    const {
      candidateLanguages = this.availableLanguages,
      priors = {},
      topK = 5
    } = options;

    console.log('Starting detection for text:', text);
    console.log('Candidate languages:', candidateLanguages.length);

    if (!text || text.trim().length === 0) {
      console.log('Empty text, returning no results');
      return [];
    }

    const wordTokens = this.tokenizeWords(text);
    const bigramTokens = this.tokenizeBigrams(text);

    console.log('Word tokens:', Array.from(wordTokens));
    console.log('Bigram tokens:', Array.from(bigramTokens));

    const results = [];

    // Process languages in batches to avoid blocking the UI
    const batchSize = 10;
    for (let i = 0; i < candidateLanguages.length; i += batchSize) {
      const batch = candidateLanguages.slice(i, i + batchSize);
      console.log(`Processing batch ${Math.floor(i/batchSize) + 1}:`, batch);

      for (const languageCode of batch) {
        try {
          const frequencyData = await this.loadFrequencyData(languageCode);
          const tokens = frequencyData.mode === 'bigram' ? bigramTokens : wordTokens;

          let overlap = 0;
          if (frequencyData.ranks.size > 0 && tokens.size > 0) {
            overlap = this.calculateOverlap(tokens, frequencyData.ranks);
            overlap /= Math.sqrt(tokens.size + 3);
          }

          const prior = priors[languageCode] || 0;
          const finalScore = PRIOR_WEIGHT * prior + FREQ_WEIGHT * overlap;

          if (finalScore > DETECTION_THRESHOLD) {
            console.log(`${languageCode}: score=${finalScore.toFixed(3)}, overlap=${overlap.toFixed(3)}, freq_size=${frequencyData.ranks.size}`);
            results.push({
              language: languageCode,
              languageName: this.languageNames.get(languageCode) || languageCode,
              confidence: finalScore,
              mode: frequencyData.mode,
              tokenCount: tokens.size,
              matchingTokens: this.getMatchingTokens(tokens, frequencyData.ranks)
            });
          }
        } catch (error) {
          console.warn(`Error processing language ${languageCode}:`, error);
        }
      }

      // Allow UI to update between batches
      if (i + batchSize < candidateLanguages.length) {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }

    console.log('Detection complete. Results found:', results.length);

    // Sort by confidence and return top results
    results.sort((a, b) => b.confidence - a.confidence);
    return results.slice(0, topK);
  }

  /**
   * Get tokens that match the frequency data (for debugging)
   */
  getMatchingTokens(tokens, ranks) {
    const matching = [];
    for (const token of tokens) {
      if (ranks.has(token)) {
        matching.push(token);
      }
    }
    return matching.slice(0, 10); // Limit to first 10 for display
  }

  /**
   * Get language name for a language code
   */
  getLanguageName(languageCode) {
    return this.languageNames.get(languageCode) || languageCode;
  }

  /**
   * Get list of available languages for detection
   */
  getAvailableLanguages() {
    return this.availableLanguages.slice();
  }
}

// Create singleton instance
const languageDetectionService = new LanguageDetectionService();

export default languageDetectionService;
