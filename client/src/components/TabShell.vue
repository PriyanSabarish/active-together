<template>
  <nav class="tab-bar" aria-label="Primary">
    <RouterLink to="/today" class="tab-item" :class="{ active: tab === 'today' }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 9.5 L10 3 L17 9.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        <path d="M5 8.5 V16.5 H15 V8.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <span class="tab-label">Today</span>
    </RouterLink>

    <RouterLink to="/" class="tab-item" :class="{ active: tab === 'discover' }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.6" />
        <line x1="12.7" y1="12.7" x2="17" y2="17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
      <span class="tab-label">Discover</span>
    </RouterLink>

    <RouterLink to="/plan" class="tab-item" :class="{ active: tab === 'plan' }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <rect x="4" y="4" width="12" height="14" rx="2" stroke="currentColor" stroke-width="1.6" />
        <rect x="7" y="3" width="6" height="2.4" rx="1" fill="currentColor" />
        <line x1="6.5" y1="9.5" x2="13.5" y2="9.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
        <line x1="6.5" y1="13" x2="13.5" y2="13" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
      </svg>
      <span class="tab-label">Plan</span>
    </RouterLink>

    <RouterLink to="/insights" class="tab-item" :class="{ active: tab === 'insights' }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <line x1="4" y1="17" x2="16" y2="17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        <rect x="5" y="11" width="3" height="6" rx="0.8" fill="currentColor" />
        <rect x="9.5" y="7" width="3" height="10" rx="0.8" fill="currentColor" />
        <rect x="14" y="3" width="3" height="14" rx="0.8" fill="currentColor" />
      </svg>
      <span class="tab-label">Insights</span>
    </RouterLink>

    <RouterLink to="/prefs" class="tab-item" :class="{ active: tab === 'prefs' }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <line x1="4" y1="4" x2="4" y2="16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        <line x1="10" y1="4" x2="10" y2="16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        <line x1="16" y1="4" x2="16" y2="16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        <circle cx="4" cy="7" r="1.6" fill="currentColor" />
        <circle cx="10" cy="13" r="1.6" fill="currentColor" />
        <circle cx="16" cy="9" r="1.6" fill="currentColor" />
      </svg>
      <span class="tab-label">Prefs</span>
    </RouterLink>
  </nav>
</template>

<script setup>
defineProps({
  // Active tab key, from route.meta.tab: 'today' | 'discover' | 'plan' | 'insights' | 'prefs'
  tab: { type: String, default: '' }
})
</script>
