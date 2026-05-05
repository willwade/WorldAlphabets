<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import alphabetDataService from '../services/alphabetDataService';

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const error = ref(null);
const localeIndex = ref(null);
const selectedLocale = ref(null);
const wordsData = ref(null);
const searchQuery = ref('');
const expandedWord = ref(null);
const posFilter = ref('');
const sortBy = ref('word');
const sortDir = ref('asc');

const localeList = computed(() => {
  if (!localeIndex.value) return [];
  const locales = localeIndex.value.locales;
  return Object.entries(locales)
    .map(([code, info]) => ({
      code,
      wordCount: info.word_count,
      ruleCount: info.rule_count,
      testCount: info.test_count,
      baseLocale: info.base_locale
    }))
    .sort((a, b) => a.code.localeCompare(b.code));
});

const selectedLocaleInfo = computed(() => {
  if (!selectedLocale.value || !localeIndex.value) return null;
  return localeIndex.value.locales[selectedLocale.value] || null;
});

const availablePosTypes = computed(() => {
  if (!wordsData.value) return [];
  const types = new Set();
  Object.values(wordsData.value).forEach((entry) => {
    if (entry.types) {
      entry.types.forEach((t) => types.add(t));
    }
  });
  return [...types].sort();
});

const wordEntries = computed(() => {
  if (!wordsData.value) return [];
  const metadataKeys = ['_type', '_locale', '_version'];
  let entries = Object.entries(wordsData.value)
    .filter(([key]) => !metadataKeys.includes(key))
    .map(([word, data]) => ({ word, ...data }));

  if (posFilter.value) {
    entries = entries.filter((e) =>
      e.types && e.types.includes(posFilter.value)
    );
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    entries = entries.filter((e) =>
      e.word.toLowerCase().includes(q) ||
      (e.base && e.base.toLowerCase().includes(q))
    );
  }

  entries.sort((a, b) => {
    let cmp;
    if (sortBy.value === 'word') {
      cmp = a.word.localeCompare(b.word);
    } else if (sortBy.value === 'types') {
      const at = (a.types || []).join(',');
      const bt = (b.types || []).join(',');
      cmp = at.localeCompare(bt);
    } else {
      cmp = 0;
    }
    return sortDir.value === 'desc' ? -cmp : cmp;
  });

  return entries;
});

const filteredCount = computed(() => wordEntries.value.length);
const totalCount = computed(() => {
  if (!wordsData.value) return 0;
  const metadataKeys = ['_type', '_locale', '_version'];
  return Object.keys(wordsData.value).filter(
    (k) => !metadataKeys.includes(k)
  ).length;
});

const localeCoverage = computed(() => {
  if (!wordsData.value) return { withForms: 0, total: 0, pct: 0 };
  const metadataKeys = ['_type', '_locale', '_version'];
  let withForms = 0;
  let total = 0;
  Object.entries(wordsData.value).forEach(([k, entry]) => {
    if (metadataKeys.includes(k)) return;
    total++;
    const infl = entry.inflections;
    if (infl) {
      const formKeys = Object.keys(infl).filter(
        (ik) => ik !== 'regulars' && typeof infl[ik] === 'string'
      );
      if (formKeys.length > 0) withForms++;
    }
  });
  return { withForms, total, pct: total > 0 ? Math.round((withForms / total) * 100) : 0 };
});

const inflectionKeys = computed(() => {
  if (!wordsData.value) return [];
  const keys = new Set();
  Object.values(wordsData.value).forEach((entry) => {
    if (entry.inflections) {
      Object.keys(entry.inflections).forEach((k) => {
        if (k !== 'regulars') keys.add(k);
      });
    }
  });
  return [...keys].sort();
});

function toggleSort(field) {
  if (sortBy.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortBy.value = field;
    sortDir.value = 'asc';
  }
}

function selectLocale(code) {
  router.push({ path: `/inflections/${code}` });
}

function toggleWord(word) {
  expandedWord.value =
    expandedWord.value === word ? null : word;
}

function getInflectionEntries(inflections) {
  if (!inflections) return [];
  return Object.entries(inflections).filter(
    ([key]) => key !== 'regulars'
  );
}

function formatInflectionValue(val) {
  if (Array.isArray(val)) return val.join(', ');
  return String(val);
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const idx = await alphabetDataService.loadInflectionIndex();
    localeIndex.value = idx;

    const locale = route.params.locale || null;
    if (locale && idx.locales[locale]) {
      selectedLocale.value = locale;
      const words = await alphabetDataService.loadInflectionWords(
        locale
      );
      wordsData.value = words;
    } else {
      selectedLocale.value = null;
      wordsData.value = null;
    }
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.locale, loadData);
onMounted(loadData);
</script>

