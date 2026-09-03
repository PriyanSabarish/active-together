<template>
  <div class="gate">
    <div class="gate-card" role="dialog" aria-labelledby="gate-title">
      <svg class="gate-logo" width="40" height="50" viewBox="0 0 100 126" aria-hidden="true">
        <path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" fill="#2E8540" />
        <circle cx="50" cy="34" r="12" fill="#F49B1B" />
        <path d="M28 54 Q50 70 72 54" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" />
        <path d="M32 78 Q50 92 68 78" fill="none" stroke="#7CBE7A" stroke-width="10" stroke-linecap="round" />
      </svg>
      <h1 id="gate-title" class="gate-title">Sign in</h1>
      <p class="gate-sub">Active Together is in a private pilot. Enter the admin account to continue.</p>

      <form @submit.prevent="submit">
        <label class="gate-label" for="gate-user">Username</label>
        <input id="gate-user" v-model.trim="username" class="gate-input" type="text" autocomplete="username" autofocus />

        <label class="gate-label" for="gate-pass">Password</label>
        <input id="gate-pass" v-model="password" class="gate-input" type="password" autocomplete="current-password" />

        <p v-if="error" class="gate-error">{{ error }}</p>

        <button class="btn btn-primary gate-btn" type="submit" :disabled="!username || !password">Sign in</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// Local-only gate for the pilot demo. Credentials are checked in the browser;
// this is not real authentication and must not be relied on for security.
const ACCOUNT = { username: 'admin', password: 'admin123' }

const emit = defineEmits(['authenticated'])

const username = ref('')
const password = ref('')
const error = ref('')

function submit() {
  if (username.value === ACCOUNT.username && password.value === ACCOUNT.password) {
    error.value = ''
    emit('authenticated')
  } else {
    error.value = 'Incorrect username or password.'
    password.value = ''
  }
}
</script>

<style scoped>
.gate {
  position: absolute;
  inset: 0;
  background: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 50;
}

.gate-card {
  width: 100%;
  max-width: 360px;
  background: #FFFFFF;
  border: 1px solid var(--line-2);
  border-radius: 16px;
  padding: 28px 24px;
  box-shadow: 0 12px 32px rgba(44, 44, 42, 0.08);
  text-align: center;
}

.gate-logo { margin-bottom: 8px; }

.gate-title {
  font-size: 20px;
  font-weight: 600;
}

.gate-sub {
  font-size: 12px;
  color: var(--ink-3);
  margin: 6px 0 20px;
  line-height: 1.5;
}

.gate-label {
  display: block;
  text-align: left;
  font-size: 11.5px;
  color: var(--ink-4);
  margin: 12px 0 6px;
}

.gate-input {
  width: 100%;
  height: 44px;
  border: 1px solid var(--line-3);
  border-radius: 10px;
  padding: 0 14px;
  font-size: 14px;
  font-family: inherit;
  color: var(--ink);
  outline: none;
}

.gate-input:focus { border-color: var(--green); }

.gate-error {
  margin-top: 12px;
  font-size: 12px;
  color: var(--amber);
}

.gate-btn {
  width: 100%;
  margin-top: 20px;
}

.gate-btn:disabled {
  opacity: 0.45;
  cursor: default;
}
</style>
