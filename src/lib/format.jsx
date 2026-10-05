import React from 'react'

const nf0 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const trim = (v, d = 1) => { const s = Number(v).toFixed(d); return s.replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1') }

export const inr = (x) => {
  const a = Math.abs(x)
  if (a >= 1e7) return `₹${(x / 1e7).toFixed(2)} Cr`
  if (a >= 1e5) return `₹${(x / 1e5).toFixed(1)} L`
  if (a >= 1e3) return `₹${(x / 1e3).toFixed(1)}K`
  return `₹${nf0.format(x)}`
}

/** Format a value according to a spec `fmt` key */
export function fmtVal(v, fmt = 'int') {
  if (v == null || Number.isNaN(v)) return '–'
  switch (fmt) {
    case 'int': return nf0.format(v)
    case 'dec1': return trim(v, 1)
    case 'pct': return `${trim(v, 1)}%`
    case 'inr': return inr(v)
    case 'lpa': return `₹${trim(v, 1)} L`
    case 'days': return `${trim(v, 1)} ${Number(v) === 1 ? 'day' : 'days'}`
    case 'min': return `${trim(v, 1)} min`
    case 'rating': return `${Number(v).toFixed(1)} ★`
    default: return String(v)
  }
}
/** KPI value: like fmtVal but 'text' prints as is */
export const fmtKpi = (v, fmt) => (fmt === 'text' ? String(v) : fmtVal(v, fmt))

/** compact axis label */
export function axisFmt(v, fmt = 'int') {
  if (fmt === 'inr') return inr(v).replace('.00', '')
  if (fmt === 'int') return Math.abs(v) >= 1e6 ? `${trim(v / 1e6, 1)}M` : Math.abs(v) >= 1e4 ? `${trim(v / 1e3, 1)}K` : nf0.format(v)
  if (fmt === 'pct') return `${trim(v, 0)}%`
  if (fmt === 'lpa') return `${trim(v, 0)} L`
  return trim(v, 1)
}

/** Render **bold** markup */
export function Rich({ text }) {
  const parts = String(text).split(/\*\*(.+?)\*\*/g)
  return <>{parts.map((p, i) => (i % 2 ? <strong key={i}>{p}</strong> : <React.Fragment key={i}>{p}</React.Fragment>))}</>
}
export const plain = (t) => String(t).replace(/\*\*/g, '')
export const nowTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
