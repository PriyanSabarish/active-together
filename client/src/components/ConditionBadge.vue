<template>
  <span class="badge" :class="badge.type">
    <svg v-if="badge.type === 'good'" width="12" height="14" viewBox="0 0 12 14">
      <circle cx="6" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="1.3" />
      <line x1="6" y1="0.5" x2="6" y2="2.5" stroke="currentColor" stroke-width="1.3" />
      <line x1="6" y1="11.5" x2="6" y2="13.5" stroke="currentColor" stroke-width="1.3" />
      <line x1="-0.5" y1="7" x2="1.5" y2="7" stroke="currentColor" stroke-width="1.3" />
      <line x1="10.5" y1="7" x2="12.5" y2="7" stroke="currentColor" stroke-width="1.3" />
    </svg>
    <svg v-else-if="badge.type === 'muted'" width="12" height="12" viewBox="0 0 12 12">
      <circle cx="6" cy="6" r="5" fill="none" stroke="currentColor" stroke-width="1.3" />
      <path d="M4.5 4.8 a1.5 1.5 0 1 1 2.2 1.3 c-0.5 0.3 -0.7 0.6 -0.7 1.1" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
      <circle cx="6" cy="9" r="0.7" fill="currentColor" />
    </svg>
    <svg v-else width="12" height="12" viewBox="0 0 12 12">
      <line x1="1" y1="3" x2="11" y2="3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      <line x1="1" y1="7" x2="8" y2="7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      <line x1="1" y1="11" x2="10" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    </svg>
    {{ badge.label }}
  </span>
</template>

<script setup>
defineProps({ badge: { type: Object, required: true } })
</script>
