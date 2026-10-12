<template>
  <div class="scrim" @click="$emit('close')">
    <div class="sheet" role="dialog" aria-label="Parent guide" @click.stop>
      <div class="sheet-top">
        <span class="grabber" />
        <div class="top-row">
          <h1 class="title">Parent guide</h1>
          <button class="close" @click="$emit('close')">Close</button>
        </div>
      </div>

      <div class="body">
        <section v-if="stage" class="task">
          <div class="task-head">
            <span class="eyebrow">Task {{ stageIndex + 1 }}</span>
            <h2 class="task-title">{{ stage.title }}</h2>
          </div>

          <div v-for="(part, i) in stage.parts" :key="i" class="part">
            <p v-if="part.label" class="part-label">{{ part.label }}</p>

            <div v-if="part.read" class="say">
              <span class="say-label">Say</span>
              <p>“{{ part.read }}”</p>
            </div>

            <ol v-if="part.do?.length" class="steps">
              <li v-for="(d, j) in part.do" :key="j">
                <span class="num">{{ j + 1 }}</span>
                <p>{{ d }}</p>
              </li>
            </ol>

            <div v-if="part.bands?.[ageBand] || part.hint" class="notes">
              <div v-if="part.bands?.[ageBand]" class="note-row">
                <span class="pill">Ages {{ ageBand.replace('-', '–') }}</span>
                <p>{{ part.bands[ageBand] }}</p>
              </div>
              <span v-if="part.bands?.[ageBand] && part.hint" class="rule" />
              <div v-if="part.hint" class="note-row">
                <svg class="note-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E8913A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6 M10 21h4 M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3Z" /></svg>
                <p><b>If they’re stuck:</b> {{ lowerFirst(part.hint) }}</p>
              </div>
            </div>
          </div>

          <div v-if="stage.closing && isLastStep" class="say">
            <span class="say-label">Say to finish</span>
            <p>“{{ stage.closing }}”</p>
          </div>
        </section>
        <p v-else class="empty">There is no guide for this task. Follow the steps on screen.</p>

        <div class="accordions">
          <div class="acc">
            <button class="acc-head" :aria-expanded="setupOpen" @click="setupOpen = !setupOpen">
              <span class="acc-text">
                <span class="acc-title">Before you start</span>
                <span class="acc-sub">Setup and opening line · {{ guide.setupTime }}</span>
              </span>
              <svg class="chev" :class="{ up: setupOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
            </button>
            <div v-if="setupOpen" class="acc-body">
              <div class="say">
                <span class="say-label">Say first</span>
                <p>“{{ guide.opening }}”</p>
              </div>
              <div class="group">
                <span class="group-label">You’ll need</span>
                <div class="chips">
                  <span v-for="k in guide.kit" :key="k" class="chip">{{ k }}</span>
                </div>
              </div>
              <div class="group">
                <span class="group-label">Set up</span>
                <ol class="steps">
                  <li v-for="(t, i) in guide.setup" :key="i">
                    <span class="num">{{ i + 1 }}</span>
                    <p>{{ t }}</p>
                  </li>
                </ol>
              </div>
            </div>
          </div>

          <div class="acc">
            <button class="acc-head" :aria-expanded="safetyOpen" @click="safetyOpen = !safetyOpen">
              <svg class="shield" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E8913A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3Z" /></svg>
              <span class="acc-title grow">Safety rules</span>
              <svg class="chev" :class="{ up: safetyOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
            </button>
            <div v-if="safetyOpen" class="acc-body tight">
              <div v-for="(r, i) in SHARED_RULES" :key="i" class="bullet">
                <span class="dot" />
                <p>{{ r }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { SHARED_RULES } from '../parentGuides'

// Setup, rules, clue answers and what to say for the at-home activities
// (story 9.2). Opened from the run screen; one task of the guide per step.
// Layout follows "Parent Guide Sheet.html" in the iteration 3 designs.
const props = defineProps({
  guide: { type: Object, required: true },
  stageIndex: { type: Number, default: 0 },
  ageBand: { type: String, default: '8-10' },
  isLastStep: { type: Boolean, default: false }
})
defineEmits(['close'])

const stage = computed(() => props.guide.stages[props.stageIndex] ?? null)
// Setup is open on the first task so it is read before play starts.
const setupOpen = ref(props.stageIndex === 0)
const safetyOpen = ref(false)

const lowerFirst = (t) => (t ? t.charAt(0).toLowerCase() + t.slice(1) : t)
</script>

<style scoped>
.scrim {
  position: absolute;
  inset: 0;
  z-index: 9;
  background: rgba(10, 14, 11, 0.62);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.sheet {
  max-height: 92%;
  overflow: auto;
  scrollbar-width: none;
  background: #233027;
  border-radius: 28px 28px 0 0;
  color: #F2F1EC;
  box-shadow: 0 -1px 0 rgba(242, 241, 236, 0.06);
}
.sheet::-webkit-scrollbar { display: none; }

.sheet-top {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #233027;
  padding: 10px 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.grabber { align-self: center; width: 36px; height: 4px; border-radius: 999px; background: rgba(242, 241, 236, 0.22); }
.top-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.title { margin: 0; font-family: var(--font-display); font-weight: 700; font-size: 24px; letter-spacing: -0.4px; }
.close {
  height: 36px;
  padding: 0 14px;
  border: none;
  border-radius: 999px;
  background: rgba(242, 241, 236, 0.08);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  color: #F2F1EC;
  cursor: pointer;
}

.body { padding: 4px 20px 28px; display: flex; flex-direction: column; gap: 22px; }

.task { display: flex; flex-direction: column; gap: 14px; }
.task-head { display: flex; flex-direction: column; gap: 4px; }
.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #E8913A; }
.task-title { margin: 0; font-family: var(--font-display); font-weight: 700; font-size: 22px; letter-spacing: -0.3px; line-height: 1.15; }

.part { display: flex; flex-direction: column; gap: 14px; }
.part + .part { padding-top: 6px; }
.part-label { font-weight: 700; font-size: 15px; color: rgba(242, 241, 236, 0.75); }

.say { display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; border-radius: 18px; background: rgba(232, 145, 58, 0.1); }
.say-label { font-size: 11.5px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #E8913A; }
.say p { margin: 0; font-size: 15.5px; line-height: 1.45; text-wrap: pretty; }

.steps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.steps li { display: flex; gap: 12px; align-items: flex-start; }
.num {
  flex: none;
  width: 22px;
  height: 22px;
  margin-top: 1px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(242, 241, 236, 0.1);
  font-size: 12px;
  font-weight: 700;
}
.steps p { margin: 0; flex: 1; font-size: 15px; line-height: 1.45; color: rgba(242, 241, 236, 0.86); text-wrap: pretty; }

.notes { display: flex; flex-direction: column; border-radius: 18px; background: rgba(242, 241, 236, 0.05); }
.note-row { display: flex; gap: 12px; align-items: flex-start; padding: 13px 16px; }
.note-row p { margin: 0; flex: 1; font-size: 14.5px; line-height: 1.45; color: rgba(242, 241, 236, 0.86); }
.note-row b { font-weight: 700; color: #F2F1EC; }
.note-icon { flex: none; margin-top: 2px; }
.pill { flex: none; margin-top: 1px; padding: 3px 9px; border-radius: 999px; background: #E8913A; color: #1E2A1F; font-size: 12px; font-weight: 700; white-space: nowrap; }
.rule { height: 1px; margin: 0 16px; background: rgba(242, 241, 236, 0.07); }

.accordions { display: flex; flex-direction: column; gap: 8px; }
.acc { border-radius: 18px; background: rgba(242, 241, 236, 0.05); overflow: hidden; }
.acc-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 0 16px;
  border: none;
  background: none;
  font-family: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
}
.acc-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; padding: 8px 0; }
.acc-title { font-size: 15.5px; font-weight: 700; }
.acc-title.grow { flex: 1; }
.acc-sub { font-size: 13px; color: rgba(242, 241, 236, 0.55); }
.chev { flex: none; color: rgba(242, 241, 236, 0.7); transition: transform 0.2s ease; }
.chev.up { transform: rotate(180deg); }
.shield { flex: none; }

.acc-body { padding: 2px 16px 18px; display: flex; flex-direction: column; gap: 18px; }
.acc-body.tight { padding-top: 0; gap: 10px; }
.group { display: flex; flex-direction: column; gap: 10px; }
.group-label { font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: rgba(242, 241, 236, 0.5); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { padding: 7px 12px; border-radius: 999px; background: rgba(242, 241, 236, 0.08); font-size: 13.5px; font-weight: 500; }
.acc-body .steps p { font-size: 14.5px; }

.bullet { display: flex; gap: 12px; align-items: flex-start; }
.dot { flex: none; width: 6px; height: 6px; margin-top: 8px; border-radius: 50%; background: #E8913A; }
.bullet p { margin: 0; flex: 1; font-size: 14.5px; line-height: 1.45; color: rgba(242, 241, 236, 0.86); text-wrap: pretty; }

.empty { color: rgba(242, 241, 236, 0.7); }
</style>
