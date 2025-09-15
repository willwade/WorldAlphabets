/**
 * Language Detection Service for WorldAlphabets WebUI
 * Client-side implementation of frequency-based language detection
 */

const PRIOR_WEIGHT = 0.65;
const FREQ_WEIGHT = 0.35;
const CHAR_WEIGHT = 0.2; // Weight for character-based detection fallback
const DETECTION_THRESHOLD = 0.01; // Lowered for testing
const CHAR_DETECTION_THRESHOLD = 0.02; // Lower threshold for character-based detection

class LanguageDetectionService {
  constructor() {
    this.frequencyCache = new Map();
    this.alphabetCache = new Map();
    this.languageNames = new Map();
    this.availableLanguages = [];
    this.frequencyLanguages = new Set(); // Languages that have frequency data
    this.bulkFrequencyData = null; // Cache for bulk-loaded frequency data
    this.bulkAlphabetData = null; // Cache for bulk-loaded alphabet data
    this.charIndex = null; // Character-based index for fast lookups
    this.scriptIndex = null; // Script-based index for filtering
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

      // Load frequency data availability index
      console.log('Loading frequency data index...');
      const freqIndexResponse = await fetch('./data/freq_index.json');
      if (freqIndexResponse.ok) {
        const freqLanguages = await freqIndexResponse.json();
        this.frequencyLanguages = new Set(freqLanguages);
        console.log('Frequency data available for:', this.frequencyLanguages.size, 'languages');
      } else {
        // If index loading fails, assume no frequency data is available
        // This will cause all languages to fall back to character-based detection
        console.warn('Failed to load frequency data index - falling back to character-based detection only');
        this.frequencyLanguages = new Set();
      }

      // Load available languages from index data (includes both frequency and alphabet-only languages)
      const indexResponse = await fetch('./data/index.json');
      if (indexResponse.ok) {
        const indexData = await indexResponse.json();
        this.availableLanguages = [...new Set(indexData.map(item => item.language))];
        console.log('Loaded languages from index:', this.availableLanguages.length);
      } else {
        // Fallback to curated list if index loading fails
        this.availableLanguages = [
          'af', 'am', 'ar', 'ast', 'ay', 'ban', 'bg', 'bn', 'bo', 'ca', 'ceb', 'chr',
          'ckb', 'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa',
          'fi', 'fo', 'fr', 'fur', 'ga', 'gd', 'gl', 'gn', 'gu', 'haw', 'he', 'hr',
          'hu', 'ie', 'is', 'it', 'ja', 'jv', 'ka', 'kab', 'km', 'kn', 'ko', 'ksh',
          'la', 'lij', 'lo', 'lt', 'lv', 'lzh', 'mk', 'ml', 'mn', 'my', 'nds', 'nn',
          'no', 'oc', 'or', 'pl', 'ps', 'pt', 'ro', 'ru', 'si', 'sl', 'so', 'sr',
          'su', 'sv', 'szl', 'ta', 'te', 'th', 'ti', 'tl', 'tn', 'tr', 'uk', 'ur',
          'vec', 'zh',
          // Add some languages without frequency data for character-based detection
          'ab', 'cop', 'vai', 'gez', 'ba'
        ];
        console.log('Using fallback language list');
      }

      console.log(`Language detection initialized with ${this.availableLanguages.length} languages`);

      // Test loading a sample frequency file to verify data access
      console.log('Testing frequency data access...');
      const testResult = await this.loadFrequencyData('de');
      console.log('Test frequency data loaded:', testResult.mode, 'mode,', testResult.ranks.size, 'tokens');

      // Load character and script indexes for faster detection
      await this.loadIndexes();

      // Preload common frequency data for better performance
      await this.preloadCommonFrequencyData();

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
   * Tokenize text into characters (for character-based detection)
   */
  tokenizeCharacters(text) {
    const normalized = text.normalize('NFKC').toLowerCase();
    return new Set(Array.from(normalized).filter(ch => /\p{L}/u.test(ch)));
  }

  /**
   * Calculate character overlap score between text characters and alphabet characters
   */
  characterOverlap(textChars, alphabetChars) {
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

  /**
   * Calculate weighted overlap using character frequencies
   */
  frequencyOverlap(textChars, charFrequencies) {
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

  /**
   * Load alphabet data for a specific language
   */
  async loadAlphabetData(languageCode) {
    if (this.alphabetCache.has(languageCode)) {
      return this.alphabetCache.get(languageCode);
    }

    try {
      // Try script-specific file first (from index)
      const indexResponse = await fetch('./data/index.json');
      if (indexResponse.ok) {
        const indexData = await indexResponse.json();
        const entry = indexData.find(item => item.language === languageCode);
        if (entry && entry.script) {
          const scriptFile = `./data/alphabets/${languageCode}-${entry.script}.json`;
          const scriptResponse = await fetch(scriptFile);
          if (scriptResponse.ok) {
            const data = await scriptResponse.json();
            this.alphabetCache.set(languageCode, data);
            return data;
          }
        }
      }

      // Fall back to legacy file
      const legacyFile = `./data/alphabets/${languageCode}.json`;
      const legacyResponse = await fetch(legacyFile);
      if (legacyResponse.ok) {
        const data = await legacyResponse.json();
        this.alphabetCache.set(languageCode, data);
        return data;
      }

      this.alphabetCache.set(languageCode, null);
      return null;
    } catch (error) {
      console.warn(`Failed to load alphabet data for ${languageCode}:`, error);
      this.alphabetCache.set(languageCode, null);
      return null;
    }
  }

  /**
   * Load character and script indexes for faster detection
   */
  async loadIndexes() {
    try {
      console.log('Loading character and script indexes...');

      // Load character index
      const charResponse = await fetch('./data/char_index.json');
      if (charResponse.ok) {
        this.charIndex = await charResponse.json();
        console.log(`Character index loaded: ${this.charIndex.metadata.total_characters} characters, ${this.charIndex.metadata.total_languages} languages`);
      } else {
        console.warn('Character index not available, falling back to individual alphabet files');
      }

      // Load script index
      const scriptResponse = await fetch('./data/script_index.json');
      if (scriptResponse.ok) {
        this.scriptIndex = await scriptResponse.json();
        console.log(`Script index loaded: ${this.scriptIndex.metadata.total_scripts} scripts`);
      } else {
        console.warn('Script index not available');
      }

    } catch (error) {
      console.warn('Failed to load indexes:', error);
    }
  }

  /**
   * Preload frequency data for common languages to improve performance
   */
  async preloadCommonFrequencyData() {
    const commonLanguages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ar'];
    const preloadPromises = [];

    for (const lang of commonLanguages) {
      if (this.frequencyLanguages.has(lang) && !this.frequencyCache.has(lang)) {
        preloadPromises.push(this.loadFrequencyData(lang));
      }
    }

    if (preloadPromises.length > 0) {
      console.log(`Preloading frequency data for ${preloadPromises.length} common languages...`);
      await Promise.all(preloadPromises);
      console.log('Common frequency data preloaded');
    }
  }

  /**
   * Load frequency data for a specific language
   */
  async loadFrequencyData(languageCode) {
    if (this.frequencyCache.has(languageCode)) {
      return this.frequencyCache.get(languageCode);
    }

    // Check if this language has frequency data available
    if (!this.frequencyLanguages.has(languageCode)) {
      // Return empty data immediately for languages without frequency data
      const emptyData = { mode: 'word', ranks: new Map() };
      this.frequencyCache.set(languageCode, emptyData);
      return emptyData;
    }

    try {
      const response = await fetch(`./data/freq/top1000/${languageCode}.txt`);
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
   * Get candidate languages based on character analysis
   */
  getCandidateLanguagesFromText(text) {
    if (!this.charIndex) {
      return this.availableLanguages; // Fallback to all languages
    }

    const textChars = this.tokenizeCharacters(text);
    const candidateLanguages = new Set();

    // Find languages that contain the characters in the text
    for (const char of textChars) {
      const languages = this.charIndex.char_to_languages[char];
      if (languages) {
        for (const lang of languages) {
          candidateLanguages.add(lang);
        }
      }
    }

    // If no candidates found, fall back to all languages
    if (candidateLanguages.size === 0) {
      return this.availableLanguages;
    }

    // Convert to array and prioritize common languages
    const commonLanguages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ar', 'hi', 'ko'];
    const candidates = Array.from(candidateLanguages);

    return [
      ...candidates.filter(lang => commonLanguages.includes(lang)),
      ...candidates.filter(lang => !commonLanguages.includes(lang))
    ];
  }

  /**
   * Detect languages in the given text
   */
  async detectLanguages(text, options = {}) {
    const {
      candidateLanguages = null,
      priors = {},
      topK = 5,
      onProgress = null
    } = options;

    console.log('Starting detection for text:', text);

    if (!text || text.trim().length === 0) {
      console.log('Empty text, returning no results');
      return [];
    }

    // Use character-based candidate filtering if no candidates provided
    const actualCandidates = candidateLanguages || this.getCandidateLanguagesFromText(text);
    console.log('Candidate languages:', actualCandidates.length);

    // Prioritize common languages for faster detection
    const commonLanguages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ar', 'hi', 'ko'];
    const prioritizedLanguages = [
      ...actualCandidates.filter(lang => commonLanguages.includes(lang)),
      ...actualCandidates.filter(lang => !commonLanguages.includes(lang))
    ];

    const wordTokens = this.tokenizeWords(text);
    const bigramTokens = this.tokenizeBigrams(text);
    const textChars = this.tokenizeCharacters(text);

    console.log('Word tokens:', Array.from(wordTokens));
    console.log('Bigram tokens:', Array.from(bigramTokens));
    console.log('Text characters:', Array.from(textChars));

    const results = [];
    const wordBasedLangs = new Set(); // Track which languages used word-based detection

    // Report initial progress
    if (onProgress) {
      onProgress({
        status: 'Starting language detection...',
        percentage: 0,
        processed: 0,
        total: prioritizedLanguages.length
      });
    }

    // Early termination: if we find a very high confidence match, stop processing
    const HIGH_CONFIDENCE_THRESHOLD = 0.8;
    let foundHighConfidenceMatch = false;

    // Process languages in batches to avoid blocking the UI
    const batchSize = 10;
    let processedCount = 0;

    for (let i = 0; i < prioritizedLanguages.length && !foundHighConfidenceMatch; i += batchSize) {
      const batch = prioritizedLanguages.slice(i, i + batchSize);
      console.log(`Processing batch ${Math.floor(i/batchSize) + 1}:`, batch);

      // Update progress at start of batch
      if (onProgress) {
        onProgress({
          status: `Processing languages ${i + 1}-${Math.min(i + batchSize, prioritizedLanguages.length)}...`,
          percentage: (processedCount / prioritizedLanguages.length) * 100,
          processed: processedCount,
          total: prioritizedLanguages.length
        });
      }

      for (const languageCode of batch) {
        try {
          // Try word-based detection first
          const frequencyData = await this.loadFrequencyData(languageCode);
          const tokens = frequencyData.mode === 'bigram' ? bigramTokens : wordTokens;

          let wordOverlap = 0;
          if (frequencyData.ranks.size > 0 && tokens.size > 0) {
            wordOverlap = this.calculateOverlap(tokens, frequencyData.ranks);
            wordOverlap /= Math.sqrt(tokens.size + 3);
          }

          const prior = priors[languageCode] || 0;
          const wordScore = PRIOR_WEIGHT * prior + FREQ_WEIGHT * wordOverlap;

          // If word-based detection succeeds, use it and mark as word-based
          if (wordScore > DETECTION_THRESHOLD) {
            console.log(`${languageCode}: word-based score=${wordScore.toFixed(3)}, overlap=${wordOverlap.toFixed(3)}, freq_size=${frequencyData.ranks.size}`);
            results.push({
              language: languageCode,
              languageName: this.languageNames.get(languageCode) || languageCode,
              confidence: wordScore,
              mode: frequencyData.mode,
              tokenCount: tokens.size,
              matchingTokens: this.getMatchingTokens(tokens, frequencyData.ranks),
              detectionType: 'word-based'
            });
            wordBasedLangs.add(languageCode);

            // Check for early termination
            if (wordScore > HIGH_CONFIDENCE_THRESHOLD) {
              console.log(`High confidence match found for ${languageCode} (${wordScore.toFixed(3)}), terminating early`);
              foundHighConfidenceMatch = true;
              break;
            }
            continue;
          }

          // Fallback to character-based detection
          if (textChars.size > 0) {
            const alphabetData = await this.loadAlphabetData(languageCode);
            if (alphabetData) {
              // Get character sets
              const lowercaseChars = new Set(alphabetData.lowercase || []);
              const charFrequencies = alphabetData.frequency || {};

              // Calculate character-based scores
              const charOverlapScore = this.characterOverlap(textChars, lowercaseChars);
              const freqOverlapScore = this.frequencyOverlap(textChars, charFrequencies);

              // Combine character overlap and frequency overlap
              const charScore = charOverlapScore * 0.6 + freqOverlapScore * 0.4;

              // Apply character-based weight
              const finalCharScore = PRIOR_WEIGHT * prior + CHAR_WEIGHT * charScore;

              // Use a lower threshold for character-based detection
              if (finalCharScore > CHAR_DETECTION_THRESHOLD) {
                console.log(`${languageCode}: char-based score=${finalCharScore.toFixed(3)}, char_overlap=${charOverlapScore.toFixed(3)}, freq_overlap=${freqOverlapScore.toFixed(3)}`);
                results.push({
                  language: languageCode,
                  languageName: this.languageNames.get(languageCode) || languageCode,
                  confidence: finalCharScore,
                  mode: 'character',
                  tokenCount: textChars.size,
                  matchingTokens: [...textChars].filter(ch => lowercaseChars.has(ch)),
                  detectionType: 'character-based'
                });
              }
            }
          }
        } catch (error) {
          console.warn(`Error processing language ${languageCode}:`, error);
        }

        processedCount++;
      }

      // Allow UI to update between batches
      if (i + batchSize < prioritizedLanguages.length && !foundHighConfidenceMatch) {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }

    // Final progress update
    if (onProgress) {
      onProgress({
        status: foundHighConfidenceMatch ? 'High confidence match found!' : 'Finalizing results...',
        percentage: 100,
        processed: prioritizedLanguages.length,
        total: prioritizedLanguages.length
      });
    }

    console.log('Detection complete. Results found:', results.length);

    // Sort results, but prioritize word-based detections over character-based ones
    results.sort((a, b) => {
      const adjustedScoreA = wordBasedLangs.has(a.language) ? a.confidence + 0.01 : a.confidence;
      const adjustedScoreB = wordBasedLangs.has(b.language) ? b.confidence + 0.01 : b.confidence;
      return adjustedScoreB - adjustedScoreA;
    });

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
