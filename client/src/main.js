import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles.css'

const app = createApp(App).use(createPinia()).use(router)

// Mount after the router resolves the first route, otherwise the initial
// render has no route name and triggers a spurious leave transition.
router.isReady().then(() => app.mount('#app'))
