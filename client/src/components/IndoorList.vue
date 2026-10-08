<template>
  <div class="scroll-area">
    <h1>Your top options</h1>
    <p class="subtitle">Pick a place and we'll get you there.</p>

    <template v-if="store.indoorResults.length">
      <PlaceMap class="map" :center="store.coords" :places="store.indoorResults" fit numbered you-chip height="150px" @select="openById" />

      <article v-for="p in store.indoorResults" :key="p.id" class="card" role="button" tabindex="0" @click="open(p)" @keydown.enter="open(p)">
        <div class="card-top">
          <span class="icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 20V8l7.5-4 7.5 4v12 M4.5 20h15 M9 20v-5h6v5 M9 10.5h.01 M15 10.5h.01" /></svg>
          </span>
          <div class="card-title">
            <p class="name">{{ p.name }}</p>
            <p class="meta">{{ p.categoryLabel }} · {{ p.distanceKm }} km</p>
          </div>
          <span class="unverified">Unverified</span>
        </div>
        <div class="card-foot">
          <span class="dir-pill">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 3 3 10.5l7.5 2.5L13 21Z" /></svg>
            Get directions
          </span>
        </div>
      </article>
      <p class="footnote">Check hours and cost before you go.</p>
    </template>

    <div v-else class="empty">
      <span class="empty-glyph">?</span>
      <p class="empty-title">No indoor places within {{ store.radiusKm }} km</p>
      <p class="empty-text">Try a longer trip on Start, or play at home instead.</p>
      <button class="btn btn-primary" @click="tryHome">Play at home</button>
    </div>
  </div>
</template>

<script setup>
// Play tab for an Indoor place (story 9.3): nearby indoor places, nearest
// first, each labelled unverified. No mission, weather or travel breakdown —
// a place opens its page with directions and a "Completed" button. Mock data
// until the backend's indoor_place setting is wired (store.searchIndoor).

import { useRouter } from 'vue-router'
import PlaceMap from './PlaceMap.vue'
import { useSearchStore } from '../store'

const router = useRouter()
const store = useSearchStore()

if (!store.indoorResults.length && store.hasLocation) store.searchIndoor()

function open(p) {
  router.push(`/play/indoor/${p.id}`)
}

function openById(id) {
  const p = store.indoorPlace(id)
  if (p) open(p)
}

function tryHome() {
  store.setting = 'home'
  router.push('/')
}
</script>

<style scoped>
.subtitle { margin-bottom: 14px; }
.map { margin-bottom: 14px; }

.card { margin-bottom: 12px; padding: 15px 18px; border-radius: 18px; background: var(--card); box-shadow: var(--shadow-card); cursor: pointer; }
.card-top { display: flex; align-items: flex-start; gap: 12px; }
.icon { width: 38px; height: 38px; flex: none; border-radius: 50%; background: rgba(47, 107, 54, 0.12); display: flex; align-items: center; justify-content: center; }
.card-title { flex: 1; min-width: 0; }
.name { font-family: var(--font-display); font-weight: 600; font-size: 17.5px; letter-spacing: -0.3px; }
.meta { margin-top: 2px; font-size: 13px; color: rgba(30, 42, 31, 0.55); }
.unverified { padding: 5px 11px; border-radius: 999px; font-size: 12px; font-weight: 600; white-space: nowrap; color: var(--amber); background: var(--amber-light); }
.card-foot { display: flex; margin-top: 12px; }
.dir-pill { display: flex; align-items: center; gap: 5px; padding: 5px 11px; border-radius: 999px; font-size: 12px; font-weight: 600; color: var(--green); background: rgba(47, 107, 54, 0.12); }

.footnote { margin: 4px 2px 12px; font-size: 12.5px; color: var(--ink-4); text-align: center; }

.empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 48px 12px 0; }
.empty-glyph { width: 64px; height: 64px; border-radius: 50%; background: var(--tint); color: var(--ink-4); font-family: var(--font-display); font-size: 28px; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; }
.empty-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; }
.empty-text { font-size: 14px; color: var(--ink-3); margin-bottom: 10px; }
.empty .btn { width: 100%; }
</style>
