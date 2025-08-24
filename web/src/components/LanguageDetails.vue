<script setup>
import { ref, watch } from 'vue';
import AlphabetView from './AlphabetView.vue';
import KeyboardView from './KeyboardView.vue';

const props = defineProps({
  selectedLangCode: String
});

const languageInfo = ref(null);
const alphabetData = ref(null);
const keyboardData = ref(null);
const translation = ref(null);
const audioUrl = ref(null);
const error = ref(null);
const isLoading = ref(false);

watch(() => props.selectedLangCode, async (newLangCode) => {
  if (!newLangCode) {
    languageInfo.value = null;
    return;
  }

  isLoading.value = true;
  error.value = null;
  languageInfo.value = null;
  alphabetData.value = null;
  keyboardData.value = null;
  translation.value = null;
  audioUrl.value = null;

  try {
    // Fetch all data in parallel
    const [indexRes, alphabetRes, mappingRes] = await Promise.all([
      fetch('data/index.json'),
      fetch(`data/alphabets/${newLangCode}.json`),
      fetch('data/mappings/language_to_driver.json'),
    ]);

    // Process language info
    const indexData = await indexRes.json();
    const langInfo = indexData.find(l => l.language === newLangCode);
    if (langInfo) {
      languageInfo.value = {
        name: langInfo['language-name'],
        direction: langInfo.direction === 'rtl' ? 'Right to Left' : 'Left to Right'
      };
    }

    // Process alphabet and translation
    if (alphabetRes.ok) {
      const fetchedAlphabetData = await alphabetRes.json();
      alphabetData.value = fetchedAlphabetData;
      if (fetchedAlphabetData.hello_how_are_you) {
        translation.value = fetchedAlphabetData.hello_how_are_you;
      }
    } else {
      console.warn(`No alphabet data for ${newLangCode}`);
    }

    // Check for audio
    const audioCheck = await fetch(`audio/${newLangCode}.wav`);
    if (audioCheck.ok) {
        audioUrl.value = `audio/${newLangCode}.wav`;
    }

    // Process keyboard layout
    const mappingData = await mappingRes.json();
    const layoutName = mappingData[newLangCode];
    if (layoutName) {
      const keyboardRes = await fetch(`data/layouts/${layoutName}.json`);
      if (keyboardRes.ok) {
        keyboardData.value = await keyboardRes.json();
      }
    }
  } catch (e) {
    error.value = "Failed to load language data.";
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}, { immediate: true });

function playAudio() {
    if (audioUrl.value) {
        new Audio(audioUrl.value).play();
    }
}

</script>

<template>
  <div class="details-container">
    <div v-if="isLoading" class="loading-message">
      <p>Loading...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
    <div v-else-if="languageInfo" class="language-details-content">
      <h2>{{ languageInfo.name }}</h2>
      <p><strong>Direction:</strong> {{ languageInfo.direction }}</p>

      <hr>
      <AlphabetView v-if="alphabetData" :alphabet-data="alphabetData" />

      <div v-if="translation" class="feature-section">
        <h3>Example Phrase</h3>
        <p class="example-phrase">"{{ translation }}"</p>
        <button v-if="audioUrl" @click="playAudio">▶️ Play</button>
      </div>

      <div class="feature-section">
        <KeyboardView v-if="keyboardData" :layout-data="keyboardData" />
      </div>

      <div class="feature-section">
        <h3>External Links</h3>
        <ul>
          <li><a :href="`https://iso639-3.sil.org/code/${selectedLangCode}`" target="_blank">ISO 639-3</a></li>
          <li><a :href="`https://www.ethnologue.com/language/${selectedLangCode}`" target="_blank">Ethnologue</a></li>
          <li><a :href="`http://glottolog.org/glottolog?iso=${selectedLangCode}`" target="_blank">Glottolog</a></li>
          <li><a :href="`https://en.wikipedia.org/wiki/ISO_639:${selectedLangCode}`" target="_blank">Wikipedia</a></li>
        </ul>
      </div>

    </div>
    <div v-else class="placeholder-message">
      <p>Select a language to see the details.</p>
    </div>
  </div>
</template>

<style scoped>
.details-container {
  padding: 2em;
  overflow-y: auto;
  height: 100vh;
  box-sizing: border-box;
}
.error-message {
  color: red;
}
hr {
  margin: 1.5em 0;
}
.feature-section {
  margin-top: 2em;
}
.example-phrase {
  font-style: italic;
  margin: 0.5em 0;
}
ul {
  list-style: none;
  padding: 0;
}
li {
  margin-bottom: 0.5em;
}
a {
  color: #42b983;
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
</style>
