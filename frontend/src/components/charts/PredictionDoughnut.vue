<script setup>
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { COLORS } from './setup'

const props = defineProps({ ai: Number, real: Number, uncertain: Number })
const data = computed(() => ({
  labels: ['AI generated', 'Real', 'Uncertain'],
  datasets: [{ data: [props.ai, props.real, props.uncertain], backgroundColor: [COLORS.ai, COLORS.real, COLORS.uncertain], borderWidth: 2 }],
}))
const options = { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
</script>

<template>
  <div class="h-64"><Doughnut :data="data" :options="options" aria-label="Prediction distribution chart" role="img" /></div>
</template>
