<script setup>
import { ref, watch, computed } from 'vue';
import AlphabetView from './AlphabetView.vue';
import KeyboardView from './KeyboardView.vue';

const props = defineProps({
  selectedLangCode: String
});

const languageInfo = ref(null);
const alphabetData = ref(null);
const keyboardLayouts = ref([]);
const selectedLayoutId = ref(null);
const keyboardData = ref(null);
const keyboardCount = ref(0);
const translation = ref(null);
const audioOptions = ref([]);
const audioUrl = ref(null);
const activeTab = ref('alphabet');
const error = ref(null);
const isLoading = ref(false);
const baseUrl = import.meta.env.BASE_URL;
const availableScripts = ref([]);
const selectedScript = ref(null);
const scriptNames = {
  Latn: 'Latin',
  Deva: 'Devanagari'
};

async function loadAlphabet(langCode, script) {
  const alphabetPath = script
    ? `${baseUrl}data/alphabets/${langCode}-${script}.json`
    : `${baseUrl}data/alphabets/${langCode}.json`;
  const alphabetRes = await fetch(alphabetPath);
  alphabetData.value = null;
  translation.value = null;
  if (alphabetRes.ok) {
    try {
      const fetchedAlphabetData = await alphabetRes.json();
      alphabetData.value = fetchedAlphabetData;
      if (fetchedAlphabetData.hello_how_are_you) {
        translation.value = fetchedAlphabetData.hello_how_are_you;
      }
    } catch {
      console.warn(`Invalid alphabet data for ${langCode}`);
    }
  } else {
    console.warn(`No alphabet data for ${langCode}`);
  }
}

watch(() => props.selectedLangCode, async (newLangCode) => {
  if (!newLangCode) {
    languageInfo.value = null;
    return;
  }

  isLoading.value = true;
  error.value = null;
  languageInfo.value = null;
  alphabetData.value = null;
  keyboardLayouts.value = [];
  selectedLayoutId.value = null;
  keyboardData.value = null;
  keyboardCount.value = 0;
  translation.value = null;
  audioOptions.value = [];
  audioUrl.value = null;
  activeTab.value = 'alphabet';
  availableScripts.value = [];
  selectedScript.value = null;

  try {
    // Fetch indexes in parallel
    const [indexRes, audioIndexRes, layoutIndexRes] = await Promise.all([
      fetch(`${baseUrl}data/index.json`),
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
        direction: langInfo.direction === 'rtl'
          ? 'Right to Left'
          : 'Left to Right'
      };
      if (Array.isArray(langInfo.scripts) && langInfo.scripts.length) {
        availableScripts.value = langInfo.scripts;
        selectedScript.value = langInfo.scripts[0];
      } else {
        await loadAlphabet(newLangCode, null);
      }
    } else {
      await loadAlphabet(newLangCode, null);
    }

    // Keyboard layouts
    if (layoutIndexRes.ok) {
      try {
        const layoutIndex = await layoutIndexRes.json();
        const layouts = layoutIndex[newLangCode];
        if (Array.isArray(layouts) && layouts.length) {
          keyboardCount.value = layouts.length;
          const fetched = await Promise.all(
            layouts.map(async id => {
              try {
                const res = await fetch(`${baseUrl}data/layouts/${id}.json`);
                if (!res.ok) throw new Error();
                const data = await res.json();
                const valid = Array.isArray(data.keys) && data.keys.some(k => k.pos);
                return { id, name: data.name || id, data: valid ? data : null };
              } catch {
                console.warn(`No keyboard layout for ${id}`);
                return { id, name: id, data: null };
              }
            })
          );
          keyboardLayouts.value = fetched;
          const firstValid = keyboardLayouts.value.find(l => l.data);
          if (firstValid) {
            selectedLayoutId.value = firstValid.id;
            keyboardData.value = firstValid.data;
          } else if (keyboardLayouts.value.length) {
            selectedLayoutId.value = keyboardLayouts.value[0].id;
          }
        }
      } catch {
        console.warn('Invalid layout index');
      }
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

watch(selectedScript, async script => {
  if (props.selectedLangCode) {
    await loadAlphabet(props.selectedLangCode, script);
  }
});

function playAudio() {
    if (audioUrl.value) {
        new Audio(audioUrl.value).play();
    }
}

watch(selectedLayoutId, id => {
  const layout = keyboardLayouts.value.find(l => l.id === id);
  keyboardData.value = layout ? layout.data : null;
});

const currentLayoutName = computed(() => {
  const layout = keyboardLayouts.value.find(l => l.id === selectedLayoutId.value);
  return layout ? layout.name : '';
});

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
      <div v-if="availableScripts.length > 1" class="script-selector">
        <label>
          Script:
          <select v-model="selectedScript">
            <option
              v-for="script in availableScripts"
              :key="script"
              :value="script"
            >{{ scriptNames[script] || script }}</option>
          </select>
        </label>
      </div>
      <p v-else-if="selectedScript">
        <strong>Script:</strong>
        {{ scriptNames[selectedScript] || selectedScript }}
      </p>

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
        <div v-if="keyboardLayouts.length">
          <label>
            Layout:
            <select v-model="selectedLayoutId">
              <option
                v-for="layout in keyboardLayouts"
                :key="layout.id"
                :value="layout.id"
              >{{ layout.name }}</option>
            </select>
          </label>
          <KeyboardView
            :layout-data="keyboardData"
            :layout-name="currentLayoutName"
            :total="keyboardCount"
          />
        </div>
        <div v-else>
          <p>No keyboard layout available for this language.</p>
        </div>
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
.script-selector {
  margin-top: 0.5em;
}
.tab-content {
  margin-top: 1em;
}
</style>
