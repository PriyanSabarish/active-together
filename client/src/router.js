import { createRouter, createWebHistory } from 'vue-router'
import LocationView from './views/LocationView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'location', component: LocationView }
  ]
})
