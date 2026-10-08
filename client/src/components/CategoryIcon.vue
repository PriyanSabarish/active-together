<template>
  <!-- Tinted circle per backend category, as in the Canvas cards: green for
       park-like places, orange for grounds and courts. -->
  <span class="cat-icon" :class="tone" :aria-label="categoryLabel(category)">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" :stroke-width="category === 'playground' ? 1.4 : 1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(category)" /></svg>
  </span>
</template>

<script setup>
// Category glyph for a place card. The tone follows CATEGORY_META's shape
// (store.js): park and trail places are green, grounds and courts orange.
// The glyph itself comes from taskIcons (tree, oval, leaf, ...).

import { computed } from 'vue'
import { CATEGORY_META, categoryLabel } from '../store'
import { categoryIcon } from '../taskIcons'

const props = defineProps({ category: { type: String, required: true } })
const tone = computed(() => (CATEGORY_META[props.category]?.shape === 'ground' ? 'warm' : 'green'))
</script>

<style scoped>
.cat-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cat-icon.green { background: rgba(47, 107, 54, 0.12); color: var(--green); }
.cat-icon.warm { background: rgba(232, 145, 58, 0.2); color: var(--amber); }
</style>
