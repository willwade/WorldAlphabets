<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  locale: { type: String, required: true },
  wordsData: { type: Object, required: true },
  rulesData: { type: Object, required: true },
});

const inputWord = ref('');
const tokens = ref([]);
const renderedTokens = ref([]);
const renderedText = ref('');
const lastDiffs = ref([]);
const error = ref(null);

const wordsList = computed(() => {
  const list = [];
  if (!props.wordsData) return list;
  for (const [word, entry] of Object.entries(props.wordsData)) {
    if (word.startsWith('_') || typeof entry !== 'object' || !entry) continue;
    list.push({ ...entry, word });
  }
  return list;
});

const rules = computed(() => {
  return Array.isArray(props.rulesData?.rules) ? props.rulesData.rules : [];
});

const joinRules = computed(() => {
  return Array.isArray(props.rulesData?.join) ? props.rulesData.join : [];
});

const suggestions = computed(() => {
  if (!inputWord.value || inputWord.value.length < 1) return [];
  const q = inputWord.value.toLowerCase();
  const matches = wordsList.value
    .filter(w => w.word.toLowerCase().startsWith(q))
    .slice(0, 8);
  return matches;
});

function itemMatches(check, item) {
  const label = String(item.word || '').toLowerCase();
  let matching = true;
  if (Array.isArray(check.words)) {
    matching = check.words.includes(label);
  } else if (typeof check.type === 'string') {
    matching = Array.isArray(item.types) && item.types.includes(check.type);
  }
  if (matching && typeof check.match === 'string') {
    matching = new RegExp(check.match).test(label);
  }
  if (matching && typeof check.non_match === 'string') {
    matching = !new RegExp(check.non_match).test(label);
  }
  return matching;
}

function matchesRule(rule, buttons) {
  const lookback = rule.lookback || [];
  if (!Array.isArray(lookback)) return false;
  let historyIdx = buttons.length - 1;
  let valid = true;
  const condenses = [];
  for (let idx = lookback.length - 1; idx >= 0; idx--) {
    const check = lookback[idx];
    const preCheck = idx > 0 ? lookback[idx - 1] : null;
    if (!check || typeof check !== 'object') return false;
    const item = historyIdx >= 0 ? buttons[historyIdx] : null;
    if (item === null || item === undefined) {
      if (!check.optional) valid = false;
    } else {
      let matching = itemMatches(check, item);
      const preMatching = preCheck && typeof preCheck === 'object' && itemMatches(preCheck, item);
      const preOptional = preCheck && typeof preCheck === 'object' ? preCheck.optional : null;
      if (matching && check.optional && preMatching && !preOptional) {
        matching = false;
      }
      if (matching) {
        if (check.condense) condenses.push(historyIdx);
        historyIdx--;
      } else if (!check.optional) {
        valid = false;
      }
    }
    if (!valid) break;
  }
  if (valid && condenses.length > 0) return { condense_items: condenses };
  return valid;
}

function lookupToken(token, priorButtons) {
  const found = wordsList.value.filter(w => w.word === token);
  if (!found.length) return { surface: token, rule_id: null, rule_type: null, inflection: null };

  const foundTypes = {};
  const matchingRules = [];
  for (const rule of rules.value) {
    if (!rule || typeof rule !== 'object') continue;
    const ruleType = rule.type;
    if (typeof ruleType !== 'string') continue;
    if (foundTypes[ruleType] && ruleType !== 'override') continue;
    const m = matchesRule(rule, priorButtons);
    if (m) {
      const matched = { ...rule };
      if (typeof m === 'object' && m.condense_items) matched.condense_items = m.condense_items;
      matchingRules.push(matched);
      foundTypes[ruleType] = true;
    }
  }

  const first = { ...found[0] };
  const infl = {};
  for (const rule of matchingRules) {
    if (rule.type === 'override' && rule.overrides && typeof rule.overrides === 'object') {
      for (const [key, value] of Object.entries(rule.overrides)) {
        if (!infl[key]) infl[key] = { type: 'override', word: value, id: rule.id };
      }
    } else {
      const rt = rule.type;
      if (typeof rt === 'string') infl[rt] = rule;
    }
  }

  let replacement = null;
  let ruleId = null;
  let ruleType = null;
  let inflection = null;

  const direct = typeof first.word === 'string' ? infl[first.word] : null;
  if (direct && typeof direct === 'object' && direct.word) {
    replacement = direct.word;
    ruleId = direct.id || null;
  } else {
    let replacementRule = null;
    const types = Array.isArray(first.types) ? first.types : [];
    for (const part of types) {
      if (infl[part] && !replacementRule) replacementRule = infl[part];
    }
    if (replacementRule && typeof replacementRule === 'object') {
      const forms = first.inflections || {};
      const inflKey = replacementRule.inflection;
      if (forms && typeof forms === 'object' && typeof inflKey === 'string') {
        replacement = forms[inflKey] || first.word;
        inflection = inflKey;
      } else {
        replacement = first.word;
      }
      ruleId = replacementRule.id || null;
      ruleType = inflKey || null;
    }
  }

  return { surface: replacement || token, rule_id: ruleId, rule_type: ruleType, inflection };
}

