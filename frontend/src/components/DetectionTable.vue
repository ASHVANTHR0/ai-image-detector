<script setup>
import { useRouter } from 'vue-router'
import PredictionBadge from './PredictionBadge.vue'
import { dateTime, pct, topProbability } from '../services/format'

defineProps({ items: { type: Array, required: true }, compact: Boolean })
const router = useRouter()
const open = (id) => router.push(`/history/${id}`)
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left text-sm">
      <thead class="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
        <tr>
          <th class="py-2 pr-4 font-medium">Date</th>
          <th class="py-2 pr-4 font-medium">File</th>
          <th class="py-2 pr-4 font-medium">Prediction</th>
          <th class="py-2 pr-4 text-right font-medium">Confidence</th>
          <th v-if="!compact" class="py-2 pr-4 text-right font-medium">AI prob.</th>
          <th v-if="!compact" class="py-2 font-medium">Model</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in items" :key="d.id" tabindex="0"
          class="cursor-pointer border-b border-slate-100 hover:bg-slate-50 focus:bg-indigo-50 focus:outline-none"
          @click="open(d.id)" @keydown.enter="open(d.id)">
          <td class="whitespace-nowrap py-2 pr-4 text-slate-600">{{ dateTime(d.created_at) }}</td>
          <td class="max-w-[14rem] truncate py-2 pr-4 font-medium" :title="d.filename">{{ d.filename }}</td>
          <td class="py-2 pr-4"><PredictionBadge :prediction="d.prediction" /></td>
          <td class="py-2 pr-4 text-right tabular-nums">{{ pct(topProbability(d)) }}</td>
          <td v-if="!compact" class="py-2 pr-4 text-right tabular-nums">{{ pct(d.ai_probability) }}</td>
          <td v-if="!compact" class="py-2 text-slate-600">{{ d.model_name }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
