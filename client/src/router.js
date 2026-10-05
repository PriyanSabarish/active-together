import { createRouter, createWebHistory } from 'vue-router'
import LocationView from './views/LocationView.vue'
import ResultsView from './views/ResultsView.vue'
import DetailView from './views/DetailView.vue'
import MissionRunView from './views/MissionRunView.vue'
import MissionFinishedView from './views/MissionFinishedView.vue'
import WeekView from './views/WeekView.vue'
import EntryView from './views/EntryView.vue'
import YouView from './views/YouView.vue'
import YouOutingsView from './views/YouOutingsView.vue'
import YouLikesView from './views/YouLikesView.vue'
import YouAboutView from './views/YouAboutView.vue'

// Four tabs, as in the prototype:
//   Start — where you are, how far, how long (one screen)
//   Play  — your top options → a place → pick a mission → run it → finished
//   Week  — the activity diary and each outing, device-local
//   You   — age band, outings and photos, likes, about; device-local
// meta.tab picks the active tab in TabShell; meta.dark switches the shell to
// the dark mission-run look.
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: LocationView, meta: { tab: 'start' } },
    { path: '/play', name: 'play', component: ResultsView, meta: { tab: 'play' } },
    { path: '/play/place/:id', name: 'detail', component: DetailView, props: true, meta: { tab: 'play' } },
    { path: '/play/run', name: 'mission-run', component: MissionRunView, meta: { tab: 'play', dark: true } },
    { path: '/play/finished', name: 'mission-finished', component: MissionFinishedView, meta: { tab: 'play' } },
    { path: '/week', name: 'week', component: WeekView, meta: { tab: 'week' } },
    { path: '/week/entry/:id', name: 'entry', component: EntryView, props: true, meta: { tab: 'week' } },
    { path: '/you', name: 'you', component: YouView, meta: { tab: 'you' } },
    { path: '/you/outings', name: 'you-outings', component: YouOutingsView, meta: { tab: 'you' } },
    { path: '/you/likes', name: 'you-likes', component: YouLikesView, meta: { tab: 'you' } },
    { path: '/you/about', name: 'you-about', component: YouAboutView, meta: { tab: 'you' } },
    // Earlier paths, kept so bookmarks still land somewhere sensible.
    { path: '/week/:date', redirect: '/week' },
    { path: '/you/age-band', redirect: '/you' },
    { path: '/location', redirect: '/' },
    { path: '/time', redirect: '/' },
    { path: '/results', redirect: '/play' },
    { path: '/place/:id', redirect: (to) => `/play/place/${to.params.id}` },
    { path: '/play/preview', redirect: '/play' },
    { path: '/play/pick', redirect: '/play' },
    { path: '/play/overview', redirect: '/play/run' },
    { path: '/today', redirect: '/play' },
    { path: '/plan', redirect: '/play' },
    { path: '/plan/:rest(.*)', redirect: (to) => `/play/${to.params.rest}` },
    { path: '/insights', redirect: '/week' },
    { path: '/insights/:date', redirect: '/week' },
    { path: '/prefs', redirect: '/you' },
    { path: '/prefs/age-band', redirect: '/you' }
  ]
})