function applyJoinRules(rawTokens) {
  if (!joinRules.value.length) return rawTokens;
  const result = [];
  let i = 0;
  while (i < rawTokens.length) {
    if (result.length > 0) {
      const prevSurface = result[result.length - 1].surface;
      const nextSurface = rawTokens[i].surface;
      const jr = findJoin(prevSurface, nextSurface);
      if (jr) {
        result[result.length - 1] = {
          ...result[result.length - 1],
          surface: jr.result,
          join_applied: jr.rule_id,
        };
        i++;
        continue;
      }
    }
    result.push(rawTokens[i]);
    i++;
  }
  return result;
}

function findJoin(prev, nextWord) {
  const prevLower = prev.toLowerCase();
  const nextLower = nextWord.toLowerCase();
  for (const rule of joinRules.value) {
    if (!rule || typeof rule !== 'object') continue;
    let prevList = rule.prev;
    if (typeof prevList === 'string') prevList = [prevList];
    if (!Array.isArray(prevList)) continue;
    if (!prevList.some(p => p.toLowerCase() === prevLower)) continue;
    let matched = false;
    if (Array.isArray(rule.next)) {
      matched = rule.next.some(n => (typeof n === 'string' ? n.toLowerCase() : '') === nextLower);
    } else if (typeof rule.next === 'string') {
      matched = rule.next.toLowerCase() === nextLower;
    }
    if (!matched && typeof rule.next_match === 'string') {
      try { matched = new RegExp(rule.next_match).test(nextLower); } catch { continue; }
    }
    if (!matched) continue;
    const template = rule.result || '{prev} {next}';
    const result = template.replace(/\{prev\}/g, prev).replace(/\{next\}/g, nextWord);
    if (template === '{prev} {next}') return null;
    return { result, rule_id: rule.id || null, reason: rule.reason || null };
  }
  return null;
}

function render() {
  const raw = [];
  for (let i = 0; i < tokens.value.length; i++) {
    const priorButtons = [];
    for (let j = 0; j < i; j++) {
      const found = wordsList.value.find(w => w.word === tokens.value[j]);
      priorButtons.push(found || { word: tokens.value[j] });
    }
    const result = lookupToken(tokens.value[i], priorButtons);
    raw.push({
      index: i,
      base: tokens.value[i],
      surface: result.surface,
      rule_id: result.rule_id,
      rule_type: result.rule_type,
      inflection: result.inflection,
    });
  }

  const oldSurfaces = renderedTokens.value.map(t => t.surface);
  const joined = applyJoinRules(raw);
  const newSurfaces = joined.map(t => t.surface);

  const diffs = [];
  const maxLen = Math.max(oldSurfaces.length, newSurfaces.length);
  for (let i = 0; i < maxLen; i++) {
    const oldS = i < oldSurfaces.length ? oldSurfaces[i] : null;
    const newS = i < newSurfaces.length ? newSurfaces[i] : null;
    if (oldS === null && newS !== null) {
      diffs.push({ index: i, kind: 'add', old: null, new: newS });
    } else if (oldS !== null && newS === null) {
      diffs.push({ index: i, kind: 'remove', old: oldS, new: '' });
    } else if (oldS !== newS) {
      diffs.push({ index: i, kind: 'change', old: oldS, new: newS });
    }
  }
  lastDiffs.value = diffs;

  renderedTokens.value = joined;
  renderedText.value = newSurfaces.join(' ');
}

function pushWord(word) {
  const w = word.trim();
  if (!w) return;
  tokens.value.push(w);
  inputWord.value = '';
  error.value = null;
  render();
}

function removeToken(index) {
  tokens.value.splice(index, 1);
  render();
}

function clearAll() {
  tokens.value = [];
  renderedTokens.value = [];
  renderedText.value = '';
  lastDiffs.value = [];
}

function submitWord() {
  pushWord(inputWord.value);
}

watch(() => [props.wordsData, props.rulesData], () => {
  clearAll();
}, { deep: false });

const wordCount = computed(() => {
  let c = 0;
  for (const key of Object.keys(props.wordsData || {})) {
    if (!key.startsWith('_')) c++;
  }
  return c;
});

const ruleCount = computed(() => rules.value.length);
const joinCount = computed(() => joinRules.value.length);
</script>

