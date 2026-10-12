<template>
  <div v-if="full || a2hs" class="notices">
    <p v-if="full" class="notice">
      Photo storage on this phone is nearly full. Nothing is deleted for you. Open an outing and delete photos you no longer want to make room.
    </p>
    <p v-if="a2hs" class="notice">
      On iPhone, tap Share, then Add to Home Screen. Photos are kept more safely when Active Together is installed.
    </p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { needsHomeScreenPrompt, storageIsNearlyFull } from '../storageNotice'

const full = ref(false)
const a2hs = ref(needsHomeScreenPrompt())
onMounted(async () => {
  full.value = await storageIsNearlyFull()
})
</script>

<style scoped>
.notices { margin: 4px 0 12px; display: flex; flex-direction: column; gap: 8px; }
.notice { padding: 10px 12px; border-radius: 12px; background: var(--amber-light); color: var(--amber); font-size: 13px; line-height: 1.4; }
</style>
