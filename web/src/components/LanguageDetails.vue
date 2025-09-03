<script setup>
import { ref, watch, computed, nextTick } from 'vue';
import AlphabetView from './AlphabetView.vue';
import KeyboardView from './KeyboardView.vue';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-javascript';
import 'prismjs/themes/prism.css';

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
const showCodeExamples = ref(false);
const activeCodeTab = ref('python');
const copiedStates = ref({
  python: false,
  nodejs: false
});
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
    const langEntries = indexData.filter(l => l.language === newLangCode);
    if (langEntries.length > 0) {
      const firstEntry = langEntries[0];
      languageInfo.value = {
        name: firstEntry.name,
        direction: firstEntry.direction === 'rtl'
          ? 'Right to Left'
          : 'Left to Right'
      };

      // Collect all scripts for this language
      const scripts = langEntries.map(entry => entry.script);
      availableScripts.value = scripts;
      selectedScript.value = scripts[0];
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
  if (props.selectedLangCode && script) {
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

// Generate code content for copying
const pythonCode = computed(() => {
  return `# Install: pip install worldalphabets
from worldalphabets import load_alphabet, get_available_layouts, load_keyboard

# Load alphabet data
alphabet = load_alphabet("${props.selectedLangCode}"${selectedScript.value ? `, "${selectedScript.value}"` : ''})
print("Alphabetical:", alphabet.alphabetical)
print("Uppercase:", alphabet.uppercase)
print("Lowercase:", alphabet.lowercase)
print("Frequency:", alphabet.frequency)
${alphabetData.value && alphabetData.value.digits ? 'print("Digits:", alphabet.digits)' : '# No digits available'}

# Load keyboard layouts${keyboardLayouts.value.length ? `
layouts = get_available_layouts("${props.selectedLangCode}")
if layouts:
    keyboard = load_keyboard(layouts[0])
    print("Keyboard layout:", keyboard.name)` : `
# No keyboard layouts available for this language`}`;
});

const nodejsCode = computed(() => {
  return `// Install: npm install worldalphabets
const {
  loadAlphabet,
  getUppercase,
  getLowercase,
  getFrequency,${alphabetData.value && alphabetData.value.digits ? `
  getDigits,` : ''}
  getAvailableLayouts,
  loadKeyboard
} = require('worldalphabets');

async function example() {
  // Load alphabet data
  const alphabet = await loadAlphabet("${props.selectedLangCode}"${selectedScript.value ? `, "${selectedScript.value}"` : ''});
  console.log("Alphabetical:", alphabet.alphabetical);
  console.log("Uppercase:", alphabet.uppercase);
  console.log("Lowercase:", alphabet.lowercase);
  console.log("Frequency:", alphabet.frequency);${alphabetData.value && alphabetData.value.digits ? `
  console.log("Digits:", alphabet.digits);` : `
  // No digits available`}

  // Or load individual components
  const uppercase = await getUppercase("${props.selectedLangCode}"${selectedScript.value ? `, "${selectedScript.value}"` : ''});
  const frequency = await getFrequency("${props.selectedLangCode}"${selectedScript.value ? `, "${selectedScript.value}"` : ''});${alphabetData.value && alphabetData.value.digits ? `
  const digits = await getDigits("${props.selectedLangCode}"${selectedScript.value ? `, "${selectedScript.value}"` : ''});` : ''}

  // Load keyboard layouts${keyboardLayouts.value.length ? `
  const layouts = await getAvailableLayouts("${props.selectedLangCode}");
  if (layouts.length > 0) {
    const keyboard = await loadKeyboard(layouts[0].id);
    console.log("Keyboard layout:", keyboard.name);
  }` : `
  // No keyboard layouts available for this language`}
}

example();`;
});

async function copyCode(type) {
  try {
    const code = type === 'python' ? pythonCode.value : nodejsCode.value;
    await navigator.clipboard.writeText(code);
    copiedStates.value[type] = true;
    setTimeout(() => {
      copiedStates.value[type] = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy code:', err);
  }
}

// Highlight code after DOM updates
function highlightCode() {
  nextTick(() => {
    Prism.highlightAll();
  });
}

// Watch for changes that should trigger re-highlighting
watch([activeCodeTab, showCodeExamples, selectedScript, alphabetData, keyboardLayouts], () => {
  if (showCodeExamples.value) {
    highlightCode();
  }
});

watch(showCodeExamples, (newValue) => {
  if (newValue) {
    highlightCode();
  }
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
        <h3>
          <button
            @click="showCodeExamples = !showCodeExamples"
            class="toggle-button"
            :class="{ expanded: showCodeExamples }"
          >
            {{ showCodeExamples ? '▼' : '▶' }} Code Examples
          </button>
        </h3>
        <div v-show="showCodeExamples" class="code-examples">
          <div class="code-tabs">
            <button
              @click="activeCodeTab = 'python'"
              :class="{ active: activeCodeTab === 'python' }"
              class="code-tab"
            >
              Python
            </button>
            <button
              @click="activeCodeTab = 'nodejs'"
              :class="{ active: activeCodeTab === 'nodejs' }"
              class="code-tab"
            >
              Node.js
            </button>
          </div>

          <div v-show="activeCodeTab === 'python'" class="code-content">
            <div class="code-header">
              <span class="code-language">Python</span>
              <button @click="copyCode('python')" class="copy-btn" title="Copy code">
                <span v-if="!copiedStates.python">📋</span>
                <span v-else class="copied">✓</span>
              </button>
            </div>
            <pre><code class="language-python">{{ pythonCode }}</code></pre>
          </div>

          <div v-show="activeCodeTab === 'nodejs'" class="code-content">
            <div class="code-header">
              <span class="code-language">Node.js</span>
              <button @click="copyCode('nodejs')" class="copy-btn" title="Copy code">
                <span v-if="!copiedStates.nodejs">📋</span>
                <span v-else class="copied">✓</span>
              </button>
            </div>
            <pre><code class="language-javascript">{{ nodejsCode }}</code></pre>
          </div>
        </div>
      </div>

      <div class="feature-section">
        <h3>External Links</h3>
        <ul>
          <li><a :href="`https://iso639-3.sil.org/code/${alphabetData?.iso639_3 || selectedLangCode}`" target="_blank">ISO 639-3</a></li>
          <li><a :href="`https://www.ethnologue.com/language/${alphabetData?.iso639_3 || selectedLangCode}`" target="_blank">Ethnologue</a></li>
          <li><a :href="`http://glottolog.org/glottolog?iso=${alphabetData?.iso639_3 || selectedLangCode}`" target="_blank">Glottolog</a></li>
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

.toggle-button {
  background: none;
  border: none;
  font-size: 1.1em;
  font-weight: bold;
  cursor: pointer;
  color: #333;
  padding: 0;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.toggle-button:hover {
  color: #0066cc;
}

.code-examples {
  margin-top: 1em;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.code-tabs {
  display: flex;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ddd;
}

.code-tab {
  flex: 1;
  padding: 0.75em 1em;
  border: none;
  background-color: transparent;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 500;
  color: #6c757d;
  transition: all 0.2s ease;
  border-bottom: 3px solid transparent;
}

.code-tab:hover {
  background-color: #e9ecef;
  color: #495057;
}

.code-tab.active {
  background-color: #fff;
  color: #0066cc;
  border-bottom-color: #0066cc;
  font-weight: 600;
}

.code-content {
  background-color: #f8f9fa;
  position: relative;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: #e9ecef;
  border-bottom: 1px solid #dee2e6;
}

.code-language {
  font-size: 0.8rem;
  font-weight: 600;
  color: #495057;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.copy-btn {
  background: none;
  border: 1px solid #ced4da;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: #6c757d;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.copy-btn:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
  color: #495057;
}

.copy-btn .copied {
  color: #28a745;
}

.code-content pre {
  margin: 0;
  padding: 1.5em;
  background-color: #f8f9fa;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85em;
  line-height: 1.5;
}

.code-content code {
  background: none;
}
</style>
