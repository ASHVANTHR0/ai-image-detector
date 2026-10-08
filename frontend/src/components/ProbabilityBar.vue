<script setup>
import { pct } from '../services/format'

defineProps({ label: String, value: Number, color: String })
</script>

<template>
  <div>
    <div class="mb-1 flex justify-between text-sm">
      <span class="text-slate-600">{{ label }}</span>
      <span class="font-semibold tabular-nums">{{ pct(value) }}</span>
    </div>
    <div class="h-2.5 overflow-hidden rounded-full bg-slate-100" role="meter" :aria-label="label"
      aria-valuemin="0" aria-valuemax="100" :aria-valuenow="Math.round(value * 100)">
      <div class="h-full rounded-full transition-all duration-700" :class="color" :style="{ width: `${value * 100}%` }" />
    </div>
  </div>
</template>
