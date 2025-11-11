<template>
  <div class="alphabet-index">
    <!-- Header with statistics -->
    <div class="header">
      <h1>World Alphabets Explorer</h1>
      <div v-if="statistics" class="stats">
        <span class="stat">{{ statistics.totalAlphabets }} language-script combinations</span>
        <span class="stat">{{ statistics.totalLanguages }} languages</span>
        <span class="stat">{{ statistics.totalScripts }} scripts</span>
        <span class="stat">{{ statistics.withTTS }} with TTS</span>
        <span class="stat">{{ statistics.withWordFrequency }} with word frequency lists</span>
        <span class="stat">{{ statistics.withKeyboard }} with keyboards</span>
      </div>

    </div>

    <!-- Search and Filters -->
    <div class="search-filters">
      <div class="search-section">
        <input
          v-model="searchTerm"
          type="search"
          placeholder="Search alphabets by name, language, or script..."
          class="search-input"
          @input="debouncedSearch"
        />
        <p class="search-help">
          Search by language name (e.g., "Welsh", "Arabic"), language code (e.g., "cy", "ar"), or script type (e.g., "Latin", "Cyrillic")
        </p>
      </div>

      <!-- Mobile: Collapsible filters -->
      <div class="mobile-filter-toggle">
        <button @click="showMobileFilters = !showMobileFilters" class="mobile-filter-btn">
          <span>Filters</span>
          <span class="filter-count" v-if="hasActiveFilters">({{ activeFilterCount }})</span>
          <span class="toggle-icon">{{ showMobileFilters ? '▲' : '▼' }}</span>
        </button>
      </div>

      <div class="filters-section" :class="{ 'mobile-hidden': !showMobileFilters }">
        <div class="filter-group">
          <label class="filter-label">Show only alphabets with:</label>
          <div class="checkbox-group">
            <label class="checkbox-label">
              <input
                v-model="filters.hasTTS"
                type="checkbox"
                @change="onFilterChange"
              />
              <span class="checkbox-text">Text-to-Speech</span>
            </label>
            <label class="checkbox-label">
              <input
                v-model="filters.hasFrequency"
                type="checkbox"
                @change="onFilterChange"
              />
              <span class="checkbox-text">Character Frequency Data</span>
            </label>
            <label class="checkbox-label">
              <input
                v-model="filters.hasWordFrequency"
                type="checkbox"
                @change="onFilterChange"
              />
              <span class="checkbox-text">Word Frequency List</span>
            </label>
            <label class="checkbox-label">
              <input
                v-model="filters.hasKeyboard"
                type="checkbox"
                @change="onFilterChange"
              />
              <span class="checkbox-text">Keyboard Layout</span>
            </label>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">Script Type:</label>
          <select v-model="filters.scriptType" @change="onFilterChange" class="script-select">
            <option value="">All Scripts</option>
            <option v-for="script in availableScripts" :key="script" :value="script">
              {{ getScriptTypeName(script) }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">Sort by:</label>
          <select v-model="sortBy" @change="onSortChange" class="sort-select">
            <option value="name">Name</option>
            <option value="language">Language Code</option>
            <option value="script">Script</option>
            <option value="letterCount">Letter Count</option>
          </select>
          <button @click="toggleSortOrder" class="sort-order-btn" :title="sortOrder === 'asc' ? 'Sort Descending' : 'Sort Ascending'">
            {{ sortOrder === 'asc' ? '↑' : '↓' }}
          </button>
        </div>

        <button @click="clearFilters" class="clear-filters-btn">Clear Filters</button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      Loading alphabets...
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <!-- Results -->
    <div v-else class="results">
      <div class="results-info">
        <span v-if="searchResults">
          Showing {{ searchResults.pagination.totalItems }} results
          <span v-if="searchTerm || hasActiveFilters">
            (filtered from {{ statistics?.totalAlphabets || 0 }} total)
          </span>
        </span>
      </div>

      <!-- Desktop: Alphabet Table -->
      <div v-if="searchResults?.data.length" class="table-container">
        <table class="alphabet-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Language</th>
              <th>Script</th>
              <th>Features</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="alphabet in searchResults.data"
              :key="`${alphabet.language}-${alphabet.script}`"
              class="alphabet-row"
              @click="selectAlphabet(alphabet)"
            >
              <td class="name-cell">
                <strong>{{ alphabet.name }}</strong>
              </td>
              <td class="language-cell">
                {{ alphabet.language }}
                <span v-if="alphabet.iso639_3" class="iso-code">({{ alphabet.iso639_3 }})</span>
              </td>
              <td class="script-cell">
                {{ getScriptTypeName(alphabet.script) }}
              </td>
              <td class="features-cell">
                <div class="feature-badges">
                  <span v-if="alphabet.hasTTS" class="badge tts-badge" title="Text-to-Speech Available">TTS</span>
                  <span
                    v-if="alphabet.hasFrequency"
                    class="badge freq-badge"
                    title="Character Frequency Data Available"
                  >FREQ</span>
                  <span
                    v-if="alphabet.hasWordFrequency"
                    class="badge word-badge"
                    title="Word Frequency List Available"
                  >WORDS</span>
                  <span v-if="alphabet.hasKeyboard" class="badge kbd-badge" title="Keyboard Layout Available">KBD</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>


      <!-- No results -->
      <div v-else class="no-results">
        <p>No alphabets found matching your criteria.</p>
        <button @click="clearFilters" class="clear-filters-btn">Clear Filters</button>
      </div>

      <!-- Pagination -->
      <div v-if="searchResults?.pagination.totalPages > 1" class="pagination">
        <button
          @click="goToPage(1)"
          :disabled="!searchResults.pagination.hasPreviousPage"
          class="page-btn"
        >
          First
        </button>
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="!searchResults.pagination.hasPreviousPage"
          class="page-btn"
        >
          Previous
        </button>
        
        <span class="page-info">
          Page {{ searchResults.pagination.currentPage }} of {{ searchResults.pagination.totalPages }}
        </span>
        
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="!searchResults.pagination.hasNextPage"
          class="page-btn"
        >
          Next
        </button>
        <button
          @click="goToPage(searchResults.pagination.totalPages)"
          :disabled="!searchResults.pagination.hasNextPage"
          class="page-btn"
        >
          Last
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import alphabetDataService from '../services/alphabetDataService.js';

const router = useRouter();

// Reactive data
const loading = ref(true);
const error = ref(null);
const searchTerm = ref('');
const searchResults = ref(null);
const statistics = ref(null);
const availableScripts = ref([]);
const currentPage = ref(1);
const pageSize = ref(50);
const showMobileFilters = ref(false);

// Computed page size based on screen size
const effectivePageSize = computed(() => {
  // Use smaller page size on mobile for better performance
  return window.innerWidth <= 768 ? 20 : pageSize.value;
});

const filters = reactive({
  hasTTS: false,
  hasFrequency: false,
  hasWordFrequency: false,
  hasKeyboard: false,
  scriptType: ''
});

const sortBy = ref('name');
const sortOrder = ref('asc');

// Computed properties
const hasActiveFilters = computed(() => {
  return filters.hasTTS === true ||
         filters.hasFrequency === true ||
         filters.hasWordFrequency === true ||
         filters.hasKeyboard === true ||
         filters.scriptType !== '';
});

const activeFilterCount = computed(() => {
  let count = 0;
  if (filters.hasTTS) count++;
  if (filters.hasFrequency) count++;
  if (filters.hasWordFrequency) count++;
  if (filters.hasKeyboard) count++;
  if (filters.scriptType) count++;
  return count;
});

// Debounced search
let searchTimeout;
const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1; // Reset to first page on search
    performSearch();
  }, 300);
};

