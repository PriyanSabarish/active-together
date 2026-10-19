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
    </div>
  </div>
</template>

<script setup>
// You → About: coverage, no-account and photo privacy notes.

import AppHeader from '../components/AppHeader.vue'
import SubPageHead from '../components/SubPageHead.vue'
</script>

<style scoped>
.cards { display: flex; flex-direction: column; gap: 11px; padding-bottom: 18px; }
.info { position: relative; padding: 16px 18px; border-radius: 16px; }
.info-title { display: block; font-family: var(--font-display); font-weight: 600; font-size: 15.5px; margin-bottom: 4px; }
.info-body { display: block; font-size: 13.5px; line-height: 1.5; color: rgba(30, 42, 31, 0.6); }
</style>
