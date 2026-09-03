<template>
  <div class="phone">
    <LoginGate v-if="!authed" @authenticated="signIn" />
    <router-view v-else v-slot="{ Component, route }">
      <transition :name="transitionName" mode="out-in">
        <div :key="route.name" class="screen">
          <component :is="Component" />
        </div>
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import LoginGate from './components/LoginGate.vue'

// Local-only admin gate for the pilot demo. Kept for the browser session so a
// refresh does not ask again; closing the tab signs out.
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
  try {
    sessionStorage.setItem(AUTH_KEY, '1')
  } catch {
    /* storage unavailable; stay signed in for this render */
  }
}

const ORDER = ['location', 'time', 'results', 'detail']
const router = useRouter()
const transitionName = ref('slide-left')

watch(
  () => router.currentRoute.value,
  (to, from) => {
    if (!from?.name) return
    transitionName.value =
      ORDER.indexOf(to.name) >= ORDER.indexOf(from.name) ? 'slide-left' : 'slide-right'
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
