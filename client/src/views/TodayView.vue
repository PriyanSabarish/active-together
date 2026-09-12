<template>
  <AppHeader plain />
  <div class="scroll-area placeholder">
    <p class="section-eyebrow">Today</p>
    <h1>Nothing planned yet</h1>
    <p class="subtitle">Once preferences and missions are wired up, this becomes the daily mission card.</p>
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
</script>

<style scoped>
.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
