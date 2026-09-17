<template>
  <div class="phone" :class="{ dark: isDark }">
    <LoginGate v-if="!authed" @authenticated="signIn" />
    <template v-else>
      <router-view v-slot="{ Component, route }">
        <transition :name="transitionName" mode="out-in">
          <div :key="route.name" class="screen" :inert="showOnboarding">
            <component :is="Component" />
          </div>
        </transition>
      </router-view>
      <TabShell v-if="showTabBar" :tab="currentTab" :inert="showOnboarding" />
      <!-- Sits on top of the first screen and dims it; the app stays visible behind. -->
      <OnboardingModal v-if="showOnboarding" @done="finishOnboarding" />
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LoginGate from './components/LoginGate.vue'
import OnboardingModal from './components/OnboardingModal.vue'
import TabShell from './components/TabShell.vue'

// Local-only admin gate for the pilot demo. Kept for the browser session so a
// refresh does not ask again; closing the tab signs out.
const router = useRouter()

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
  showOnboarding.value = !hasOnboarded()
  // Always land on Start after the gate; the walkthrough sits on top of it.
  router.replace('/')
  try {
    sessionStorage.setItem(AUTH_KEY, '1')
  } catch {
    /* storage unavailable; stay signed in for this render */
  }
}

// First-run walkthrough. Shown once per device after a fresh sign-in, so a
// returning user (or a reload mid-session) goes straight to the app.
const ONBOARDED_KEY = 'at-onboarded-v1'
const showOnboarding = ref(false)

function hasOnboarded() {
  try {
    return localStorage.getItem(ONBOARDED_KEY) === '1'
  } catch {
    return true // storage blocked: never trap the user in the walkthrough
  }
}

function finishOnboarding(reason) {
  showOnboarding.value = false
  try {
    localStorage.setItem(ONBOARDED_KEY, '1')
  } catch {
    /* storage unavailable; fine for this session */
  }
  // The last slide's button is "Choose where you are starting": go straight
  // into the setup form. Skip just reveals Start underneath.
  if (reason === 'setup') router.push('/location')
}

const ORDER = ['location', 'time', 'results', 'detail']
const transitionName = ref('slide-left')

const currentTab = computed(() => router.currentRoute.value.meta.tab ?? '')
const isDark = computed(() => !!router.currentRoute.value.meta.dark)
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