<template>
  <div class="inflection-view">
    <nav class="navigation">
      <div class="nav-container">
        <router-link to="/" class="nav-brand">
          <img
            src="/logo.png"
            alt="World Alphabets"
            class="nav-logo"
          />
          <span class="nav-brand-text">World Alphabets</span>
        </router-link>
        <div class="nav-links">
          <router-link
            to="/"
            class="nav-link"
            :class="{ active: $route.name === 'index' }"
          >
            Browse All
          </router-link>
          <router-link
            to="/explore"
            class="nav-link"
            :class="{
              active:
                $route.name === 'explore' ||
                $route.name === 'language'
            }"
          >
            Language Explorer
          </router-link>
          <router-link
            to="/detect-language"
            class="nav-link"
            :class="{
              active: $route.name === 'detect-language'
            }"
          >
            Language Detection
          </router-link>
          <router-link
            to="/inflections"
            class="nav-link"
            :class="{
              active:
                $route.name === 'inflections' ||
                $route.name === 'inflection-locale'
            }"
          >
            Inflections
          </router-link>
        </div>
      </div>
    </nav>

    <main class="app-container">
      <aside class="sidebar">
        <div class="sidebar-header">
          <h3>Locales</h3>
          <span class="locale-count">
            {{ localeList.length }}
          </span>
        </div>
        <div class="sidebar-filter">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filter words..."
            class="filter-input"
            v-if="selectedLocale"
          />
        </div>
        <ul class="locale-list" v-if="!selectedLocale">
          <li
            v-for="loc in localeList"
            :key="loc.code"
            class="locale-item"
            :class="{ active: selectedLocale === loc.code }"
            @click="selectLocale(loc.code)"
          >
            <span class="locale-code">{{ loc.code }}</span>
            <span class="locale-meta">
              {{ loc.wordCount }} words
              <span v-if="loc.baseLocale" class="base-badge">
                from {{ loc.baseLocale }}
              </span>
            </span>
          </li>
        </ul>
        <div class="sidebar-back" v-else>
          <button
            class="back-btn"
            @click="router.push({ path: '/inflections' })"
          >
            &larr; All locales
          </button>
          <div class="current-locale">
            <strong>{{ selectedLocale }}</strong>
            <div
              v-if="selectedLocaleInfo?.base_locale"
              class="base-info"
            >
              Base: {{ selectedLocaleInfo.base_locale }}
            </div>
          </div>
        </div>
      </aside>

      <section class="main-content">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading inflection data...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p class="error-text">Error: {{ error }}</p>
          <button
            class="retry-btn"
            @click="loadData"
          >
            Retry
          </button>
        </div>

        <div v-else-if="!selectedLocale" class="welcome-state">
          <h2>Inflection Browser</h2>
          <p>
            Select a locale from the sidebar to browse its
            inflection data.
          </p>
          <div class="stats-grid" v-if="localeList.length">
            <div class="stat-card">
              <div class="stat-number">
                {{ localeList.length }}
              </div>
              <div class="stat-label">Locales</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">
                {{
                  localeList.reduce(
                    (s, l) => s + l.wordCount,
                    0
                  )
                }}
              </div>
              <div class="stat-label">Total Words</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">
                {{
                  localeList.filter(
                    (l) => l.ruleCount > 0
                  ).length
                }}
              </div>
              <div class="stat-label">With Rules</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">
                {{
                  localeList.filter(
                    (l) => l.testCount > 0
                  ).length
                }}
              </div>
              <div class="stat-label">With Tests</div>
            </div>
          </div>
        </div>

        <div v-else class="locale-content">
          <div class="locale-header">
            <h2>
              {{ selectedLocale }} Inflections
            </h2>
            <div class="locale-summary">
              <span class="summary-badge">
                {{ selectedLocaleInfo?.word_count ?? 0 }} words
              </span>
              <span class="summary-badge">
                {{
                  selectedLocaleInfo?.rule_count ?? 0
                }} rules
              </span>
              <span class="summary-badge">
                {{ selectedLocaleInfo?.test_count ?? 0 }} tests
              </span>
              <span class="summary-badge">
                {{ availablePosTypes.length }} POS types
              </span>
              <span
                class="summary-badge"
                :class="{ 'low-coverage': localeCoverage.pct < 50 }"
                v-if="localeCoverage.total > 0"
              >
                {{ localeCoverage.pct }}% coverage
                ({{ localeCoverage.withForms }}/{{ localeCoverage.total }}
                words with forms)
              </span>
            </div>
            <div
              class="pos-types"
              v-if="availablePosTypes.length"
            >
              <button
                class="pos-chip"
                :class="{ active: posFilter === '' }"
                @click="posFilter = ''"
              >
                All
              </button>
              <button
                v-for="pos in availablePosTypes"
                :key="pos"
                class="pos-chip"
                :class="{ active: posFilter === pos }"
                @click="posFilter = pos"
              >
                {{ pos }}
              </button>
            </div>
          </div>

          <div class="results-info">
            Showing {{ filteredCount }} of {{ totalCount }}
            words
            <span v-if="posFilter">
              (filtered by: {{ posFilter }})
            </span>
          </div>

          <div class="words-table">
            <div class="table-header">
              <button
                class="th-cell sortable"
                @click="toggleSort('word')"
              >
                Word
                <span
                  v-if="sortBy === 'word'"
                  class="sort-arrow"
                >
                  {{ sortDir === 'asc' ? '&#9650;' : '&#9660;' }}
                </span>
              </button>
              <button
                class="th-cell sortable"
                @click="toggleSort('types')"
              >
                POS
                <span
                  v-if="sortBy === 'types'"
                  class="sort-arrow"
                >
                  {{ sortDir === 'asc' ? '&#9650;' : '&#9660;' }}
                </span>
              </button>
              <span class="th-cell">Base</span>
              <span class="th-cell">Forms</span>
            </div>
            <div class="table-body">
              <div
                v-for="entry in wordEntries"
                :key="entry.word"
                class="word-row"
                :class="{
                  expanded:
                    expandedWord === entry.word,
                  'no-forms':
                    getInflectionEntries(entry.inflections).length === 0
                }"
              >
                <div
                  class="word-row-header"
                  @click="
                    getInflectionEntries(entry.inflections).length > 0
                      ? toggleWord(entry.word)
                      : null
                  "
                >
                  <span class="word-text">
                    {{ entry.word }}
                  </span>
                  <span class="word-types">
                    <span
                      v-for="t in entry.types"
                      :key="t"
                      class="type-badge"
                    >
                      {{ t }}
                    </span>
                  </span>
                  <span class="word-base">
                    {{ entry.base || entry.word }}
                  </span>
                  <span class="word-forms-count">
                    {{
                      getInflectionEntries(
                        entry.inflections
                      ).length
                    }}
                    <span
                      v-if="
                        getInflectionEntries(entry.inflections)
                          .length > 0
                      "
                      class="expand-icon"
                    >
                      {{
                        expandedWord === entry.word
                          ? '&#9660;'
                          : '&#9654;'
                      }}
                    </span>
                  </span>
                </div>
                <div
                  v-if="expandedWord === entry.word"
                  class="word-detail"
                >
                  <div
                    v-if="
                      getInflectionEntries(entry.inflections)
                        .length === 0
                    "
                    class="no-forms-message"
                  >
                    No inflected forms available
                    for this word
                  </div>
                  <div
                    v-else
                    class="inflection-grid"
                  >
                    <div
                      v-for="[
                        key,
                        val
                      ] in getInflectionEntries(
                        entry.inflections
                      )"
                      :key="key"
                      class="inflection-item"
                    >
                      <span class="inflection-key">
                        {{ key }}
                      </span>
                      <span class="inflection-val">
                        {{ formatInflectionValue(val) }}
                      </span>
                    </div>
                  </div>
                  <div
                    v-if="entry._sources"
                    class="word-sources"
                  >
                    Sources:
                    {{ entry._sources.join(', ') }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="wordEntries.length === 0 && !loading"
            class="empty-state"
          >
            <p>
              No words found matching your filters.
            </p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.inflection-view {
  min-height: 100vh;
  background: #f8f9fa;
}

.navigation {
  background: white;
  border-bottom: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #007bff;
  text-decoration: none;
}

.nav-brand:hover {
  color: #0056b3;
}

.nav-logo {
  height: 40px;
  width: auto;
}

.nav-brand-text {
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: #6c757d;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #007bff;
  background: #f8f9fa;
}

.nav-link.active {
  color: #007bff;
  background: #e3f2fd;
}

.app-container {
  display: grid;
  grid-template-columns: 280px 1fr;
  height: calc(100vh - 60px);
}

.sidebar {
  background: white;
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.locale-count {
  background: #e3f2fd;
  color: #007bff;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.sidebar-filter {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #e9ecef;
}

.filter-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.85rem;
}

.filter-input:focus {
  border-color: #007bff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
}

.locale-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.locale-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #f1f3f5;
  transition: background 0.15s;
}