// Methods
const performSearch = async () => {
  try {
    loading.value = true;
    error.value = null;

    const searchOptions = {
      searchTerm: searchTerm.value,
      filters: {
        hasTTS: filters.hasTTS ? true : null,
        hasFrequency: filters.hasFrequency ? true : null,
        hasWordFrequency: filters.hasWordFrequency ? true : null,
        hasKeyboard: filters.hasKeyboard ? true : null,
        scriptType: filters.scriptType
      },
      sortBy: sortBy.value,
      sortOrder: sortOrder.value,
      page: currentPage.value,
      pageSize: effectivePageSize.value
    };

    searchResults.value = await alphabetDataService.searchAlphabets(searchOptions);
  } catch (err) {
    error.value = 'Failed to search alphabets: ' + err.message;
    console.error('Search error:', err);
  } finally {
    loading.value = false;
  }
};

const onFilterChange = () => {
  currentPage.value = 1; // Reset to first page on filter change
  performSearch();
};

const onSortChange = () => {
  performSearch();
};

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  performSearch();
};

const clearFilters = () => {
  searchTerm.value = '';
  filters.hasTTS = false;
  filters.hasFrequency = false;
  filters.hasWordFrequency = false;
  filters.hasKeyboard = false;
  filters.scriptType = '';
  sortBy.value = 'name';
  sortOrder.value = 'asc';
  currentPage.value = 1;
  performSearch();
};

const goToPage = (page) => {
  currentPage.value = page;
  performSearch();
};

const selectAlphabet = (alphabet) => {
  // Navigate to the alphabet detail view
  router.push({ path: `/${alphabet.language}` });
};

