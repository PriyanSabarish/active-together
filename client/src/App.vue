<template>
  <div class="phone" :class="{ dark: isDark, green: isGreen }">
    <LoginGate v-if="!authed" @authenticated="signIn" />
    <template v-else>
      <router-view v-slot="{ Component, route }">
        <transition :name="transitionName" mode="out-in">
          <div :key="route.name" class="screen" :inert="showOnboarding || showCover">
            <component :is="Component" />
          </div>
        </transition>
      </router-view>
      <TabShell v-if="showTabBar" :tab="currentTab" :inert="showOnboarding || showCover" />
      <!-- Short confirmation with an optional Undo (photo deleted, saved). -->
      <div v-if="photoStore.toast" class="toast" role="status">
        <span class="toast-text">{{ photoStore.toast.text }}</span>
        <button v-if="photoStore.toast.undo" class="toast-undo" @click="photoStore.undoToast()">Undo</button>
      </div>
      <!-- After every sign-in: the welcome cover, then the four-slide walkthrough, both over Start. -->
      <LandingCover v-if="showCover" @done="showCover = false" />
      <OnboardingModal v-else-if="showOnboarding" @done="finishOnboarding" />
    </template>
  </div>
</template>

<script setup>
// App shell. Order of layers, bottom to top: the routed screen, the four-tab
// bar, the first-run walkthrough. Two flags gate what shows:
//   - authed (sessionStorage): the private-pilot admin gate, per browser tab
//   - onboarded (localStorage): walkthrough seen once per device
// route.meta.tab picks the active tab; route.meta.dark switches the whole
// shell to the dark mission-run look (background, header, tab bar).

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LoginGate from './components/LoginGate.vue'
import LandingCover from './components/LandingCover.vue'
import OnboardingModal from './components/OnboardingModal.vue'
import TabShell from './components/TabShell.vue'
import { usePhotoStore } from './photoStore'
import { useMissionStore } from './missionStore'

// Local-only admin gate for the pilot demo. Kept for the browser session so a
// refresh does not ask again; closing the tab signs out.
const router = useRouter()
const photoStore = usePhotoStore()

const AUTH_KEY = 'at-admin-authed'
const authed = ref(readAuthed())

function readAuthed() {
  try {
    return sessionStorage.getItem(AUTH_KEY) === '1'
  } catch {
    return false
  }
}

function signIn() {
  authed.value = true
  showOnboarding.value = true
  showCover.value = true
  // Always land on Start after the gate; the walkthrough sits on top of it.
  router.replace('/')
  try {
    sessionStorage.setItem(AUTH_KEY, '1')
  } catch {
    /* storage unavailable; stay signed in for this render */
  }
}

// Welcome cover + walkthrough. Shown after every sign-in; a reload mid-session
// goes straight to the app. The flag below only records that it has been seen.
const ONBOARDED_KEY = 'at-onboarded-v1'
const showOnboarding = ref(false)
const showCover = ref(false) // welcome cover, shown after each sign-in


function finishOnboarding(reason) {
  showOnboarding.value = false
  try {
    localStorage.setItem(ONBOARDED_KEY, '1')
  } catch {
    /* storage unavailable; fine for this session */
  }
  // The last slide's button is "Choose where you are starting": go straight
  // into the setup form. Skip just reveals Start underneath.
  if (reason === 'setup') router.push('/')
}

const ORDER = ['location', 'time', 'results', 'detail']
const transitionName = ref('slide-left')

const currentTab = computed(() => router.currentRoute.value.meta.tab ?? '')
const isDark = computed(() => !!router.currentRoute.value.meta.dark)
// The end-of-mission photo prompt sits on a green shell.
const missionStore = useMissionStore()
const isGreen = computed(() => router.currentRoute.value.name === 'mission-finished' && missionStore.status === 'done' && missionStore.finishPhase === 'capture')
const showTabBar = computed(() => !!currentTab.value && !router.currentRoute.value.meta.hideTabBar)

watch(
  () => router.currentRoute.value,
  (to, from) => {
    if (!from?.name) return
    const toIdx = ORDER.indexOf(to.name)
    const fromIdx = ORDER.indexOf(from.name)
    transitionName.value =
      toIdx === -1 || fromIdx === -1 || toIdx >= fromIdx ? 'slide-left' : 'slide-right'
  }
)
</script>

<style>
.toast {
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 97px;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 52px;
  padding: 0 8px 0 18px;
  border-radius: 16px;
  background: var(--dark);
  box-shadow: 0 10px 26px rgba(30, 42, 31, 0.25);
}

.toast-text { flex: 1; font-size: 14.5px; font-weight: 600; color: var(--paper); }

.toast-undo {
  height: 38px;
  padding: 0 14px;
  border: none;
  border-radius: 11px;
  background: none;
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 700;
  color: var(--accent);
  cursor: pointer;
}

.screen {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.slide-left-enter-from { opacity: 0; transform: translateX(24px); }
.slide-left-leave-to { opacity: 0; transform: translateX(-24px); }
.slide-right-enter-from { opacity: 0; transform: translateX(-24px); }
.slide-right-leave-to { opacity: 0; transform: translateX(24px); }
</style>
