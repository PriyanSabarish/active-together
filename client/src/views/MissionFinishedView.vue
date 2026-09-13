<template>
  <AppHeader plain />
  <div class="scroll-area placeholder">
    <p class="section-eyebrow">Plan</p>
    <h1 v-if="mission">{{ mission.title }}, done!</h1>
    <h1 v-else>No mission to finish</h1>
    <p class="subtitle">
      Feedback, the activity record and a keepsake photo — built in F19.
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