const getScriptTypeName = (script) => {
  return alphabetDataService.getScriptTypeName(script);
};

// Initialize
onMounted(async () => {
  try {
    // Load initial data
    const [stats, scripts] = await Promise.all([
      alphabetDataService.getStatistics(),
      alphabetDataService.getAvailableScriptTypes()
    ]);
    
    statistics.value = stats;
    availableScripts.value = scripts;
    
    // Perform initial search
    await performSearch();
  } catch (err) {
    error.value = 'Failed to load alphabet data: ' + err.message;
    console.error('Initialization error:', err);
    loading.value = false;
  }
});
</script>

<style scoped>
.alphabet-index {
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 2.5rem;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.stat {
  background: #f5f5f5;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #666;
}


.search-filters {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-section {
  margin-bottom: 1.5rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.search-help {
  margin: 0.5rem 0 0 0;
  font-size: 0.85rem;
  color: #6c757d;
  line-height: 1.4;
}

.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
}

.checkbox-group {
  display: flex;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-text {
  white-space: nowrap;
}

.script-select, .sort-select {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}

.sort-order-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 1.2rem;
  margin-left: 0.25rem;
}

.sort-order-btn:hover {
  background: #f5f5f5;
}

.clear-filters-btn {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.clear-filters-btn:hover {
  background: #c82333;
}

/* Mobile filter toggle */
.mobile-filter-toggle {
  display: none;
  margin-bottom: 1rem;
}

.mobile-filter-btn {
  width: 100%;
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
  color: #495057;
}

.mobile-filter-btn:hover {
  background: #e9ecef;
}

.filter-count {
  background: #007bff;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.toggle-icon {
  font-size: 0.8rem;
  color: #6c757d;
}

/* Desktop/Mobile visibility */
.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.error {
  color: #dc3545;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

.results-info {
  margin-bottom: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.alphabet-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.alphabet-table th {
  background: #f8f9fa;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  color: #495057;
}

.alphabet-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #dee2e6;
}

.alphabet-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.alphabet-row:hover {
  background-color: #f8f9fa;
}

.name-cell strong {
  color: #007bff;
}

.iso-code {
  color: #6c757d;
  font-size: 0.8rem;
}

.feature-badges {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.badge {
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.tts-badge {
  background: #d4edda;
  color: #155724;
}

.freq-badge {
  background: #d1ecf1;
  color: #0c5460;
}

.word-badge {
  background: #fff3cd;
  color: #856404;
}

.kbd-badge {
  background: #f8d7da;
  color: #721c24;
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #6c757d;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2rem;
}

.page-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  color: #007bff;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.page-btn:disabled {
  color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.page-info {
  margin: 0 1rem;
  color: #6c757d;
  font-size: 0.9rem;
}

/* Mobile Cards Layout */
.cards-container {
  display: grid;
  gap: 1rem;
  margin-bottom: 2rem;
}

.alphabet-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.alphabet-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transform: translateY(-1px);
}

.alphabet-card:active {
  transform: translateY(0);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #007bff;
  line-height: 1.3;
}

.card-badges {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-label {
  font-weight: 500;
  color: #6c757d;
  font-size: 0.9rem;
}

.card-value {
  color: #495057;
  font-size: 0.9rem;
  text-align: right;
}

/* Responsive design */
@media (max-width: 768px) {
  .alphabet-index {
    padding: 0.5rem;
  }

  .header h1 {
    font-size: 2rem;
  }

  .stats {
    gap: 1rem;
  }




  /* Show mobile filter toggle */
  .mobile-filter-toggle {
    display: block;
  }

  /* Hide filters by default on mobile */
  .filters-section.mobile-hidden {
    display: none;
  }

  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    justify-content: space-between;
  }

  .checkbox-group {
    flex-direction: column;
    gap: 0.5rem;
  }

  /* Hide desktop table, show mobile cards */
  .desktop-only {
    display: none;
  }

  .mobile-only {
    display: block;
  }

  .pagination {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .header h1 {
    font-size: 1.5rem;
  }

  .stats {
    flex-direction: column;
    gap: 0.5rem;
  }




  /* Smaller page size for mobile */
  .cards-container {
    gap: 0.75rem;
  }

  .alphabet-card {
    padding: 0.75rem;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .card-title {
    font-size: 1rem;
  }

  .card-badges {
    align-self: flex-end;
  }

  .pagination {
    gap: 0.25rem;
  }

  .page-btn {
    padding: 0.4rem 0.8rem;
    font-size: 0.9rem;
  }

  .page-info {
    margin: 0 0.5rem;
    font-size: 0.8rem;
  }
}
</style>
