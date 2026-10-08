<script setup>
defineProps({ confidence: { type: String, required: true } })
const styles = {
  VERIFIED: 'bg-indigo-600 text-white',
  HIGH: 'bg-slate-900 text-white',
  MEDIUM: 'bg-slate-200 text-slate-800',
  LOW: 'bg-white text-slate-600 border border-dashed border-slate-400',
}
</script>

<template>
  <span class="inline-flex rounded-md px-2 py-0.5 text-xs font-semibold tracking-wide" :class="styles[confidence]">
    {{ confidence === 'VERIFIED' ? 'Verified by file metadata' : `${confidence} confidence` }}
  </span>
</template>
