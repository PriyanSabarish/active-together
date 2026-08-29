import { createRouter, createWebHistory } from 'vue-router'
import LocationView from './views/LocationView.vue'
import TimeView from './views/TimeView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'location', component: LocationView },
    { path: '/time', name: 'time', component: TimeView }
  ]
})
