<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  layoutData: Object,
  layoutName: String,
  total: Number,
});

const LAYER_LABELS = {
  base: 'Base',
  shift: 'Shift',
  caps: 'Caps Lock',
  altgr: 'AltGr',
  shift_altgr: 'Shift + AltGr',
  ctrl: 'Ctrl',
  alt: 'Alt',
};

const LAYER_ORDER = ['base', 'shift', 'caps', 'altgr', 'shift_altgr', 'ctrl', 'alt'];
const LAYER_FALLBACKS = {
  base: [],
  shift: ['base'],
  caps: ['shift', 'base'],
  altgr: ['base'],
  shift_altgr: ['altgr', 'shift', 'base'],
  ctrl: [],
  alt: ['base'],
};

const LAYOUT_ROWS = [
  [
    'Backquote',
    'Digit1',
    'Digit2',
    'Digit3',
    'Digit4',
    'Digit5',
    'Digit6',
    'Digit7',
    'Digit8',
    'Digit9',
    'Digit0',
    'Minus',
    'Equal',
  ],
  [
    'KeyQ',
    'KeyW',
    'KeyE',
    'KeyR',
    'KeyT',
    'KeyY',
    'KeyU',
    'KeyI',
    'KeyO',
    'KeyP',
    'BracketLeft',
    'BracketRight',
  ],
  [
    'KeyA',
    'KeyS',
    'KeyD',
    'KeyF',
    'KeyG',
    'KeyH',
    'KeyJ',
    'KeyK',
    'KeyL',
    'Semicolon',
    'Quote',
    'Backslash',
  ],
  [
    'KeyZ',
    'KeyX',
    'KeyC',
    'KeyV',
    'KeyB',
    'KeyN',
    'KeyM',
    'Comma',
    'Period',
    'Slash',
  ],
  ['Space'],
];

const ROW_OFFSETS = [0, 1, 1, 2, 5];

const selectedLayer = ref('base');

watch(
  () => props.layoutData,
  () => {
    selectedLayer.value = 'base';
  }
);

const availableLayers = computed(() => {
  const data = props.layoutData;
  if (!data || !Array.isArray(data.keys)) {
    return ['base'];
  }
  const present = new Set();
  for (const key of data.keys) {
    if (!key || !key.legends) continue;
    for (const layer of LAYER_ORDER) {
      const value = key.legends[layer];
      if (value) {
        present.add(layer);
      }
    }
  }
  present.add('base');
  return LAYER_ORDER.filter(layer => present.has(layer));
});

function legendFor(key, layer) {
  if (!key || !key.legends) return '';
  const direct = key.legends[layer];
  if (direct) return direct;
  const fallbacks = LAYER_FALLBACKS[layer] || [];
  for (const fallback of fallbacks) {
    const value = key.legends[fallback];
    if (value) return value;
  }
  return '';
}

const rows = computed(() => {
  const data = props.layoutData;
  if (!data || !Array.isArray(data.keys)) {
    return [];
  }
  const keyByPos = {};
  for (const k of data.keys) {
    if (k.pos) {
      keyByPos[k.pos] = k;
    }
  }
  return LAYOUT_ROWS.map((row, idx) => {
    const off = ROW_OFFSETS[idx];
    const cells = Array(off).fill('');
    for (const pos of row) {
      const key = keyByPos[pos];
      const value = legendFor(key, selectedLayer.value);
      const display = value === ' ' ? '␠' : value;
      cells.push(display || '');
    }
    return cells;
  });
});

function hasRows() {
  return rows.value.length > 0;
}

function setLayer(layer) {
  selectedLayer.value = layer;
}
</script>

<template>
  <div>
    <h3>Keyboard Layout</h3>
    <p class="keyboard-count" v-if="typeof total === 'number'">
      {{ total }} keyboard layout{{ total === 1 ? '' : 's' }} available
    </p>
    <p v-if="layoutName" class="keyboard-name">{{ layoutName }}</p>
    <div
      v-if="availableLayers.length > 1"
      class="layer-selector"
    >
      <button
        v-for="layer in availableLayers"
        :key="layer"
        type="button"
        :class="['layer-button', { active: selectedLayer === layer }]"
        @click="setLayer(layer)"
      >
        {{ LAYER_LABELS[layer] || layer }}
      </button>
    </div>
    <table v-if="hasRows()" class="keyboard-table">
      <tbody>
        <tr v-for="(row, rIdx) in rows" :key="rIdx">
          <td v-for="(cell, cIdx) in row" :key="cIdx">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else>
      <p>No preview for this keyboard layout.</p>
    </div>
  </div>
</template>

<style scoped>
.keyboard-table {
  border-collapse: collapse;
  margin-top: 1em;
}

.keyboard-table td {
  border: 1px solid #ccc;
  padding: 4px;
  min-width: 20px;
  text-align: center;
}

.keyboard-count {
  margin-top: 0.5em;
}
.keyboard-name {
  margin-top: 0.25em;
}
h3 {
  margin-bottom: 0.5em;
}

.layer-selector {
  margin: 0.75em 0 0.25em;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
}

.layer-button {
  border: 1px solid #ccc;
  background: #f6f6f6;
  padding: 0.25em 0.6em;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.layer-button.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.layer-button:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
