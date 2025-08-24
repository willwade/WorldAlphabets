<script setup>
import { ref } from 'vue';
import LanguageList from './components/LanguageList.vue';
import LanguageDetails from './components/LanguageDetails.vue';

const selectedLangCode = ref(null);

function handleLanguageSelected(langCode) {
  selectedLangCode.value = langCode;
}
</script>

<template>
  <main class="app-container">
    <LanguageList @language-selected="handleLanguageSelected" />
    <LanguageDetails :selected-lang-code="selectedLangCode" />
  </main>
</template>

<style scoped>
.app-container {
  display: grid;
  grid-template-columns: 300px 1fr;
  height: 100vh;
}
</style>
