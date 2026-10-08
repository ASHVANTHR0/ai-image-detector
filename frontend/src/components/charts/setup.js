import { ArcElement, BarElement, CategoryScale, Chart, Legend, LinearScale, Tooltip } from 'chart.js'

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)
Chart.defaults.font.family = 'ui-sans-serif, system-ui, sans-serif'
Chart.defaults.color = '#475569'

export const COLORS = { ai: '#dc2626', real: '#059669', uncertain: '#d97706', accent: '#4f46e5', muted: '#94a3b8' }
