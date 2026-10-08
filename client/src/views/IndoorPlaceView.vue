<template>
  <AppHeader />
  <div class="scroll-area">
    <button class="pill crumb" @click="router.push('/play')">‹ All places</button>

    <template v-if="place">
      <h1 class="name">{{ place.name }}</h1>
      <p class="subtitle">{{ place.categoryLabel }} · {{ place.distanceKm }} km away</p>
      <p class="unverified">Unverified — check hours and cost before you go.</p>

      <h2 class="sect">Getting there</h2>
      <PlaceMap :center="store.coords" :places="[place]" fit you-chip height="190px" />

      <a class="directions" :href="directionsUrl" target="_blank" rel="noopener">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 3 3 10.5l7.5 2.5L13 21Z" /></svg>
        Get directions
      </a>
      <button class="btn btn-primary completed" @click="complete">Completed</button>
    </template>

    <template v-else>
      <h1 class="name">Place not found</h1>
      <p class="subtitle">Go back to the list and pick another.</p>
    </template>
  </div>
</template>

<script setup>
// One indoor place: where it is, directions in the phone's maps app, and
// "Completed" once you've been — that logs a visit (no mission, no photo).

import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import PlaceMap from '../components/PlaceMap.vue'
import { useSearchStore } from '../store'
import { useMissionStore } from '../missionStore'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const store = useSearchStore()
const missionStore = useMissionStore()

const place = computed(() => store.indoorPlace(props.id))
const directionsUrl = computed(() => {
  const p = place.value
  return `https://www.google.com/maps/dir/?api=1&destination=${p.latitude.toFixed(5)},${p.longitude.toFixed(5)}`
})

function complete() {
  missionStore.completeVisit(place.value, store.stayMin)
  router.push('/play/finished')
}
</script>

<style scoped>
.name { margin: 12px 0 6px; font-size: 29px; letter-spacing: -0.8px; }
.unverified { margin-top: 10px; padding: 9px 12px; border-radius: 12px; background: var(--amber-light); color: var(--amber); font-size: 13px; font-weight: 600; }
.sect { margin: 22px 0 12px; }

.directions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(47, 107, 54, 0.12);
  color: var(--green);
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
}

.completed { width: 100%; margin-top: 12px; border-radius: 999px; }
</style>
