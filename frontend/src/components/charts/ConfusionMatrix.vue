<script setup>
import { computed } from 'vue'

const props = defineProps({ matrix: { type: Object, required: true } }) // { TN, FP, FN, TP }
const cells = computed(() => {
  const m = props.matrix
  const max = Math.max(m.TN, m.FP, m.FN, m.TP, 1)
  const cell = (key, label, correct) => ({ key, label, value: m[key], correct, alpha: 0.12 + 0.75 * (m[key] / max) })
  return [
    [cell('TN', 'Real correctly accepted', true), cell('FP', 'Real flagged as AI', false)],
    [cell('FN', 'AI missed', false), cell('TP', 'AI correctly detected', true)],
  ]
})
</script>

<template>
  <div class="overflow-x-auto">
    <table class="mx-auto text-sm">
      <thead>
        <tr><th /><th class="px-2 pb-2 text-xs font-medium text-slate-500">Predicted REAL</th><th class="px-2 pb-2 text-xs font-medium text-slate-500">Predicted AI</th></tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in cells" :key="i">
          <th class="pr-3 text-right text-xs font-medium text-slate-500">Actual {{ i === 0 ? 'REAL' : 'AI' }}</th>
          <td v-for="c in row" :key="c.key" class="p-1">
            <div class="flex h-24 w-32 flex-col items-center justify-center rounded-lg text-center sm:w-40"
              :style="{ backgroundColor: c.correct ? `rgba(5,150,105,${c.alpha})` : `rgba(220,38,38,${c.alpha})` }">
              <span class="text-2xl font-semibold tabular-nums" :class="c.alpha > 0.55 ? 'text-white' : 'text-slate-900'">{{ c.value }}</span>
              <span class="text-xs" :class="c.alpha > 0.55 ? 'text-white' : 'text-slate-700'">{{ c.key }} · {{ c.label }}</span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
