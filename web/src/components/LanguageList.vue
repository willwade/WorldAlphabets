<script setup>
import { ref, onMounted, computed } from 'vue';

const languages = ref([]);
const searchTerm = ref('');
const isCollapsed = ref(false);
const emit = defineEmits(['language-selected']);
const baseUrl = import.meta.env.BASE_URL;

onMounted(async () => {
  try {
    console.log('Loading languages from:', `${baseUrl}data/index.json`);
    const response = await fetch(`${baseUrl}data/index.json`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    console.log('Loaded languages:', data.length);

    // Group by language code to avoid duplicates
    const languageMap = new Map();
    data.forEach(lang => {
      if (!languageMap.has(lang.language)) {
        languageMap.set(lang.language, {
          language: lang.language,
          name: lang.name,
          scripts: [lang.script],
          entries: [lang]
        });
      } else {
        const existing = languageMap.get(lang.language);
        existing.scripts.push(lang.script);
        existing.entries.push(lang);
      }
    });

    // Convert to array and sort
    languages.value = Array.from(languageMap.values()).sort((a, b) =>
      a.name.localeCompare(
        b.name,
        undefined,
        { sensitivity: 'base' },
      ),
    );
    console.log('Languages grouped and sorted:', languages.value.length);
  } catch (error) {
    console.error('Failed to fetch languages:', error);
  }
});

const filteredLanguages = computed(() => {
  if (!searchTerm.value) {
    return languages.value;
  }
  return languages.value.filter(lang =>
    lang.name.toLowerCase().includes(searchTerm.value.toLowerCase())
  );
});

function selectLanguage(langCode) {
  emit('language-selected', langCode);
  // Auto-collapse on mobile after selection
  if (window.innerWidth <= 480) {
    isCollapsed.value = true;
  }
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}
</script>

<template>
  <div class="language-list-container" :class="{ collapsed: isCollapsed }">
    <!-- Mobile collapse toggle -->
    <div class="mobile-header">
      <button @click="toggleCollapse" class="collapse-toggle">
        <span class="toggle-text">{{ isCollapsed ? 'Show Languages' : 'Hide Languages' }}</span>
        <span class="toggle-icon">{{ isCollapsed ? '▼' : '▲' }}</span>
      </button>
    </div>

    <!-- Collapsible content -->
    <div class="collapsible-content" :class="{ hidden: isCollapsed }">
      <input type="search" v-model="searchTerm" placeholder="Search for a language..." class="search-box">
      <ul class="language-list">
        <li
          v-for="lang in filteredLanguages"
          :key="lang.language"
          @click="selectLanguage(lang.language)"
          class="language-item"
        >
          {{ lang.name }}
          <span v-if="lang.scripts.length > 1" class="script-count">
            ({{ lang.scripts.length }} scripts)
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.language-list-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  border-right: 1px solid #ccc;
  background: white;
}

/* Mobile header - hidden by default */
.mobile-header {
  display: none;
}

.collapse-toggle {
  width: 100%;
  padding: 0.75rem;
  background: #f8f9fa;
  border: none;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
}

.collapse-toggle:hover {
  background: #e9ecef;
}

.toggle-icon {
  font-size: 0.8rem;
  color: #6c757d;
}

.collapsible-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.collapsible-content.hidden {
  display: none;
}

.search-box {
  padding: 0.5em;
  margin: 0.5em;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.language-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
}

.language-item {
  padding: 0.75em;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.language-item:hover {
  background-color: #f0f0f0;
}

.language-item:last-child {
  border-bottom: none;
}

.script-count {
  font-size: 0.8em;
  color: #666;
  font-weight: normal;
}

/* Mobile styles */
@media (max-width: 480px) {
  .language-list-container {
    height: auto;
    min-height: auto;
  }

  .language-list-container.collapsed {
    height: auto;
  }

  .mobile-header {
    display: block;
  }

  .collapsible-content {
    max-height: 40vh;
    overflow-y: auto;
  }

  .collapsible-content.hidden {
    display: none;
  }

  .language-item {
    padding: 1rem 0.75rem;
    font-size: 1rem;
  }
}

/* Tablet styles */
@media (max-width: 768px) and (min-width: 481px) {
  .language-list-container {
    height: 100vh;
  }

  .mobile-header {
    display: none;
  }
}
</style>
