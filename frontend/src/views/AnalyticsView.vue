<script setup>
import { computed, onMounted, ref } from 'vue'
import BarChart from '../components/charts/BarChart.vue'
import ConfusionMatrix from '../components/charts/ConfusionMatrix.vue'
import PredictionDoughnut from '../components/charts/PredictionDoughnut.vue'
import { COLORS } from '../components/charts/setup'
import StatTile from '../components/StatTile.vue'
import { api, errorMessage } from '../services/api'
import { pct, seconds } from '../services/format'

const stats = ref(null)
const evaluation = ref(null)
const error = ref('')
const split = ref('test')

onMounted(async () => {
  try {
    const [s, e] = await Promise.all([api.statistics(), api.evaluation()])
    stats.value = s
    evaluation.value = e
  } catch (e) {
    error.value = errorMessage(e)
  }
})

const binLabels = Array.from({ length: 10 }, (_, i) => `${i * 10}–${i * 10 + 10}%`)
const binColors = Array.from({ length: 10 }, (_, i) => (i < 3 ? COLORS.real : i > 6 ? COLORS.ai : COLORS.uncertain))

const latency = computed(() => {
  const times = stats.value?.processing_times_ms ?? []
  if (!times.length) return null
  const edges = [250, 500, 1000, 2000, 5000]
  const labels = ['<0.25 s', '0.25–0.5 s', '0.5–1 s', '1–2 s', '2–5 s', '>5 s']
  const counts = new Array(labels.length).fill(0)
  for (const t of times) {
    const bin = edges.findIndex((e) => t < e)
    counts[bin === -1 ? edges.length : bin]++
  }
  return { labels, counts }
})

const result = computed(() => evaluation.value?.available ? evaluation.value.splits?.[split.value] : null)
const generators = computed(() => {
  const g = result.value?.by_generator ?? {}
  const names = Object.keys(g).filter((n) => n !== 'none')
  return { labels: names, values: names.map((n) => g[n].accuracy), counts: names.map((n) => g[n].n) }
})
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Analytics</h1>
      <p class="mt-1 text-sm text-slate-600">Live usage of this installation, and the model's measured performance on the labelled test sets.</p>
    </div>

    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{{ error }}</p>

    <!-- Model performance: offline evaluation with ground truth -->
    <section class="space-y-4">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 class="text-lg font-semibold">Model performance</h2>
          <p class="text-sm text-slate-600">Measured once on held-out labelled images. These numbers do not apply to every image on the internet.</p>
        </div>
        <div v-if="evaluation?.available" class="inline-flex rounded-lg border border-slate-300 bg-white p-0.5 text-sm" role="tablist">
          <button v-for="s in Object.keys(evaluation.splits)" :key="s" role="tab" :aria-selected="split === s"
            class="rounded-md px-3 py-1.5" :class="split === s ? 'bg-indigo-600 text-white' : 'text-slate-700'" @click="split = s">
            {{ s === 'test' ? 'Seen generators' : 'Unseen generators' }}
          </button>
        </div>
      </div>

      <div v-if="evaluation && !evaluation.available" class="card text-sm text-slate-600">
        No final evaluation yet. Run <code class="rounded bg-slate-100 px-1">python scripts/final_evaluation.py --confirm</code>
        after the model and thresholds are frozen; accuracy, precision, recall, F1 and the confusion matrix will appear here.
      </div>

      <template v-if="result">
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-7">
          <StatTile label="Accuracy" :value="pct(result.accuracy)" :hint="result.ci95 ? `95% CI ${pct(result.ci95.accuracy[0])}–${pct(result.ci95.accuracy[1])}` : ''" />
          <StatTile label="Precision" :value="pct(result.precision)" />
          <StatTile label="Recall" :value="pct(result.recall)" />
          <StatTile label="F1 score" :value="pct(result.f1)" />
          <StatTile label="False positive rate" :value="pct(result.fpr)" />
          <StatTile label="ROC-AUC" :value="result.roc_auc?.toFixed(3)" />
          <StatTile label="Coverage" :value="pct(result.coverage)" hint="not Uncertain" />
        </div>
        <div class="grid gap-4 lg:grid-cols-2">
          <div class="card">
            <h3 class="mb-3 font-semibold">Confusion matrix <span class="text-sm font-normal text-slate-500">(n = {{ result.n }}, threshold 50%)</span></h3>
            <ConfusionMatrix :matrix="result.confusion_matrix" />
          </div>
          <div class="card">
            <h3 class="mb-3 font-semibold">Accuracy by AI generator</h3>
            <BarChart v-if="generators.labels.length" :labels="generators.labels" :values="generators.values" percent horizontal
              aria-label="Accuracy per generator" />
            <p v-else class="text-sm text-slate-500">No generator breakdown for this split.</p>
          </div>
        </div>
        <p class="text-xs text-slate-500">Model {{ evaluation.model }} · evaluated {{ evaluation.date }} · dataset version {{ evaluation.dataset_version }}</p>
      </template>
    </section>

    <!-- Live usage: no ground truth -->
    <section class="space-y-4">
      <div>
        <h2 class="text-lg font-semibold">Usage on this computer</h2>
        <p class="text-sm text-slate-600">Uploaded images have no known answer, so accuracy cannot be measured from them.</p>
      </div>
      <div v-if="stats && stats.total === 0" class="card text-sm text-slate-500">No images analysed yet.</div>
      <div v-else-if="stats" class="grid gap-4 lg:grid-cols-3">
        <div class="card">
          <h3 class="mb-3 font-semibold">Prediction distribution</h3>
          <PredictionDoughnut :ai="stats.ai_generated" :real="stats.real" :uncertain="stats.uncertain" />
        </div>
        <div class="card">
          <h3 class="mb-3 font-semibold">AI probability distribution</h3>
          <BarChart :labels="binLabels" :values="stats.confidence_histogram" :colors="binColors" x-title="AI probability"
            y-title="Images" aria-label="Distribution of AI probabilities" />
        </div>
        <div class="card">
          <h3 class="mb-3 font-semibold">Processing time</h3>
          <BarChart v-if="latency" :labels="latency.labels" :values="latency.counts" y-title="Images" aria-label="Processing time distribution" />
          <p class="mt-2 text-xs text-slate-500">Average {{ seconds(stats.average_processing_time_ms) }} (last {{ stats.processing_times_ms.length }} images)</p>
        </div>
      </div>
    </section>
  </div>
</template>
