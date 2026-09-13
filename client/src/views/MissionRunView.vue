<template>
  <AppHeader plain />
  <div class="scroll-area placeholder">
    <p class="section-eyebrow">Plan</p>
    <h1 v-if="mission">{{ mission.title }} is running</h1>
    <h1 v-else>No mission running</h1>
    <p class="subtitle">
      One step at a time, confirm-or-skip — built in F17.
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'

const missionStore = useMissionStore()
const mission = computed(() => missionStore.active)
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
