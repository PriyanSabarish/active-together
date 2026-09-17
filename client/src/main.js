import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { persistSearchState } from './persist'
import { seedDemoData } from './demoSeed'
import './styles.css'

const pinia = createPinia()
pinia.use(persistSearchState)

const app = createApp(App).use(pinia).use(router)

// Insights and Prefs run on device-local demo data until the final iteration.
seedDemoData()

// Mount after the router resolves the first route, otherwise the initial
// render has no route name and triggers a spurious leave transition.
router.isReady().then(() => app.mount('#app'))
