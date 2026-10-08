<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/detect', label: 'Detect' },
  { to: '/history', label: 'History' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/about', label: 'About' },
]
const route = useRoute()
const menuOpen = ref(false)
const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b border-slate-200 bg-white">
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <RouterLink to="/" class="flex items-center gap-2 font-semibold text-slate-900">
          <img src="/favicon.svg" alt="" class="h-7 w-7" />
          AI Image Detector
        </RouterLink>
        <button class="btn-secondary sm:hidden" :aria-expanded="menuOpen" aria-label="Toggle menu" @click="menuOpen = !menuOpen">☰</button>
        <ul class="hidden gap-1 sm:flex">
          <li v-for="l in links" :key="l.to">
            <RouterLink :to="l.to" class="rounded-md px-3 py-2 text-sm font-medium"
              :class="isActive(l.to) ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'">{{ l.label }}</RouterLink>
          </li>
        </ul>
      </nav>
      <ul v-if="menuOpen" class="border-t border-slate-100 px-4 py-2 sm:hidden">
        <li v-for="l in links" :key="l.to">
          <RouterLink :to="l.to" class="block rounded-md px-3 py-2 text-sm"
            :class="isActive(l.to) ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-100'"
            @click="menuOpen = false">{{ l.label }}</RouterLink>
        </li>
      </ul>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-6">
      <RouterView />
    </main>
    <footer class="mx-auto max-w-6xl px-4 pb-8 text-xs text-slate-500">
      Runs fully locally with open-source models. Results are probabilistic estimates, not proof.
    </footer>
  </div>
</template>
