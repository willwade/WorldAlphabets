<script setup>
import { ref, computed } from 'vue';
import LetterModal from './LetterModal.vue';

const props = defineProps({
  alphabetData: Object
});

const activeTab = ref('alphabetical');
const showModal = ref(false);
const modalLetter = ref('');
const copyAllText = ref('Copy All');

const frequencySortedAlphabet = computed(() => {
  if (!props.alphabetData || !props.alphabetData.frequency) return [];

  const sorted = Object.entries(props.alphabetData.frequency)
    .sort(([, freqA], [, freqB]) => freqB - freqA);

  const maxFreq = sorted.length > 0 ? sorted[0][1] : 0;

  return sorted.map(([letter, freq]) => ({
    letter,
    freq,
    barWidth: maxFreq > 0 ? (freq / maxFreq) * 100 : 0
  }));
});

const currentAlphabet = computed(() => {
  if (!props.alphabetData) return [];
  switch (activeTab.value) {
    case 'uppercase':
      return props.alphabetData.uppercase || [];
    case 'lowercase':
      return props.alphabetData.lowercase || [];
    case 'frequency':
      return frequencySortedAlphabet.value.map(item => item.letter);
    default:
      return props.alphabetData.alphabetical || [];
  }
});

function openLetterModal(letter) {
  modalLetter.value = letter;
  showModal.value = true;
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(err => {
    console.error('Could not copy text: ', err);
  });
}

function handleCopyAll() {
  const alphabetString = currentAlphabet.value.join('\n');
  copyToClipboard(alphabetString);
  copyAllText.value = 'Copied!';
  setTimeout(() => copyAllText.value = 'Copy All', 1500);
}

function handleCopyLetter(letter) {
  copyToClipboard(letter);
}
</script>

<template>
  <div>
    <div class="header-container">
      <h3>Letters</h3>
      <button @click="handleCopyAll" v-if="currentAlphabet.length > 0">{{ copyAllText }}</button>
    </div>

    <div class="tabs">
      <button @click="activeTab = 'alphabetical'" :class="{ active: activeTab === 'alphabetical' }">Alphabetical</button>
      <button @click="activeTab = 'uppercase'" :class="{ active: activeTab === 'uppercase' }">Uppercase</button>
      <button @click="activeTab = 'lowercase'" :class="{ active: activeTab === 'lowercase' }">Lowercase</button>
      <button @click="activeTab = 'frequency'" :class="{ active: activeTab === 'frequency' }">Frequency</button>
    </div>

    <div v-if="activeTab !== 'frequency'" class="alphabet-grid">
      <span
        v-for="letter in currentAlphabet"
        :key="letter"
        class="letter-box"
        @click="openLetterModal(letter)"
      >
        {{ letter }}
      </span>
    </div>

    <div v-else class="frequency-list">
      <div v-for="item in frequencySortedAlphabet" :key="item.letter" class="freq-item">
        <span class="freq-letter" @click="openLetterModal(item.letter)">{{ item.letter }}</span>
        <div class="freq-bar-container">
          <div class="freq-bar" :style="{ width: item.barWidth + '%' }"></div>
        </div>
        <span class="freq-value">{{ item.freq.toFixed(4) }}</span>
      </div>
    </div>

    <LetterModal
      :show="showModal"
      :letter="modalLetter"
      @close="showModal = false"
      @copy="handleCopyLetter"
    />
  </div>
</template>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  gap: 1em;
  margin-bottom: 1em;
}
h3 {
  margin: 0;
}
.tabs {
  margin-bottom: 1em;
}
.tabs button {
  padding: 0.5em 1em;
  border: 1px solid #ccc;
  background-color: #f9f9f9;
  cursor: pointer;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
}
.tabs button.active {
  background-color: white;
  border-bottom: 1px solid white;
  position: relative;
  top: 1px;
}
.alphabet-grid, .frequency-list {
  border: 1px solid #ccc;
  padding: 1em;
  border-radius: 0 4px 4px 4px;
}
.alphabet-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
}
.letter-box {
  border: 1px solid #ccc;
  padding: 0.5em;
  border-radius: 4px;
  min-width: 2em;
  text-align: center;
  cursor: pointer;
}
.letter-box:hover {
  background-color: #e0e0e0;
}
.frequency-list {
  margin-top: -1px; /* to align with the tabs border */
}
.freq-item {
  display: flex;
  align-items: center;
  margin-bottom: 0.5em;
  gap: 0.5em;
}
.freq-letter {
  width: 2em;
  font-weight: bold;
  cursor: pointer;
  text-align: center;
}
.freq-bar-container {
  flex-grow: 1;
  height: 1.2em;
  background-color: #f0f0f0;
  border-radius: 4px;
}
.freq-bar {
  height: 100%;
  background-color: #42b983; /* Vue green :) */
  border-radius: 4px;
}
.freq-value {
  font-family: monospace;
  font-size: 0.9em;
  width: 4em;
}
</style>
