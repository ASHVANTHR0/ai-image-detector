export const PREDICTION_META = {
  AI_GENERATED: { label: 'AI generated', short: 'AI', icon: '⚠', text: 'text-ai', bg: 'bg-red-50', border: 'border-red-200', bar: 'bg-ai' },
  REAL: { label: 'Real', short: 'REAL', icon: '✓', text: 'text-real', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-real' },
  UNCERTAIN: { label: 'Uncertain', short: 'UNCERTAIN', icon: '?', text: 'text-uncertain', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-uncertain' },
}

export const pct = (v, digits = 1) => (v == null || Number.isNaN(v) ? '—' : `${(v * 100).toFixed(digits)}%`)

export const seconds = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(2)} s`)

export const dateTime = (iso) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

// Probability of the predicted side, matching how the history table in the plan shows "confidence".
export const topProbability = (d) => Math.max(d.ai_probability, d.real_probability)
