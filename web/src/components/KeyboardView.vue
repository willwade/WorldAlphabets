<script setup>
import { computed } from 'vue';

const props = defineProps({
  layoutData: Object,
  total: Number,
});

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

const rows = computed(() => {
  const data = props.layoutData;
  if (!data || !Array.isArray(data.keys)) {
    return [];
  }
  const keyByPos = {};
  for (const k of data.keys) {
    keyByPos[k.pos] = k;
  }
  return LAYOUT_ROWS.map((row, idx) => {
    const off = ROW_OFFSETS[idx];
    const cells = Array(off).fill('');
    for (const pos of row) {
      const key = keyByPos[pos];
      let val = '';
      if (key && key.legends && key.legends.base) {
        val = key.legends.base === ' ' ? '␠' : key.legends.base;
      }
      cells.push(val || '');
    }
    return cells;
  });
});

function hasRows() {
  return rows.value.length > 0;
}
</script>

<template>
  <div>
    <h3>Keyboard Layout</h3>
    <p class="keyboard-count" v-if="typeof total === 'number'">
      Showing first of {{ total }} keyboard layout{{ total === 1 ? '' : 's' }}
    </p>
    <table v-if="hasRows()" class="keyboard-table">
      <tbody>
        <tr v-for="(row, rIdx) in rows" :key="rIdx">
          <td v-for="(cell, cIdx) in row" :key="cIdx">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else>
      <p>No keyboard layout available for this language.</p>
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
h3 {
  margin-bottom: 0.5em;
}
</style>

