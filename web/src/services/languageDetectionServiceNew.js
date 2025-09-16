/**
 * Language Detection Service using WorldAlphabets Browser Interface
 *
 * This service uses the browser-compatible ES module version of WorldAlphabets
 * that shares the same detection algorithm as the Node.js version.
 */

import { detectLanguages, getAvailableCodes, getIndexData } from 'worldalphabets';

class LanguageDetectionService {
  constructor() {
    this.availableLanguages = [];
    this.languageIndex = new Map();
    this.initialized = false;
  }

  /**
   * Initialize the service by loading available languages
   */
  async initialize() {
    if (this.initialized) return;

    try {
      // Use the browser-compatible functions
      this.availableLanguages = await getAvailableCodes();
      const indexData = await getIndexData();

      this.languageIndex = new Map(
        indexData.map(item => [item.language, item])
      );

      this.initialized = true;
      console.log(`Language detection service initialized with ${this.availableLanguages.length} languages`);
    } catch (error) {
      console.error('Failed to initialize language detection service:', error);
      throw error;
    }
  }

  /**
   * Detect languages in the given text using the browser-compatible interface
   */
  async detectLanguages(text, candidateLanguages = null, topK = 5, progressCallback = null) {
    await this.initialize();

    // Double-check initialization
    if (!this.availableLanguages || !Array.isArray(this.availableLanguages)) {
      console.error('Service not properly initialized. availableLanguages:', this.availableLanguages);
      throw new Error('Language detection service not properly initialized');
    }

    if (!text || text.trim().length === 0) {
      return [];
    }

    try {
      if (progressCallback) {
        progressCallback({
          status: 'Analyzing text...',
          percentage: 0,
          processed: 0,
          total: 0,
          emoji: '🔍'
        });
      }

      // Use smart candidate filtering if no candidates specified
      // The optimized module will automatically filter candidates if null is passed
      const candidates = candidateLanguages; // Let the module handle smart filtering

      if (progressCallback) {
        progressCallback({
          status: 'Analyzing text and selecting candidates...',
          percentage: 25,
          processed: 0,
          total: 20, // Estimated candidate count
          emoji: '🔍'
        });
      }

      // Use the browser-compatible detectLanguages function
      const results = await detectLanguages(text, candidates, {}, topK);

      if (progressCallback) {
        progressCallback({
          status: 'Formatting results...',
          percentage: 75,
          processed: 20,
          total: 20,
          emoji: '📊'
        });
      }

      // Format results to match the expected webUI format
      const formattedResults = results.map(([langCode, confidence]) => {
        const languageInfo = this.languageIndex.get(langCode);
        return {
          language: langCode,
          confidence: confidence, // Keep as decimal (0-1) to match Vue component expectation
          name: languageInfo?.name || langCode,
          script: languageInfo?.script || 'Unknown',
          mode: confidence > 0.05 ? 'word' : 'character', // Estimate mode based on confidence
          tokenCount: Math.floor(confidence * 100), // Match Vue component property name
          matchingTokens: [] // Match Vue component property name
        };
      });

      if (progressCallback) {
        progressCallback({
          status: `Found ${formattedResults.length} matches`,
          percentage: 100,
          processed: 20,
          total: 20,
          emoji: '✅'
        });
      }

      return formattedResults;

    } catch (error) {
      console.error('Language detection failed:', error);
      if (progressCallback) {
        progressCallback({
          status: 'Detection failed',
          percentage: 100,
          processed: 0,
          total: 0,
          emoji: '❌'
        });
      }
      throw error;
    }
  }

  /**
   * Get available languages
   * @returns {Array} Array of available language codes
   */
  getAvailableLanguages() {
    return this.availableLanguages;
  }

  /**
   * Get language information
   * @param {string} langCode - Language code
   * @returns {Object|null} Language information or null if not found
   */
  getLanguageInfo(langCode) {
    return this.languageIndex.get(langCode) || null;
  }
}

// Export singleton instance
export default new LanguageDetectionService();
