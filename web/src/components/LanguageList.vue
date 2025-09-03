<script setup>
import { ref, onMounted, computed } from 'vue';

const languages = ref([]);
const searchTerm = ref('');
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
}
</script>

<template>
  <div class="language-list-container">
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
</template>

<style scoped>
.language-list-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid #ccc;
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
}

.language-item {
  padding: 0.75em;
  cursor: pointer;
}

.language-item:hover {
  background-color: #f0f0f0;
}

.script-count {
  font-size: 0.8em;
  color: #666;
  font-weight: normal;
}
</style>
