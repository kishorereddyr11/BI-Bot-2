import { fmtVal } from './format.jsx'

/** Turn a chart spec into {columns, rows} for the Table view + CSV */
export function deriveTable(spec) {
  const f = (v, fmt) => fmtVal(v, fmt || spec.fmt)
  switch (spec.type) {
    case 'table': return { columns: spec.columns, rows: spec.rows }
    case 'donut': case 'treemap': case 'funnel': {
      const tot = spec.items.reduce((a, i) => a + i.value, 0), first = spec.items[0]?.value
      return spec.type === 'funnel'
        ? { columns: ['Stage', 'Count', '% of start'], rows: spec.items.map((i) => [i.name, f(i.value), `${((i.value / first) * 100).toFixed(1)}%`]) }
        : { columns: ['Item', 'Value', 'Share'], rows: spec.items.map((i) => [i.name, f(i.value), `${((i.value / tot) * 100).toFixed(1)}%`]) }
    }
    case 'gauge': return { columns: ['Measure', 'Value'], rows: [[spec.label || 'Value', f(spec.value)]] }
    case 'heatmap': return { columns: ['', ...spec.xs], rows: spec.ys.map((y, yi) => [y, ...spec.xs.map((_, xi) => f((spec.data.find((d) => d[0] === xi && d[1] === yi) || [0, 0, 0])[2]))]) }
    case 'sankey': return { columns: ['From', 'To', 'Candidates'], rows: [...spec.links].sort((a, b) => b.value - a.value).map((l) => [l.source, l.target, f(l.value)]) }
    default: {
      const rev = spec.type === 'hbar' || spec.orient === 'h'
      const idx = spec.categories.map((_, i) => i); if (rev) idx.reverse()
      return { columns: ['Item', ...spec.series.map((s) => s.name)], rows: idx.map((i) => [spec.categories[i], ...spec.series.map((s) => f(s.data[i], s.fmt))]) }
    }
  }
}

const esc = (v) => { const s = v == null ? '' : String(v); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s }
export function toCSV(columns, rows) { return '﻿' + [columns, ...rows].map((r) => r.map(esc).join(',')).join('\r\n') }
export function download(filename, text, type = 'text/csv;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([text], { type })); const a = document.createElement('a')
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
