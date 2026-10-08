<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ResultCard from '../components/ResultCard.vue'
import { api, errorMessage } from '../services/api'

const route = useRoute()
const result = ref(null)
const error = ref('')

watch(() => route.params.id, async (id) => {
  if (!id) return
  result.value = null
  error.value = ''
  try {
    result.value = await api.detection(id)
  } catch (e) {
    error.value = errorMessage(e)
  }
}, { immediate: true })
</script>

<template>
  <div class="space-y-4">
    <RouterLink to="/history" class="text-sm font-medium text-indigo-700 hover:underline">← Back to history</RouterLink>
    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{{ error }}</p>
    <div v-else-if="!result" class="card h-64 animate-pulse" />
    <ResultCard v-else :result="result" />
    <p v-if="result" class="text-xs text-slate-500">
      Uploaded images are not stored; only the result and the file's SHA-256 hash ({{ result.file_hash.slice(0, 16) }}…) are kept.
    </p>
  </div>
</template>
