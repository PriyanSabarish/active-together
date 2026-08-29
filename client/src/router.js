import { createRouter, createWebHistory } from 'vue-router'
import LocationView from './views/LocationView.vue'
import TimeView from './views/TimeView.vue'
import ResultsView from './views/ResultsView.vue'
import DetailView from './views/DetailView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'location', component: LocationView },
    { path: '/time', name: 'time', component: TimeView },
    { path: '/results', name: 'results', component: ResultsView },
    { path: '/place/:id', name: 'detail', component: DetailView, props: true }
  ]
})
