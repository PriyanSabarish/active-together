<template>
  <div class="kid-layer" role="dialog" aria-label="Your kid">
    <div class="scrim" @click="emit('close')" />
    <div class="sheet">
      <div class="head">
        <span class="avatar">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#1E2A1F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="KID_ICON" /></svg>
          <span class="avatar-band">{{ label(band) }}</span>
        </span>
        <span class="head-text">
          <span class="title">Your kid</span>
          <span class="sub">Missions get pitched to this</span>
        </span>
        <button class="close" aria-label="Close" @click="emit('close')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12 M18 6 6 18" /></svg>
        </button>
      </div>

      <div class="group">
        <div class="group-head"><span>Age</span><span class="muted">{{ label(band) }} yrs</span></div>
        <div class="ages" role="radiogroup" aria-label="Age band">
          <button v-for="b in AGE_BANDS" :key="b.id" class="age" :class="{ on: band === b.id }" role="radio" :aria-checked="band === b.id" @click="band = b.id">
            {{ label(b.id) }}
          </button>
        </div>
      </div>

      <div class="group">
        <div class="group-head"><span>Likes</span><span class="muted">{{ summary }}</span></div>
        <div class="like-list">
          <div v-for="(meta, key) in CATEGORY_META" :key="key" class="like" :class="draft[key]">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(key)" /></svg>
            <span class="like-name">{{ meta.label }}</span>
            <span class="tri" role="radiogroup" :aria-label="meta.label">
              <button
                v-for="o in PREF_LEVELS"
                :key="o.id"
                type="button"
                class="tri-btn"
                :class="[o.id, { on: draft[key] === o.id }]"
                role="radio"
                :aria-checked="draft[key] === o.id"
                :aria-label="o.label"
                :title="o.label"
                @click="draft[key] = o.id"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path :d="ICON[o.id]" /></svg>
              </button>
            </span>
          </div>
        </div>
        <p class="note">"Not for me" places and missions are left out of suggestions.</p>
      </div>

      <div class="actions">
        <button class="clear" @click="clearAll">Clear</button>
        <button class="save" @click="save">Save</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// "Your kid" sheet from the Start page: age band and, per place category,
// Likes / No preference / Not for me — the same preferences as You → Likes.
// Edits a draft; Save writes it to the preferences store (and so to the
// device and the next search), closing discards it.

import { computed, reactive, ref } from 'vue'
import { usePreferencesStore, AGE_BANDS, PREF_LEVELS, levelOf } from '../preferencesStore'
import { CATEGORY_META } from '../store'
import { categoryIcon, THUMB_UP, THUMB_DOWN } from '../taskIcons'

const emit = defineEmits(['close'])
const prefs = usePreferencesStore()

const KID_ICON = 'M12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M12 7v7 M8 10h8 M12 14l-3 6 M12 14l3 6'
const ICON = { likes: THUMB_UP, neutral: 'M6 12h12', nope: THUMB_DOWN }
const band = ref(prefs.ageBand)
const draft = reactive(Object.fromEntries(Object.keys(CATEGORY_META).map((k) => [k, levelOf(prefs.affinities[k])])))

const label = (id) => id.replace('-', '–')
const summary = computed(() => {
  const v = Object.values(draft)
  const likes = v.filter((x) => x === 'likes').length
  const nope = v.filter((x) => x === 'nope').length
  return [likes && `${likes} liked`, nope && `${nope} not for me`].filter(Boolean).join(' · ') || 'None set'
})

function clearAll() {
  for (const k of Object.keys(draft)) draft[k] = 'neutral'
}

function save() {
  prefs.setAgeBand(band.value)
  for (const [k, level] of Object.entries(draft)) prefs.setLevel(k, level)
  emit('close')
}
</script>

<style scoped>
.kid-layer { position: absolute; inset: 0; z-index: 30; }

.scrim {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px) saturate(1.2);
  -webkit-backdrop-filter: blur(10px) saturate(1.2);
}

.sheet {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  border-radius: 34px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(60px) saturate(1.5);
  -webkit-backdrop-filter: blur(60px) saturate(1.5);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.6), 0 30px 60px -20px rgba(30, 42, 31, 0.5);
  padding: 22px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: rise 0.22s ease both;
}

@keyframes rise { from { transform: translateY(24px); opacity: 0; } to { transform: none; opacity: 1; } }

.head { display: flex; align-items: center; gap: 14px; }

.avatar { position: relative; flex: none; width: 64px; height: 64px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; }
.avatar-band { position: absolute; right: -6px; bottom: -2px; padding: 3px 8px; border-radius: 999px; background: var(--green); color: #FFFFFF; font-size: 11.5px; font-weight: 700; box-shadow: 0 0 0 3px #FFFFFF; }

.head-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.title { font-family: var(--font-display); font-weight: 700; font-size: 22px; letter-spacing: -0.4px; }
.sub { font-size: 13px; color: #56625A; }

.close { width: 34px; height: 34px; border: none; border-radius: 50%; background: rgba(30, 42, 31, 0.07); color: var(--ink); display: flex; align-items: center; justify-content: center; cursor: pointer; }

.group { display: flex; flex-direction: column; gap: 10px; }
.group-head { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; }
.muted { font-size: 12.5px; font-weight: 600; color: #56625A; }

.ages { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; padding: 4px; border-radius: 999px; background: #EDF2EA; }
.age { height: 40px; border: none; border-radius: 999px; background: transparent; color: #3A5240; font-family: inherit; font-size: 14.5px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; }
.age.on { background: var(--green); color: #FFFFFF; box-shadow: 0 4px 10px rgba(47, 107, 54, 0.3); }

.like-list { display: flex; flex-direction: column; gap: 6px; max-height: 300px; overflow-y: auto; }
.like { display: flex; align-items: center; gap: 12px; min-height: 44px; padding: 0 6px 0 12px; border-radius: 14px; transition: background 0.16s ease; }
.like.likes { background: rgba(47, 107, 54, 0.08); }
.like.nope { background: rgba(196, 118, 30, 0.08); }
.like-name { flex: 1; min-width: 0; font-size: 14px; font-weight: 600; color: var(--ink); }
.tri { display: inline-flex; gap: 2px; padding: 2px; border-radius: 11px; background: rgba(30, 42, 31, 0.055); }
.tri-btn { width: 34px; height: 30px; border: none; border-radius: 9px; background: transparent; color: rgba(30, 42, 31, 0.38); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.16s ease; }
.tri-btn.on { color: #FFFFFF; }
.tri-btn.on.likes { background: var(--green); }
.tri-btn.on.neutral { background: #8D9689; }
.tri-btn.on.nope { background: #C4761E; }
.note { font-size: 12px; color: #56625A; }

.actions { display: flex; gap: 8px; }
.clear { flex: none; padding: 0 18px; height: 54px; border: none; border-radius: 999px; background: transparent; box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.18); font-family: inherit; font-size: 15px; font-weight: 600; color: var(--ink); cursor: pointer; }
.save { flex: 1; height: 54px; border: none; border-radius: 999px; background: var(--ink); color: var(--paper); font-family: inherit; font-size: 16px; font-weight: 700; cursor: pointer; }
.save:active { transform: scale(0.985); }
</style>
