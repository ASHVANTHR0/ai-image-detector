<script setup>
import { computed, ref } from 'vue'
import ConfidenceBadge from './ConfidenceBadge.vue'
import PredictionBadge from './PredictionBadge.vue'
import ProbabilityBar from './ProbabilityBar.vue'
import { PREDICTION_META, dateTime, pct, seconds } from '../services/format'

const props = defineProps({ result: { type: Object, required: true } })
const meta = computed(() => PREDICTION_META[props.result.prediction])
const showDetails = ref(false)
const f = computed(() => props.result.forensics)
</script>

<template>
  <section class="card border-2" :class="meta.border" aria-live="polite">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-500">Result</h2>
      <span v-if="result.cached" class="text-xs text-slate-500">Same file analysed before · showing saved result</span>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-3">
      <PredictionBadge :prediction="result.prediction" large />
      <ConfidenceBadge :confidence="result.confidence" />
    </div>

    <p v-if="result.recommendation" class="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
      <b>Leans {{ result.ai_probability >= 0.5 ? 'AI generated' : 'real' }}
        ({{ pct(Math.max(result.ai_probability, result.real_probability)) }})</b>, but not strongly enough for a definite answer.
      {{ result.recommendation }}
    </p>

    <div v-if="result.decided_by === 'provenance'" class="mt-3 rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-950">
      <p class="font-semibold">Decided by evidence inside the file</p>
      <ul class="mt-1 list-disc space-y-0.5 pl-5">
        <li v-for="(s, i) in result.provenance.signals.filter((x) => x.verdict)" :key="i">{{ s.detail }}</li>
      </ul>
      <p class="mt-2 text-xs text-indigo-800">The detectors alone estimated {{ pct(result.model_ai_probability) }} AI.</p>
    </div>
    <p v-else-if="result.provenance?.signals?.length" class="mt-3 text-xs text-slate-500">
      Metadata note: {{ result.provenance.signals.map((s) => s.detail).join(' · ') }}
    </p>

    <div class="mt-5 space-y-3">
      <ProbabilityBar label="AI probability" :value="result.ai_probability" color="bg-ai" />
      <ProbabilityBar label="Real probability" :value="result.real_probability" color="bg-real" />
    </div>

    <dl class="mt-5 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
      <div><dt class="text-slate-500">File</dt><dd class="truncate font-medium" :title="result.filename">{{ result.filename }}</dd></div>
      <div><dt class="text-slate-500">Processing time</dt><dd class="font-medium">{{ seconds(result.processing_time_ms) }}</dd></div>
      <div><dt class="text-slate-500">Model</dt><dd class="font-medium">{{ result.model_name }}</dd></div>
      <div><dt class="text-slate-500">Analysed</dt><dd class="font-medium">{{ dateTime(result.created_at) }}</dd></div>
    </dl>

    <button class="mt-5 text-sm font-medium text-indigo-700 hover:underline" :aria-expanded="showDetails"
      @click="showDetails = !showDetails">
      {{ showDetails ? 'Hide' : 'Show' }} technical details
    </button>
    <div v-if="showDetails" class="mt-3 grid gap-4 sm:grid-cols-2">
      <div v-if="result.member_scores">
        <h3 class="mb-2 text-sm font-semibold">Individual detectors (AI probability)</h3>
        <ul class="space-y-1 text-sm">
          <li v-for="(score, name) in result.member_scores" :key="name" class="flex justify-between">
            <span class="text-slate-600">{{ name }}</span><span class="tabular-nums">{{ pct(score) }}</span>
          </li>
        </ul>
      </div>
      <div v-if="f">
        <h3 class="mb-2 text-sm font-semibold">Forensic information</h3>
        <ul class="space-y-1 text-sm text-slate-600">
          <li>{{ f.format }} · {{ f.width }}×{{ f.height }} · {{ f.mode }}</li>
          <li>EXIF metadata: {{ f.has_exif ? 'present' : 'none' }}<span v-if="f.camera"> ({{ f.camera }})</span></li>
          <li v-if="f.software">Software tag: {{ f.software }}</li>
          <li v-if="f.generator_metadata_hints?.length" class="text-ai">Generator names in metadata: {{ f.generator_metadata_hints.join(', ') }}</li>
          <li v-if="f.jpeg_quality_estimate">Estimated JPEG quality: {{ f.jpeg_quality_estimate }}</li>
          <li>Noise level: {{ f.noise_level }} · High-frequency ratio: {{ f.high_frequency_ratio }}</li>
        </ul>
        <p class="mt-2 text-xs text-slate-500">Metadata can be removed or faked, so it does not affect the prediction.</p>
      </div>
    </div>
  </section>
</template>
