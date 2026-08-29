<template>
  <!-- Distinct, unambiguous icon per category: canopy+trunk = park,
       circle with seam = sporting ground, zigzag = trail -->
  <span class="cat-icon" :aria-label="category">
    <svg width="32" height="32" viewBox="0 0 32 32">
      <template v-if="category === 'park'">
        <circle cx="16" cy="13" r="7" fill="none" stroke="#444441" stroke-width="1.8" />
        <line x1="16" y1="20" x2="16" y2="26" stroke="#444441" stroke-width="1.8" stroke-linecap="round" />
      </template>
      <template v-else-if="category === 'ground'">
        <circle cx="16" cy="16" r="7" fill="none" stroke="#444441" stroke-width="1.8" />
        <path d="M10 11 Q16 16 10 21 M22 11 Q16 16 22 21" fill="none" stroke="#444441" stroke-width="1.3" />
      </template>
      <template v-else>
        <path d="M8 20 L13 10 L16.5 16 L20 8 L24 18" fill="none" stroke="#444441" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
      </template>
    </svg>
  </span>
</template>

<script setup>
defineProps({ category: { type: String, required: true } })
</script>

<style scoped>
.cat-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--paper);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
