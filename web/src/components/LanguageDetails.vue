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
const keyboardCount = ref(0);
const translation = ref(null);
const audioOptions = ref([]);
const audioUrl = ref(null);
const activeTab = ref('alphabet');
const error = ref(null);
const isLoading = ref(false);
const baseUrl = import.meta.env.BASE_URL;

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
  keyboardCount.value = 0;
  translation.value = null;
  audioOptions.value = [];
  audioUrl.value = null;
  activeTab.value = 'alphabet';

  try {
    // Fetch all data in parallel
    const [indexRes, alphabetRes, audioIndexRes, layoutIndexRes] = await Promise.all([
      fetch(`${baseUrl}data/index.json`),
      fetch(`${baseUrl}data/alphabets/${newLangCode}.json`),
      fetch(`${baseUrl}data/audio/index.json`),
      fetch(`${baseUrl}data/layouts/index.json`),
    ]);

    // Process language info
    if (!indexRes.ok) {
      throw new Error('Failed to load language index');
    }
    const indexData = await indexRes.json();
    const langInfo = indexData.find(l => l.language === newLangCode);
    if (langInfo) {
      languageInfo.value = {
        name: langInfo['language-name'],
        direction: langInfo.direction === 'rtl' ? 'Right to Left' : 'Left to Right'
      };
    }

    // Keyboard layouts
    if (layoutIndexRes.ok) {
      try {
        const layoutIndex = await layoutIndexRes.json();
        const layouts = layoutIndex[newLangCode];
        if (Array.isArray(layouts) && layouts.length) {
          keyboardCount.value = layouts.length;
          const layoutId = layouts[0];
          try {
            const keyboardRes = await fetch(`${baseUrl}data/layouts/${layoutId}.json`);
            keyboardData.value = await keyboardRes.json();
          } catch {
            console.warn(`No keyboard layout for ${layoutId}`);
          }
        }
      } catch {
        console.warn('Invalid layout index');
      }
    }

    // Process alphabet and translation
    if (alphabetRes.ok) {
      try {
        const fetchedAlphabetData = await alphabetRes.json();
        alphabetData.value = fetchedAlphabetData;
        if (fetchedAlphabetData.hello_how_are_you) {
          translation.value = fetchedAlphabetData.hello_how_are_you;
        }
      } catch {
        console.warn(`Invalid alphabet data for ${newLangCode}`);
      }
    } else {
      console.warn(`No alphabet data for ${newLangCode}`);
    }

    // Process available audio options
    if (audioIndexRes.ok) {
      try {
        const audioIndexData = await audioIndexRes.json();
        const options = audioIndexData[newLangCode];
        if (Array.isArray(options) && options.length) {
          audioOptions.value = options.map(opt => ({
            ...opt,
            path: `${baseUrl}${opt.path}`
          }));
          audioUrl.value = audioOptions.value[0].path;
        }
      } catch {
        console.warn('Invalid audio index data');
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

      <div class="tabs">
        <button
          :class="{ active: activeTab === 'alphabet' }"
          @click="activeTab = 'alphabet'"
        >Alphabet</button>
        <button
          v-if="keyboardCount"
          :class="{ active: activeTab === 'keyboard' }"
          @click="activeTab = 'keyboard'"
        >Keyboard ({{ keyboardCount }})</button>
      </div>

      <div v-if="activeTab === 'alphabet'" class="tab-content">
        <AlphabetView v-if="alphabetData" :alphabet-data="alphabetData" />

        <div v-if="translation" class="feature-section">
          <h3>Example Phrase</h3>
          <p class="example-phrase">"{{ translation }}"</p>
          <div v-if="audioOptions.length" class="audio-player">
            <label>
              Voice:
              <select v-model="audioUrl">
                <option
                  v-for="(opt, idx) in audioOptions"
                  :key="idx"
                  :value="opt.path"
                >{{ opt.engine }} - {{ opt.voice_id }}</option>
              </select>
            </label>
            <button @click="playAudio">▶️ Play</button>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'keyboard'" class="tab-content">
        <KeyboardView
          :layout-data="keyboardData"
          :total="keyboardCount"
        />
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
.tabs {
  margin-top: 1.5em;
}
.tabs button {
  margin-right: 0.5em;
}
.tabs .active {
  font-weight: bold;
}
.audio-player {
  margin-top: 0.5em;
}
.tab-content {
  margin-top: 1em;
}
</style>
