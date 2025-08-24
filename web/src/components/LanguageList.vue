<script setup>
import { ref, onMounted, computed } from 'vue';

const languages = ref([]);
const searchTerm = ref('');
const emit = defineEmits(['language-selected']);

onMounted(async () => {
  try {
    const response = await fetch('/data/index.json');
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    languages.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch languages:', error);
  }
});

const filteredLanguages = computed(() => {
  if (!searchTerm.value) {
    return languages.value;
  }
  return languages.value.filter(lang =>
    lang['language-name'].toLowerCase().includes(searchTerm.value.toLowerCase())
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
        {{ lang['language-name'] }}
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
</style>
