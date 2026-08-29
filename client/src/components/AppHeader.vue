<template>
  <div>
    <div class="app-bar">
      <button v-if="back" class="back-btn" aria-label="Back" @click="$router.back()">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <svg class="logo-pin" width="26" height="32" viewBox="0 0 100 126" aria-hidden="true">
        <path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" fill="#2E8540" />
        <circle cx="50" cy="34" r="12" fill="#F49B1B" />
        <path d="M28 54 Q50 70 72 54" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" />
        <path d="M32 78 Q50 92 68 78" fill="none" stroke="#7CBE7A" stroke-width="10" stroke-linecap="round" />
      </svg>
      <span class="app-name"><b class="w-active">Active</b> <b class="w-together">Together</b><b class="w-dot">.</b></span>
    </div>
    <div class="stepper" aria-label="Progress">
      <span v-for="i in 3" :key="i" :class="{ on: i <= step }" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  step: { type: Number, required: true },
  back: { type: Boolean, default: false }
})
</script>

<style scoped>
.logo-pin { flex-shrink: 0; }

.app-name b { font-weight: 700; }
.w-active { color: #2E8540; }
.w-together { color: #17332A; }
.w-dot { color: #F49B1B; }
</style>
