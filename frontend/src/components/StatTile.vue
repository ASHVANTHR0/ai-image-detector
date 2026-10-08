<script setup>
defineProps({ label: String, value: [String, Number], hint: String, loading: Boolean })
</script>

<template>
  <div class="card !p-4">
    <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ label }}</p>
    <div v-if="loading" class="mt-2 h-7 w-16 animate-pulse rounded bg-slate-200" />
    <p v-else class="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{{ value }}</p>
    <p v-if="hint" class="mt-0.5 text-xs text-slate-500">{{ hint }}</p>
  </div>
</template>
