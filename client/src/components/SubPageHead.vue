<template>
  <div>
    <button class="back" aria-label="Back" @click="router.push(to)">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 12h-14 M11.5 6l-6 6 6 6" /></svg>
    </button>
    <h1 class="title">{{ title }}</h1>
  </div>
</template>

<script setup>
// Round back arrow and a big title, for pages one level under a tab (You →
// outings, likes, about).

import { useRouter } from 'vue-router'

defineProps({
  title: { type: String, required: true },
  to: { type: String, default: '/you' }
})
const router = useRouter()
</script>

<style scoped>
.back {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--tint);
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 12px;
}

.title { margin: 0 0 16px; font-size: 29px; letter-spacing: -0.8px; }
</style>
