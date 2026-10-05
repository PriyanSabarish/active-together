<template>
  <AppHeader />
  <div class="scroll-area hub">
    <h1>You</h1>

    <div class="card block">
      <p class="block-title">Your kid's age</p>
      <p class="block-sub">Missions are pitched to this age band.</p>
      <div class="seg" role="radiogroup" aria-label="Age band">
        <button
          v-for="b in AGE_BANDS"
          :key="b.id"
          class="seg-opt"
          :class="{ on: prefs.ageBand === b.id }"
          role="radio"
          :aria-checked="prefs.ageBand === b.id"
          @click="prefs.setAgeBand(b.id)"
        >
          {{ b.id.replace('-', '–') }}
        </button>
      </div>
    </div>

    <button class="card block as-btn" @click="router.push('/you/outings')">
      <span class="block-head">
        <span class="block-title">Your outings</span>
        <Chevron />
      </span>
      <span class="stats">{{ statsLine }}</span>
      <template v-if="thumbs.length">
        <span class="thumbs">
          <span v-for="p in thumbs" :key="p.id" class="thumb" :style="tileStyle(p)" />
        </span>
        <span class="block-sub">Photos saved only on this phone</span>
      </template>
      <span v-else class="block-sub empty-line">{{ historyStore.records.length ? "Take a photo at the end of a mission and it'll show up here." : 'Photos from your outings will show up here.' }}</span>
    </button>

    <button class="card block as-btn" @click="router.push('/you/likes')">
      <span class="block-head">
        <span class="block-title">What your kid likes</span>
        <Chevron />
      </span>
      <span v-if="likes.length" class="likes">
        <span v-for="c in likes" :key="c.key" class="like" :class="c.up ? 'up' : 'down'" :title="c.label">
          <svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(c.key)" /></svg>
          <span class="badge-dot">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path :d="c.up ? THUMB_UP : THUMB_DOWN" /></svg>
          </span>
        </span>
      </span>
      <span v-else class="block-sub empty-line">Not set yet</span>
    </button>

    <button class="card row-link as-btn" @click="router.push('/you/about')">
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9" /><path d="M12 11v5.5 M12 7.8v.01" /></svg>
      <span class="row-label">About</span>
      <Chevron />
    </button>

    <button class="btn btn-outline replay" @click="replayIntro">Replay the intro</button>
  </div>
</template>

<script setup>
// You tab hub (Canvas → You): age band, a summary of the outings with the
// latest photos, what the kid likes, About, and replaying the intro. Each card
// opens its own page. Everything here is device-local.

import { computed, h } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { CATEGORY_META } from '../store'
import { usePreferencesStore, AGE_BANDS } from '../preferencesStore'
import { useHistoryStore, weekStreak } from '../historyStore'
import { usePhotosFor, tileStyle } from '../journal'
import { categoryIcon, THUMB_UP, THUMB_DOWN } from '../taskIcons'

const router = useRouter()
const prefs = usePreferencesStore()
const historyStore = useHistoryStore()
const photosFor = usePhotosFor()

const Chevron = () => h('svg', { width: 8, height: 13, viewBox: '0 0 8 13', fill: 'none', stroke: 'rgba(30,42,31,.28)', 'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', class: 'chev' }, [h('path', { d: 'M1.5 1.5 6.5 6.5l-5 5' })])

const statsLine = computed(() => {
  const recs = historyStore.records
  const places = new Set(recs.filter((r) => r.placeName !== 'Home').map((r) => r.placeName)).size
  const kinds = new Set(recs.map((r) => r.category)).size
  if (!recs.length) return '0 places · 0 kinds of play'
  const streak = weekStreak(recs)
  const parts = [`${places} ${places === 1 ? 'place' : 'places'}`, `${kinds} ${kinds === 1 ? 'kind' : 'kinds'} of play`]
  if (streak) parts.push(`${streak} ${streak === 1 ? 'week' : 'weeks in a row'}`)
  return parts.join(' · ')
})

const thumbs = computed(() => historyStore.records.flatMap((r) => photosFor(r).slice(0, 1)).slice(0, 3))

// Likes first, then not-for-me; "no preference" is left out.
const likes = computed(() => Object.entries(prefs.affinities)
  .filter(([, v]) => v >= 67 || v < 34)
  .sort(([, a], [, b]) => b - a)
  .map(([key, v]) => ({ key, up: v >= 67, label: CATEGORY_META[key]?.label ?? key })))

// The walkthrough is gated on a localStorage flag in App.vue; clearing it and
// reloading is the simplest way to see it again.
function replayIntro() {
  try {
    localStorage.removeItem('at-onboarded-v1')
    sessionStorage.removeItem('at-admin-authed') // the intro is shown right after the gate
  } catch {
    /* storage unavailable */
  }
  window.location.assign('/')
}
</script>

<style scoped>
.hub { display: flex; flex-direction: column; gap: 12px; padding-bottom: 18px; }
.hub h1 { margin: 4px 0 4px; font-size: 29px; letter-spacing: -0.8px; }

.block { padding: 16px 18px; }
.as-btn { border: none; font-family: inherit; color: var(--ink); text-align: left; cursor: pointer; display: flex; flex-direction: column; width: 100%; }
.as-btn:active { transform: scale(0.99); }

.block-head { display: flex; align-items: center; gap: 10px; width: 100%; }
.block-title { flex: 1; font-family: var(--font-display); font-weight: 600; font-size: 17px; letter-spacing: -0.3px; }
.block-sub { display: block; margin-top: 2px; font-size: 13px; color: rgba(30, 42, 31, 0.55); }
.empty-line { margin-top: 8px; font-size: 13.5px; line-height: 1.45; }

.seg { display: flex; gap: 4px; margin-top: 12px; padding: 3px; border-radius: 13px; background: rgba(30, 42, 31, 0.055); }
.seg-opt { flex: 1; height: 44px; border: none; border-radius: 10px; background: transparent; font-family: inherit; font-size: 14px; font-weight: 600; color: var(--ink-3); cursor: pointer; transition: all 0.15s ease; }
.seg-opt.on { background: var(--green); color: var(--paper); box-shadow: 0 1px 3px rgba(30, 42, 31, 0.18); }

.stats { margin-top: 4px; font-size: 13px; font-weight: 600; color: var(--green); }
.thumbs { display: flex; gap: 8px; margin: 12px 0 8px; }
.thumb { width: 84px; height: 84px; border-radius: 13px; }

.likes { display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
.like { position: relative; width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.like.up { background: rgba(47, 107, 54, 0.12); color: var(--green); }
.like.down { background: rgba(196, 118, 30, 0.13); color: #A85E12; }
.badge-dot { position: absolute; right: -3px; bottom: -3px; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 2px #FFFFFF; }
.like.up .badge-dot { background: var(--green); }
.like.down .badge-dot { background: #C4761E; }

.row-link { flex-direction: row; align-items: center; gap: 12px; padding: 14px 18px; color: var(--ink); }
.row-link > svg:first-child { color: rgba(30, 42, 31, 0.5); }
.row-label { flex: 1; font-size: 15.5px; font-weight: 600; }

.replay { width: 100%; height: 52px; border-radius: 999px; margin-top: 4px; box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.2); }
</style>
