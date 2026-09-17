<template>
  <nav class="tab-bar" aria-label="Primary">
    <RouterLink to="/" class="tab-item" :class="{ active: tab === 'start' }">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><path d="M12 10.5v.01" />
      </svg>
      <span class="tab-label">Start</span>
    </RouterLink>

    <RouterLink to="/play" class="tab-item" :class="{ active: tab === 'play' }">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M13 3.5 6.2 12.6a.6.6 0 0 0 .48.96h4.6l-1.28 7.04 6.8-9.1a.6.6 0 0 0-.48-.96h-4.6L13 3.5Z" />
      </svg>
      <span class="tab-label">Play</span>
    </RouterLink>

    <RouterLink to="/week" class="tab-item" :class="{ active: tab === 'week' }">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 6.5h16v13.5H4V6.5Z" /><path d="M4 10.5h16" /><path d="M8.5 3.5v4" /><path d="M15.5 3.5v4" /><path d="M8.5 14.5h3" />
      </svg>
      <span class="tab-label">Week</span>
    </RouterLink>

    <RouterLink to="/you" class="tab-item" :class="{ active: tab === 'you' }">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 11.5a3.75 3.75 0 1 0 0-7.5 3.75 3.75 0 0 0 0 7.5Z" /><path d="M4.5 20.5c.9-3.9 3.8-6 7.5-6s6.6 2.1 7.5 6" />
      </svg>
      <span class="tab-label">You</span>
    </RouterLink>
  </nav>
</template>

<script setup>
// Bottom tab bar: Start / Play / Week / You. Purely presentational; App.vue
// passes the active tab key from route.meta.tab.

defineProps({
  // Active tab key, from route.meta.tab: 'start' | 'play' | 'week' | 'you'
  tab: { type: String, default: '' }
})
</script>
