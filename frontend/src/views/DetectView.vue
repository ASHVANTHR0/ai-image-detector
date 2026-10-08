<script setup>
import { onBeforeUnmount, ref } from 'vue'
import ResultCard from '../components/ResultCard.vue'
import UploadDropzone from '../components/UploadDropzone.vue'
import { api, errorMessage } from '../services/api'

const file = ref(null)
const preview = ref('')
const result = ref(null)
const error = ref('')
const busy = ref(false)
const progress = ref(0)

function reset() {
  if (preview.value) URL.revokeObjectURL(preview.value)
  file.value = null
  preview.value = ''
  result.value = null
  error.value = ''
  progress.value = 0
}

async function analyse(selected) {
  reset()
  file.value = selected
  preview.value = URL.createObjectURL(selected)
  busy.value = true
  try {
    result.value = await api.detect(selected, (p) => (progress.value = p))
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    busy.value = false
  }
}

onBeforeUnmount(reset)
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">AI image detector</h1>
      <p class="mt-1 text-sm text-slate-600">Upload an image to estimate whether it is AI generated or a real photograph.</p>
    </div>

    <UploadDropzone v-if="!file" :disabled="busy" @select="analyse" @error="(m) => (error = m)" />

    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{{ error }}</p>

    <div v-if="file" class="grid gap-6 lg:grid-cols-5">
      <figure class="card lg:col-span-2">
        <img :src="preview" :alt="`Uploaded image ${file.name}`" class="mx-auto max-h-96 rounded-lg object-contain" />
        <figcaption class="mt-3 truncate text-center text-sm text-slate-500">{{ file.name }} · {{ (file.size / 1024).toFixed(0) }} KB</figcaption>
      </figure>

      <div class="space-y-4 lg:col-span-3">
        <div v-if="busy" class="card" aria-busy="true">
          <p class="font-medium">{{ progress < 100 ? `Uploading… ${progress}%` : 'Analysing with detectors…' }}</p>
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-indigo-600 transition-all" :class="{ 'animate-pulse': progress >= 100 }"
              :style="{ width: `${Math.max(progress, 5)}%` }" />
          </div>
          <div class="mt-5 space-y-3">
            <div class="h-4 w-1/2 animate-pulse rounded bg-slate-200" />
            <div class="h-3 w-full animate-pulse rounded bg-slate-100" />
            <div class="h-3 w-full animate-pulse rounded bg-slate-100" />
          </div>
        </div>
        <ResultCard v-else-if="result" :result="result" />
        <button class="btn-secondary" :disabled="busy" @click="reset">Analyse another image</button>
      </div>
    </div>
  </div>
</template>
