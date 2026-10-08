<script setup>
import { computed, ref, watch } from 'vue'
import DetectionTable from '../components/DetectionTable.vue'
import { api, errorMessage } from '../services/api'

const PAGE = 20
const items = ref([])
const total = ref(0)
const page = ref(0)
const filter = ref('')
const loading = ref(true)
const error = ref('')
const pages = computed(() => Math.max(1, Math.ceil(total.value / PAGE)))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = { limit: PAGE, offset: page.value * PAGE }
    if (filter.value) params.prediction = filter.value
    const res = await api.detections(params)
    items.value = res.items
    total.value = res.total
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

watch(filter, () => {
  page.value === 0 ? load() : (page.value = 0)
})
watch(page, load, { immediate: true })
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">Detection history</h1>
        <p class="mt-1 text-sm text-slate-600">{{ total }} detection{{ total === 1 ? '' : 's' }} stored locally.</p>
      </div>
      <label class="text-sm">
        <span class="mr-2 text-slate-600">Show</span>
        <select v-model="filter" class="rounded-lg border border-slate-300 bg-white px-3 py-2">
          <option value="">All predictions</option>
          <option value="AI_GENERATED">AI generated</option>
          <option value="REAL">Real</option>
          <option value="UNCERTAIN">Uncertain</option>
        </select>
      </label>
    </div>

    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">{{ error }}</p>

    <section class="card">
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 5" :key="i" class="h-8 animate-pulse rounded bg-slate-100" />
      </div>
      <DetectionTable v-else-if="items.length" :items="items" />
      <p v-else class="py-8 text-center text-sm text-slate-500">
        {{ filter ? 'No detections with this prediction.' : 'No detections yet.' }}
        <RouterLink to="/detect" class="text-indigo-700 hover:underline">Analyse an image</RouterLink>
      </p>

      <nav v-if="pages > 1" class="mt-4 flex items-center justify-between text-sm" aria-label="Pagination">
        <button class="btn-secondary" :disabled="page === 0 || loading" @click="page--">Previous</button>
        <span class="text-slate-600">Page {{ page + 1 }} of {{ pages }}</span>
        <button class="btn-secondary" :disabled="page + 1 >= pages || loading" @click="page++">Next</button>
      </nav>
    </section>
  </div>
</template>
