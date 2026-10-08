<script setup>
import { ref } from 'vue'
import { ALLOWED_EXTENSIONS, MAX_UPLOAD_MB } from '../services/api'

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['select', 'error'])
const input = ref(null)
const dragging = ref(false)

function check(file) {
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) return `Unsupported file type "${ext}". Use ${ALLOWED_EXTENSIONS.join(', ')}.`
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `File is larger than ${MAX_UPLOAD_MB} MB.`
  if (file.size === 0) return 'File is empty.'
  return null
}

function handle(files) {
  if (props.disabled || !files?.length) return
  const file = files[0]
  const problem = check(file)
  problem ? emit('error', problem) : emit('select', file)
}

function onDrop(e) {
  dragging.value = false
  handle(e.dataTransfer.files)
}

function open() {
  if (!props.disabled) input.value.click()
}
</script>

<template>
  <div role="button" tabindex="0" :aria-disabled="disabled"
    class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition"
    :class="[dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white hover:border-indigo-400',
      disabled ? 'opacity-60' : 'cursor-pointer']"
    @click="open" @keydown.enter.prevent="open" @keydown.space.prevent="open"
    @dragover.prevent="dragging = !disabled" @dragleave.prevent="dragging = false" @drop.prevent="onDrop">
    <svg class="mb-3 h-10 w-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
    <p class="font-medium text-slate-700">Drag &amp; drop an image here</p>
    <p class="mb-4 text-sm text-slate-500">JPG, PNG, WEBP or BMP · up to {{ MAX_UPLOAD_MB }} MB</p>
    <span class="btn-primary pointer-events-none">Choose image</span>
    <input ref="input" type="file" class="hidden" :accept="ALLOWED_EXTENSIONS.join(',')"
      @change="handle($event.target.files); $event.target.value = ''" />
  </div>
</template>
