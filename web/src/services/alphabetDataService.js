/**
 * Service for loading and enriching alphabet data with TTS and keyboard information
 */

class AlphabetDataService {
  constructor() {
    this.baseUrl = import.meta.env.BASE_URL;
    this.cache = {
      alphabets: null,
      ttsIndex: null,
      keyboardLayouts: null,
      enrichedData: null
    };
  }

  /**
   * Load the main alphabet index
   */
  async loadAlphabets() {
    if (this.cache.alphabets) {
      return this.cache.alphabets;
    }

    try {
      const response = await fetch(`${this.baseUrl}data/index.json`);
      if (!response.ok) {
        throw new Error('Failed to load alphabet index');
      }
      this.cache.alphabets = await response.json();
      return this.cache.alphabets;
    } catch (error) {
      console.error('Error loading alphabets:', error);
      throw error;
    }
  }

  /**
   * Load the TTS index
   */
  async loadTTSIndex() {
    if (this.cache.ttsIndex) {
      return this.cache.ttsIndex;
    }

    try {
      const response = await fetch(`${this.baseUrl}data/tts_index.json`);
      if (!response.ok) {
        throw new Error('Failed to load TTS index');
      }
      this.cache.ttsIndex = await response.json();
      return this.cache.ttsIndex;
    } catch (error) {
      console.error('Error loading TTS index:', error);
      throw error;
    }
  }

  /**
   * Load the keyboard layouts index
   */
  async loadKeyboardLayouts() {
    if (this.cache.keyboardLayouts) {
      return this.cache.keyboardLayouts;
    }

    try {
      const response = await fetch(`${this.baseUrl}data/layouts/index.json`);
      if (!response.ok) {
        throw new Error('Failed to load keyboard layouts');
      }
      this.cache.keyboardLayouts = await response.json();
      return this.cache.keyboardLayouts;
    } catch (error) {
      console.error('Error loading keyboard layouts:', error);
      throw error;
    }
  }

  /**
   * Get enriched alphabet data with TTS and keyboard availability
   */
  async getEnrichedAlphabetData() {
    if (this.cache.enrichedData) {
      return this.cache.enrichedData;
    }

    try {
      const [alphabets, ttsIndex, keyboardLayouts] = await Promise.all([
        this.loadAlphabets(),
        this.loadTTSIndex(),
        this.loadKeyboardLayouts()
      ]);

      // Create a set of languages that have TTS available
      const ttsLanguages = new Set(Object.keys(ttsIndex));

      // Create a set of language codes that have keyboard layouts available
      // The layouts/index.json has language codes as keys
      const keyboardLanguages = new Set(Object.keys(keyboardLayouts));

      // Enrich alphabet data
      this.cache.enrichedData = alphabets.map(alphabet => {
        const languageCode = alphabet.language;

        // Check TTS availability
        const hasTTS = ttsLanguages.has(languageCode);

        // Check keyboard availability using language code
        const hasKeyboard = keyboardLanguages.has(languageCode);

        return {
          ...alphabet,
          hasTTS,
          hasKeyboard,
          // Add computed display fields
          scriptType: this.getScriptTypeName(alphabet.script),
          displayName: `${alphabet.name} (${alphabet.script})`
        };
      });

      return this.cache.enrichedData;
    } catch (error) {
      console.error('Error enriching alphabet data:', error);
      throw error;
    }
  }

  /**
   * Get human-readable script type name
   */
  getScriptTypeName(script) {
    const scriptNames = {
      'Latn': 'Latin',
      'Cyrl': 'Cyrillic',
      'Arab': 'Arabic',
      'Deva': 'Devanagari',
      'Beng': 'Bengali',
      'Grek': 'Greek',
      'Hebr': 'Hebrew',
      'Thai': 'Thai',
      'Khmr': 'Khmer',
      'Mymr': 'Myanmar',
      'Ethi': 'Ethiopic',
      'Geor': 'Georgian',
      'Armn': 'Armenian',
      'Hira': 'Hiragana',
      'Kana': 'Katakana',
      'Jpan': 'Japanese',
      'Hans': 'Simplified Chinese',
      'Hant': 'Traditional Chinese',
      'Hang': 'Hangul',
      'Kore': 'Korean',
      'Tibt': 'Tibetan',
      'Sinh': 'Sinhala',
      'Taml': 'Tamil',
      'Telu': 'Telugu',
      'Knda': 'Kannada',
      'Mlym': 'Malayalam',
      'Orya': 'Oriya',
      'Gujr': 'Gujarati',
      'Guru': 'Gurmukhi'
    };
    
    return scriptNames[script] || script;
  }

  /**
   * Search and filter alphabets
   */
  async searchAlphabets(options = {}) {
    const {
      searchTerm = '',
      filters = {},
      sortBy = 'name',
      sortOrder = 'asc',
      page = 1,
      pageSize = 50
    } = options;

    const enrichedData = await this.getEnrichedAlphabetData();
    
    // Apply search
    let filteredData = enrichedData;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filteredData = enrichedData.filter(alphabet => 
        alphabet.name.toLowerCase().includes(term) ||
        alphabet.language.toLowerCase().includes(term) ||
        alphabet.scriptType.toLowerCase().includes(term) ||
        (alphabet.iso639_3 && alphabet.iso639_3.toLowerCase().includes(term))
      );
    }

    // Apply filters - only filter if explicitly set to true (checked)
    if (filters.hasTTS === true) {
      filteredData = filteredData.filter(alphabet => alphabet.hasTTS === true);
    }

    if (filters.hasFrequency === true) {
      filteredData = filteredData.filter(alphabet => alphabet.hasFrequency === true);
    }

    if (filters.hasKeyboard === true) {
      filteredData = filteredData.filter(alphabet => alphabet.hasKeyboard === true);
    }

    if (filters.scriptType) {
      filteredData = filteredData.filter(alphabet => alphabet.script === filters.scriptType);
    }

    // Apply sorting
    filteredData.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (sortOrder === 'desc') {
        return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
      } else {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      }
    });

    // Apply pagination
    const totalItems = filteredData.length;
    const totalPages = Math.ceil(totalItems / pageSize);
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = filteredData.slice(startIndex, endIndex);

    return {
      data: paginatedData,
      pagination: {
        currentPage: page,
        pageSize,
        totalItems,
        totalPages,
        hasNextPage: page < totalPages,
        hasPreviousPage: page > 1
      }
    };
  }

  /**
   * Get available script types for filtering
   */
  async getAvailableScriptTypes() {
    const enrichedData = await this.getEnrichedAlphabetData();
    const scriptTypes = [...new Set(enrichedData.map(alphabet => alphabet.script))];
    return scriptTypes.sort();
  }

  /**
   * Get statistics about the data
   */
  async getStatistics() {
    const enrichedData = await this.getEnrichedAlphabetData();
    
    return {
      totalAlphabets: enrichedData.length,
      withTTS: enrichedData.filter(a => a.hasTTS).length,
      withFrequency: enrichedData.filter(a => a.hasFrequency).length,
      withKeyboard: enrichedData.filter(a => a.hasKeyboard).length,
      scriptTypes: [...new Set(enrichedData.map(a => a.script))].length
    };
  }
}

// Export singleton instance
export default new AlphabetDataService();
