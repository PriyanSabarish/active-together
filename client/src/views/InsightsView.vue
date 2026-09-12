<template>
  <AppHeader plain />
  <div class="scroll-area placeholder">
    <p class="section-eyebrow">Insights</p>
    <h1>No activity logged yet</h1>
    <p class="subtitle">Weekly counts and a by-day breakdown will show up here once missions are completed.</p>
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
