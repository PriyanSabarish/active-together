<template>
  <AppHeader plain />
  <div class="scroll-area placeholder">
    <p class="section-eyebrow">Plan</p>
    <h1>No mission chosen yet</h1>
    <p class="subtitle">Mission preview, picking and running will live here.</p>
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