<template>
  <div class="sentence-buffer-demo">
    <p class="demo-intro">
      Build a sentence word-by-word. The engine applies inflection rules
      and euphonic joins automatically as you add words.
      <span v-if="joinCount" class="join-badge">{{ joinCount }} join rule{{ joinCount > 1 ? 's' : '' }}</span>
    </p>

    <div class="buffer-input-row">
      <input
        v-model="inputWord"
        @keydown.enter="submitWord"
        placeholder="Type a word and press Enter..."
        class="word-input"
        list="word-suggestions"
      />
      <datalist id="word-suggestions">
        <option v-for="s in suggestions" :key="s.word" :value="s.word" />
      </datalist>
      <button @click="submitWord" :disabled="!inputWord.trim()" class="btn-add">Add</button>
      <button @click="clearAll" :disabled="tokens.length === 0" class="btn-clear">Clear</button>
    </div>

    <div v-if="renderedText" class="rendered-sentence">
      <span class="label">Rendered:</span>
      <span class="sentence-text">{{ renderedText }}</span>
    </div>

    <div v-if="renderedTokens.length" class="token-list">
      <div class="token-header">
        <span>#</span>
        <span>Base</span>
        <span>Surface</span>
        <span>Rule</span>
        <span></span>
      </div>
      <div
        v-for="(t, idx) in renderedTokens"
        :key="idx"
        class="token-row"
        :class="{ changed: lastDiffs.some(d => d.index === t.index) }"
      >
        <span class="token-idx">{{ t.index + 1 }}</span>
        <span class="token-base">{{ t.base }}</span>
        <span class="token-surface" :class="{ inflected: t.surface !== t.base }">
          {{ t.surface }}
          <span v-if="t.join_applied" class="join-tag">join</span>
        </span>
        <span class="token-rule">
          <template v-if="t.rule_id">{{ t.rule_id }}</template>
          <template v-else-if="t.surface === t.base">—</template>
        </span>
        <button @click="removeToken(t.index)" class="btn-remove" title="Remove">x</button>
      </div>
    </div>

    <div v-if="lastDiffs.length && renderedTokens.length" class="diffs-section">
      <span class="label">Changes:</span>
      <span
        v-for="d in lastDiffs"
        :key="d.index"
        class="diff-chip"
        :class="d.kind"
      >
        {{ d.kind === 'add' ? '+' : d.kind === 'remove' ? '-' : '~' }}
        {{ d.new }}
      </span>
    </div>

    <div class="demo-stats">
      {{ wordCount }} words &middot; {{ ruleCount }} rules &middot; {{ joinCount }} joins
    </div>
  </div>
</template>

<style scoped>
.sentence-buffer-demo {
  margin-top: 1em;
}

.demo-intro {
  font-size: 0.9em;
  color: #555;
  margin-bottom: 1em;
}

.join-badge {
  display: inline-block;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 10px;
  padding: 1px 8px;
  font-size: 0.8em;
  margin-left: 0.5em;
}

.buffer-input-row {
  display: flex;
  gap: 0.5em;
  margin-bottom: 1em;
}

.word-input {
  flex: 1;
  padding: 0.5em 0.75em;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

.btn-add {
  padding: 0.5em 1em;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.95em;
}

.btn-add:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-clear {
  padding: 0.5em 1em;
  background: #f5f5f5;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.95em;
}

.btn-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rendered-sentence {
  background: #f0f4ff;
  border: 1px solid #c5d5f0;
  border-radius: 6px;
  padding: 0.75em 1em;
  margin-bottom: 1em;
}

.rendered-sentence .label {
  font-weight: 600;
  color: #336;
  margin-right: 0.5em;
}

.sentence-text {
  font-size: 1.15em;
  font-weight: 500;
}

.token-list {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.75em;
}

.token-header,
.token-row {
  display: grid;
  grid-template-columns: 2.5em 1fr 1fr 1fr 2.5em;
  gap: 0.5em;
  padding: 0.4em 0.75em;
  align-items: center;
  font-size: 0.9em;
}

.token-header {
  background: #f5f5f5;
  font-weight: 600;
  color: #666;
  border-bottom: 1px solid #e0e0e0;
}

.token-row {
  border-bottom: 1px solid #f0f0f0;
}

.token-row:last-child {
  border-bottom: none;
}

.token-row.changed {
  background: #fffde7;
}

.token-idx {
  color: #999;
  font-size: 0.85em;
}

.token-base {
  color: #555;
}

.token-surface {
  font-weight: 500;
}

.token-surface.inflected {
  color: #0066cc;
}

.join-tag {
  display: inline-block;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 8px;
  padding: 0 6px;
  font-size: 0.75em;
  margin-left: 0.4em;
  font-weight: 600;
}

.token-rule {
  color: #888;
  font-size: 0.85em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-remove {
  background: none;
  border: none;
  color: #cc4444;
  cursor: pointer;
  font-size: 1em;
  padding: 0;
  opacity: 0.5;
}

.btn-remove:hover {
  opacity: 1;
}

.diffs-section {
  margin-bottom: 0.75em;
  font-size: 0.85em;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4em;
}

.diffs-section .label {
  font-weight: 600;
  color: #666;
}

.diff-chip {
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 0.85em;
}

.diff-chip.add {
  background: #e8f5e9;
  color: #2e7d32;
}

.diff-chip.remove {
  background: #fbe9e7;
  color: #c62828;
}

.diff-chip.change {
  background: #fff8e1;
  color: #f57f17;
}

.demo-stats {
  font-size: 0.8em;
  color: #999;
  margin-top: 0.5em;
}
</style>
