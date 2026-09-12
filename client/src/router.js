import { createRouter, createWebHistory } from 'vue-router'
import LocationView from './views/LocationView.vue'
import TimeView from './views/TimeView.vue'
import ResultsView from './views/ResultsView.vue'
import DetailView from './views/DetailView.vue'
import TodayView from './views/TodayView.vue'
import PlanView from './views/PlanView.vue'
import InsightsView from './views/InsightsView.vue'
import PrefsView from './views/PrefsView.vue'

// meta.tab drives which bottom-tab is highlighted (see TabBar.vue); routes
// without a tab, or with meta.hideTabBar, render without the tab bar.
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'location', component: LocationView, meta: { tab: 'discover', hideTabBar: true } },
    { path: '/time', name: 'time', component: TimeView, meta: { tab: 'discover' } },
    { path: '/results', name: 'results', component: ResultsView, meta: { tab: 'discover' } },
    { path: '/place/:id', name: 'detail', component: DetailView, props: true, meta: { tab: 'discover' } },
    { path: '/today', name: 'today', component: TodayView, meta: { tab: 'today' } },
    { path: '/plan', name: 'plan', component: PlanView, meta: { tab: 'plan' } },
    { path: '/insights', name: 'insights', component: InsightsView, meta: { tab: 'insights' } },
    { path: '/prefs', name: 'prefs', component: PrefsView, meta: { tab: 'prefs' } }
  ]
})