.locale-item:hover {
  background: #f8f9fa;
}

.locale-item.active {
  background: #e3f2fd;
  border-left: 3px solid #007bff;
}

.locale-code {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.locale-meta {
  font-size: 0.75rem;
  color: #6c757d;
  text-align: right;
}

.base-badge {
  display: block;
  font-size: 0.65rem;
  color: #007bff;
}

.sidebar-back {
  padding: 1rem;
}

.back-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0.25rem 0;
  margin-bottom: 0.5rem;
}

.back-btn:hover {
  text-decoration: underline;
}

.current-locale {
  padding: 0.5rem;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.base-info {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.main-content {
  overflow-y: auto;
  padding: 1.5rem;
}

.loading-state,
.error-state,
.welcome-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
  color: #6c757d;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e9ecef;
  border-top-color: #007bff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-text {
  color: #dc3545;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.retry-btn:hover {
  background: #0056b3;
}

.welcome-state h2 {
  color: #333;
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-top: 2rem;
  max-width: 600px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #007bff;
}

.stat-label {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.locale-content {
  max-width: 100%;
}

.locale-header {
  margin-bottom: 1rem;
}

.locale-header h2 {
  margin: 0 0 0.5rem;
  color: #333;
  font-size: 1.25rem;
}

.locale-summary {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.summary-badge {
  background: #e9ecef;
  color: #495057;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.pos-types {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.pos-chip {
  background: white;
  border: 1px solid #dee2e6;
  padding: 0.2rem 0.6rem;
  border-radius: 14px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
  color: #495057;
}

.pos-chip:hover {
  border-color: #007bff;
  color: #007bff;
}

.pos-chip.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.results-info {
  font-size: 0.8rem;
  color: #6c757d;
  margin-bottom: 0.75rem;
}

.words-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 0.8fr;
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  padding: 0;
}

.th-cell {
  padding: 0.65rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.th-cell.sortable {
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.th-cell.sortable:hover {
  color: #007bff;
}

.sort-arrow {
  font-size: 0.65rem;
}

.table-body {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.word-row {
  border-bottom: 1px solid #f1f3f5;
}

.word-row.expanded {
  background: #f8f9ff;
}

.word-row-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 0.8fr;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background 0.15s;
  align-items: center;
}

.word-row-header:hover {
  background: #f8f9fa;
}

.word-text {
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
}

.word-types {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.type-badge {
  background: #e3f2fd;
  color: #007bff;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
}

.word-base {
  font-size: 0.85rem;
  color: #6c757d;
}

.word-forms-count {
  font-size: 0.8rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.no-forms .word-forms-count {
  color: #adb5bd;
}

.no-forms .word-row-header {
  cursor: default;
  opacity: 0.7;
}

.low-coverage {
  background: #fff3cd;
  color: #856404;
}

.no-forms-message {
  padding: 0.75rem;
  text-align: center;
  color: #adb5bd;
  font-style: italic;
  font-size: 0.85rem;
}

.expand-icon {
  font-size: 0.65rem;
  color: #adb5bd;
}

.word-detail {
  padding: 0.75rem 1rem 1rem;
  border-top: 1px solid #e9ecef;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.inflection-grid {
  display: grid;
  grid-template-columns: repeat(
    auto-fill,
    minmax(220px, 1fr)
  );
  gap: 0.5rem;
}

.inflection-item {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 0.4rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.inflection-key {
  font-size: 0.7rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.inflection-val {
  font-size: 0.85rem;
  color: #333;
  font-weight: 500;
}

.word-sources {
  margin-top: 0.5rem;
  font-size: 0.7rem;
  color: #adb5bd;
}

.empty-state {
  padding: 2rem;
}

@media (max-width: 768px) {
  .nav-container {
    padding: 0 0.5rem;
    height: 50px;
  }

  .nav-logo {
    height: 32px;
  }

  .nav-brand-text {
    font-size: 1.2rem;
  }

  .nav-links {
    gap: 0.5rem;
  }

  .nav-link {
    padding: 0.25rem 0.4rem;
    font-size: 0.8rem;
  }

  .app-container {
    height: calc(100vh - 50px);
    grid-template-columns: 220px 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .nav-brand-text {
    display: none;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 50px);
  }

  .sidebar {
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid #dee2e6;
  }

  .table-header,
  .word-row-header {
    grid-template-columns: 1.5fr 1fr 1fr 0.6fr;
  }
}
</style>
