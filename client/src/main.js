import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { persistSearchState, persistPreferences } from './persist'
import { seedDemoData } from './demoSeed'
import { useHistoryStore } from './historyStore'
import { usePhotoStore } from './photoStore'
import './styles.css'

const pinia = createPinia()
pinia.use(persistSearchState)
pinia.use(persistPreferences)

const app = createApp(App).use(pinia).use(router)

// Saved outings and photos come back from IndexedDB first (photos whose run
// never became a record are dropped), then the demo week fills an empty
// device. Mount after the router resolves the first route, otherwise the
// initial render has no route name and triggers a spurious leave transition.
async function loadDeviceData() {
  const history = useHistoryStore(pinia)
  const photos = usePhotoStore(pinia)
  try {
    await history.hydrate()
    await photos.hydrate(new Set(history.records.map((r) => r.runId).filter(Boolean)))
  } catch {
    /* device store unavailable: carry on in memory */
  }
  seedDemoData()
}

Promise.all([loadDeviceData(), router.isReady()]).then(() => app.mount('#app'))
