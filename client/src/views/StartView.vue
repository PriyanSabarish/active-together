<template>
  <AppHeader />
  <div class="scroll-area setup">
    <span class="setup-glyph">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <circle cx="12" cy="12" r="7" /><circle cx="12" cy="12" r="2.2" fill="currentColor" stroke="none" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
      </svg>
    </span>
    <h1>Set up where you're starting</h1>
    <p class="subtitle">We need a starting point and how long you've got before we can suggest anything nearby.</p>
    <button class="btn btn-primary cta" @click="router.push('/location')">Set up now <span class="btn-arrow">→</span></button>
    <p class="setup-note">Takes a few seconds, once. You can change it any time from the results.</p>
  </div>
</template>

<script setup>
// Start tab root. First run shows a single setup card that routes into the
// location form; once setup has been completed (store.setupDone, persisted)
// it redirects straight to the results so a parent never redoes the steps.

import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useSearchStore } from '../store'

// Gap 1 — Start has a first-run state. A parent who has already been through
// where / how far / how long lands straight on their top options; a new one
// gets one card that routes into the same setup steps, not a second copy.
const router = useRouter()
const store = useSearchStore()

if (store.setupDone && store.hasLocation) router.replace('/results')
</script>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 28px;
}

.setup-glyph {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--green-light);
  color: var(--green);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.setup h1 { text-wrap: balance; }
.cta { width: 100%; margin-top: 22px; }
.setup-note { margin-top: 14px; font-size: 12.5px; color: var(--ink-4); line-height: 1.5; }
</style>
