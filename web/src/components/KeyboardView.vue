<script setup>
defineProps({
  layoutData: Object
});
</script>

<template>
  <div>
    <h3>Keyboard Layout</h3>
    <div v-if="layoutData" class="keyboard-container">
      <div
        v-for="key in layoutData.keys"
        :key="key.sc"
        class="key"
        :style="{
          left: `${key.shape.x * 20}px`,
          top: `${key.shape.y * 20}px`,
          width: `${key.shape.w * 20}px`,
          height: `${key.shape.h * 20}px`,
        }"
      >
        {{ key.legends.base || '' }}
      </div>
    </div>
    <div v-else>
      <p>No keyboard layout available for this language.</p>
    </div>
  </div>
</template>

<style scoped>
.keyboard-container {
  position: relative;
  min-height: 200px; /* Adjust as needed */
  margin-top: 1em;
  border: 1px solid #ccc;
  padding: 1em;
  border-radius: 4px;
  overflow: auto;
}

.key {
  position: absolute;
  border: 1px solid #999;
  border-radius: 4px;
  background-color: #f9f9f9;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.8em;
  box-sizing: border-box;
}
</style>
