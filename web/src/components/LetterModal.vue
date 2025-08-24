<script setup>
const props = defineProps({
  letter: String,
  show: Boolean
});

const emit = defineEmits(['close', 'copy']);

function copyLetter() {
  emit('copy', props.letter);
}
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <span class="modal-close" @click="$emit('close')">&times;</span>
      <div class="modal-letter">{{ letter }}</div>
      <button @click="copyLetter">Copy</button>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2em;
  border-radius: 8px;
  text-align: center;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 1.5em;
  cursor: pointer;
}

.modal-letter {
  font-size: 10em;
  margin-bottom: 0.2em;
}
</style>
