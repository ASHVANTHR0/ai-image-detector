import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView, meta: { title: 'Dashboard' } },
  { path: '/detect', name: 'detect', component: () => import('../views/DetectView.vue'), meta: { title: 'Detect' } },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue'), meta: { title: 'History' } },
  { path: '/history/:id', name: 'detection', component: () => import('../views/DetectionDetailView.vue'), meta: { title: 'Detection' } },
  { path: '/analytics', name: 'analytics', component: () => import('../views/AnalyticsView.vue'), meta: { title: 'Analytics' } },
  { path: '/about', name: 'about', component: () => import('../views/AboutView.vue'), meta: { title: 'About' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.afterEach((to) => {
  document.title = `${to.meta.title ?? 'AI Image Detector'} · AI Image Detector`
})

export default router
