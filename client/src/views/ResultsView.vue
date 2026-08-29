<template>
  <AppHeader :step="3" back />

  <h1>Your top options</h1>
  <p class="subtitle">Candidate places from open data.</p>
  <p class="hint">Icon shape = category, badge colour = conditions</p>

  <!-- loading -->
  <template v-if="store.loading">
    <div v-for="i in 3" :key="i" class="skeleton-card">
      <div class="sk-row">
        <span class="sk-circle" />
        <span class="sk-lines"><span class="sk-line w60" /><span class="sk-line w40" /></span>
        <span class="sk-pill" />
      </div>
      <span class="sk-line w80" style="margin-top: 18px" />
    </div>
    <p class="loading-note">Checking places and today's forecast…</p>
  </template>

  <!-- zero results -->
  <template v-else-if="store.results.length === 0">
    <div class="empty-state">
      <svg width="44" height="44" viewBox="0 0 44 44">
        <circle cx="20" cy="20" r="12" fill="none" stroke="#B4B2A9" stroke-width="2.5" />
        <line x1="29" y1="29" x2="38" y2="38" stroke="#B4B2A9" stroke-width="2.5" stroke-linecap="round" />
      </svg>
      <p class="empty-title">Nothing within {{ store.radiusKm }} km</p>
      <p class="empty-text">
        We couldn't find activity places within {{ store.radiusKm }} km of
        {{ store.locationLabel }}. Try a wider search radius.
      </p>
      <button v-if="store.radiusKm < 10" class="btn btn-primary widen-btn" @click="widen">
        Search {{ nextRadius }} km instead
      </button>
    </div>
  </template>

  <!-- results -->
  <template v-else>
    <article
      v-for="place in store.results"
      :key="place.id"
      class="result-card"
      role="button"
      tabindex="0"
      @click="open(place)"
      @keydown.enter="open(place)"
    >
      <div class="card-top">
        <CategoryIcon :category="place.category" />
        <div class="card-title">
          <p class="place-name">{{ place.name }}</p>
          <p class="place-meta">{{ place.categoryLabel }} · {{ place.distanceKm }} km</p>
        </div>
        <ConditionBadge :badge="place.badge" />
      </div>
      <hr class="card-divider" />
      <p class="reason">{{ place.reason }}</p>
      <p class="duration-line">
        <svg width="15" height="15" viewBox="0 0 15 15">
          <circle cx="7.5" cy="7.5" r="6.5" fill="none" stroke="#888780" stroke-width="1.3" />
          <line x1="7.5" y1="7.5" x2="7.5" y2="3.5" stroke="#888780" stroke-width="1.3" />
          <line x1="7.5" y1="7.5" x2="10.5" y2="9.5" stroke="#888780" stroke-width="1.3" />
        </svg>
        {{ store.planMin }} min on-site · excludes travel
      </p>
    </article>

    <p v-if="store.results.length === 1" class="footnote">
      Only one place within {{ store.radiusKm }} km of {{ store.locationLabel }}.
      <template v-if="store.radiusKm < 10">Widen the radius to see more options.</template>
    </p>
    <p v-else-if="store.results.length === 2" class="footnote">
      Only two places within {{ store.radiusKm }} km of {{ store.locationLabel }}.
    </p>
  </template>

  <hr class="divider" style="margin-top: auto" />
  <button class="btn btn-secondary" style="width: 100%" @click="$router.back()">Back</button>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CategoryIcon from '../components/CategoryIcon.vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import { useSearchStore } from '../store'

const store = useSearchStore()
const router = useRouter()

// Landing here directly (e.g. page refresh) still shows data.
if (!store.loading && store.results.length === 0) store.fetchRecommendations()

const nextRadius = computed(() => (store.radiusKm === 3 ? 5 : 10))

function widen() {
  store.radiusKm = nextRadius.value
  store.fetchRecommendations()
}

function open(place) {
  router.push(`/place/${place.id}`)
}
</script>

<style scoped>
.hint {
  font-size: 10px;
  color: var(--ink-5);
  margin-top: 4px;
}

.result-card {
  margin-top: 14px;
  border: 1px solid var(--line-2);
  border-radius: 14px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.12s ease, transform 0.12s ease;
}

.result-card:hover { border-color: var(--line-3); }
.result-card:active { transform: scale(0.985); }

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title { flex: 1; min-width: 0; }

.place-name {
  font-size: 14.5px;
  font-weight: 500;
}

.place-meta {
  font-size: 11.5px;
  color: var(--ink-3);
  margin-top: 3px;
}

.card-divider {
  border: none;
  border-top: 1px solid var(--line);
  margin: 14px -16px;
}

.reason {
  font-size: 12px;
  color: var(--ink-2);
}

.duration-line {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--ink-4);
}

.footnote {
  text-align: center;
  font-size: 10.5px;
  color: var(--ink-4);
  margin-top: 20px;
  line-height: 1.5;
}

/* skeleton */
.skeleton-card {
  margin-top: 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px;
}

.sk-row { display: flex; align-items: center; gap: 12px; }

.sk-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--paper);
  animation: pulse 1.2s ease-in-out infinite;
}

.sk-lines { flex: 1; display: flex; flex-direction: column; gap: 7px; }

.sk-line {
  display: block;
  height: 10px;
  border-radius: 5px;
  background: var(--paper);
  animation: pulse 1.2s ease-in-out infinite;
}

.w60 { width: 60%; }
.w40 { width: 40%; }
.w80 { width: 80%; }

.sk-pill {
  width: 64px;
  height: 22px;
  border-radius: 11px;
  background: var(--paper);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}

.loading-note {
  text-align: center;
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 18px;
}

/* empty */
.empty-state {
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 24px;
}

.empty-title {
  font-size: 15px;
  font-weight: 500;
  margin-top: 16px;
}

.empty-text {
  font-size: 12px;
  color: var(--ink-3);
  line-height: 1.5;
  margin-top: 8px;
}

.widen-btn {
  margin-top: 20px;
  padding: 0 22px;
  height: 44px;
}
</style>
