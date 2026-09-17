import { createRouter, createWebHistory } from 'vue-router'
import StartView from './views/StartView.vue'
import LocationView from './views/LocationView.vue'
import TimeView from './views/TimeView.vue'
import ResultsView from './views/ResultsView.vue'
import DetailView from './views/DetailView.vue'
import PlayView from './views/PlayView.vue'
import MissionPreviewView from './views/MissionPreviewView.vue'
import PickMissionView from './views/PickMissionView.vue'
import MissionRunView from './views/MissionRunView.vue'
import MissionOverviewView from './views/MissionOverviewView.vue'
import MissionFinishedView from './views/MissionFinishedView.vue'
import WeekView from './views/WeekView.vue'
import DayDetailView from './views/DayDetailView.vue'
import YouView from './views/YouView.vue'
import AgeBandView from './views/AgeBandView.vue'

// Four tabs, as in the prototype: Start (where/how far/how long → places),
// Play (today's mission and everything while it runs), Week (what happened,
// device-local), You (preferences, device-local). meta.tab picks the active
// tab in TabShell; meta.dark switches the shell to the dark mission screen.
export default createRouter({
  history: createWebHistory(),
  routes: [
    // Start
    { path: '/', name: 'start', component: StartView, meta: { tab: 'start' } },
    { path: '/location', name: 'location', component: LocationView, meta: { tab: 'start' } },
    { path: '/time', name: 'time', component: TimeView, meta: { tab: 'start' } },
    { path: '/results', name: 'results', component: ResultsView, meta: { tab: 'start' } },
    { path: '/place/:id', name: 'detail', component: DetailView, props: true, meta: { tab: 'start' } },
    // Play
    { path: '/play', name: 'play', component: PlayView, meta: { tab: 'play' } },
    { path: '/play/preview', name: 'mission-preview', component: MissionPreviewView, meta: { tab: 'play' } },
    { path: '/play/pick', name: 'pick-mission', component: PickMissionView, meta: { tab: 'play' } },
    { path: '/play/run', name: 'mission-run', component: MissionRunView, meta: { tab: 'play', dark: true } },
    { path: '/play/overview', name: 'mission-overview', component: MissionOverviewView, meta: { tab: 'play' } },
    { path: '/play/finished', name: 'mission-finished', component: MissionFinishedView, meta: { tab: 'play' } },
    // Week
    { path: '/week', name: 'week', component: WeekView, meta: { tab: 'week' } },
    { path: '/week/:date', name: 'day-detail', component: DayDetailView, props: true, meta: { tab: 'week' } },
    // You
    { path: '/you', name: 'you', component: YouView, meta: { tab: 'you' } },
    { path: '/you/age-band', name: 'age-band', component: AgeBandView, meta: { tab: 'you' } },
    // Old five-tab paths, kept so bookmarks and the onboarding flag still land somewhere.
    { path: '/today', redirect: '/play' },
    { path: '/plan', redirect: '/play/preview' },
    { path: '/plan/:rest(.*)', redirect: (to) => `/play/${to.params.rest}` },
    { path: '/insights', redirect: '/week' },
    { path: '/insights/:date', redirect: (to) => `/week/${to.params.date}` },
    { path: '/prefs', redirect: '/you' },
    { path: '/prefs/age-band', redirect: '/you/age-band' }
  ]
})
