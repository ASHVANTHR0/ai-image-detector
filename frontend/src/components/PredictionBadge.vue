<script setup>
import { computed } from 'vue'
import { PREDICTION_META } from '../services/format'

const props = defineProps({ prediction: { type: String, required: true }, large: Boolean })
const meta = computed(() => PREDICTION_META[props.prediction] ?? PREDICTION_META.UNCERTAIN)
</script>

<template>
  <span class="inline-flex items-center gap-1.5 rounded-full border font-semibold"
    :class="[meta.bg, meta.border, meta.text, large ? 'px-4 py-1.5 text-lg' : 'px-2.5 py-0.5 text-xs']">
    <span aria-hidden="true">{{ meta.icon }}</span>{{ large ? meta.label.toUpperCase() : meta.short }}
  </span>
</template>
