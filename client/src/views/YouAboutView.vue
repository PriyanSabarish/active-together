<template>
  <AppHeader />
  <div class="scroll-area">
    <SubPageHead title="About" />
    <div class="cards">
      <div class="card info">
        <p class="info-title">Coverage</p>
        <p class="info-body">City of Melbourne, Monash and Melton. Park and playground locations come from council open data.</p>
      </div>
      <div class="card info">
        <p class="info-title">No account</p>
        <p class="info-body">Nothing to sign up for. Preferences and your week stay on this phone.</p>
      </div>
      <div class="card info">
        <p class="info-title">Photos</p>
        <p class="info-body">Outing photos never leave this phone. A photo-check image is sent once for the check and not kept on our servers.</p>
      </div>
      <button class="card info as-btn" @click="toggleDemo">
        <span class="info-title">Demo data</span>
        <span class="info-body">{{ demoOn ? 'Week and You show sample outings and preferences.' : 'Off — Week starts empty until a mission is finished.' }}</span>
        <span class="change-link">{{ demoOn ? 'Turn off' : 'Turn on' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
// You → About: coverage, no-account and photo privacy notes, plus the
// demo-data switch for the pilot.

import { ref } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import SubPageHead from '../components/SubPageHead.vue'
import { demoEnabled, setDemoEnabled } from '../demoSeed'

const demoOn = ref(demoEnabled())

// Demo data is seeded at boot, so flipping it reloads the app.
function toggleDemo() {
  setDemoEnabled(!demoOn.value)
  window.location.assign('/week')
}
</script>

<style scoped>
.cards { display: flex; flex-direction: column; gap: 11px; padding-bottom: 18px; }
.info { position: relative; padding: 16px 18px; border-radius: 16px; }
.info-title { display: block; font-family: var(--font-display); font-weight: 600; font-size: 15.5px; margin-bottom: 4px; }
.info-body { display: block; font-size: 13.5px; line-height: 1.5; color: rgba(30, 42, 31, 0.6); }
.as-btn { border: none; font-family: inherit; color: var(--ink); text-align: left; cursor: pointer; display: flex; flex-direction: column; width: 100%; }
.as-btn .info-body { padding-right: 70px; }
.change-link { position: absolute; right: 18px; top: 16px; font-size: 13.5px; font-weight: 600; color: var(--green); }
</style>
