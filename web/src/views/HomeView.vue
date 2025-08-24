<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LanguageList from '../components/LanguageList.vue';
import LanguageDetails from '../components/LanguageDetails.vue';

const route = useRoute();
const router = useRouter();
const selectedLangCode = ref(route.params.langCode || null);

watch(() => route.params.langCode, (newCode) => {
  selectedLangCode.value = newCode || null;
});

function handleLanguageSelected(langCode) {
  router.push({ path: `/${langCode}` });
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
