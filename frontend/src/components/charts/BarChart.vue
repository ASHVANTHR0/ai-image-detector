<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { COLORS } from './setup'

const props = defineProps({
  labels: { type: Array, required: true },
  values: { type: Array, required: true },
  colors: { type: [String, Array], default: COLORS.accent },
  xTitle: String,
  yTitle: String,
  percent: Boolean,
  horizontal: Boolean,
  ariaLabel: String,
})

const data = computed(() => ({
  labels: props.labels,
  datasets: [{ data: props.values, backgroundColor: props.colors, borderRadius: 4, maxBarThickness: 48 }],
}))
const options = computed(() => {
  const value = { beginAtZero: true, title: { display: !!props.yTitle, text: props.yTitle },
    ...(props.percent ? { max: 1, ticks: { callback: (v) => `${Math.round(v * 100)}%` } } : { ticks: { precision: 0 } }) }
  const category = { title: { display: !!props.xTitle, text: props.xTitle }, grid: { display: false } }
  return {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: props.horizontal ? 'y' : 'x',
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (c) => (props.percent ? `${(c.raw * 100).toFixed(1)}%` : `${c.raw}`) } },
    },
    scales: props.horizontal ? { x: value, y: category } : { x: category, y: value },
  }
})
</script>

<template>
  <div class="h-64"><Bar :data="data" :options="options" role="img" :aria-label="ariaLabel" /></div>
</template>
