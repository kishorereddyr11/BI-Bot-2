import React, { useEffect, useMemo, useRef, useState } from 'react'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart, GaugeChart, FunnelChart, HeatmapChart, TreemapChart, SankeyChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, GraphicComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useTheme } from '../theme.jsx'
import { buildOption, sparkOption } from '../lib/chartOptions.js'
import { fmtVal } from '../lib/format.jsx'
import { TONES, PALETTE, mix } from '../lib/chartTheme.js'
import Icon from '../icons.jsx'

echarts.use([BarChart, LineChart, PieChart, GaugeChart, FunnelChart, HeatmapChart, TreemapChart, SankeyChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, GraphicComponent, CanvasRenderer])

/** Thin ECharts wrapper: init once, resize with container, dispose on unmount */
export function EChart({ option, height = 360, onReady, onEvents, style }) {
  const el = useRef(null), inst = useRef(null)
  useEffect(() => {
    const c = echarts.init(el.current, null, { renderer: 'canvas' }); inst.current = c
    const ro = new ResizeObserver(() => c.resize()); ro.observe(el.current)
    onReady && onReady(c)
    return () => { ro.disconnect(); c.dispose(); inst.current = null }
  }, [])
  useEffect(() => {
    const c = inst.current; if (!c) return
    c.setOption(option, true)
    if (onEvents) Object.entries(onEvents).forEach(([k, fn]) => { c.off(k); c.on(k, fn) })
  }, [option])
  return <div ref={el} style={{ width: '100%', height, ...style }} />
}

export function Spark({ data, color }) {
  const { T } = useTheme(); const opt = useMemo(() => sparkOption(data, color, T), [data, color, T])
  return <EChart option={opt} height={46} />
}

const toneColor = (it, i) => (it.tone && TONES[it.tone]) || PALETTE[i % PALETTE.length]

function Donut({ spec, T, compact }) {
  const [hover, setHover] = useState(null); const inst = useRef(null)
  const items = spec.items, total = items.reduce((a, i) => a + i.value, 0)
  const option = useMemo(() => buildOption(spec, T, { compact }), [spec, T, compact])
  const events = useMemo(() => ({ mouseover: (p) => setHover(p.dataIndex), globalout: () => setHover(null) }), [])
  const hi = (i) => { setHover(i); inst.current && inst.current.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: i }) }
  const lo = () => { setHover(null); inst.current && inst.current.dispatchAction({ type: 'downplay', seriesIndex: 0 }) }
  const h = hover != null ? items[hover] : null
  return (
    <div className={`donut ${compact ? 'is-compact' : ''}`}>
      <div className="donut-chart">
        <EChart option={option} height={compact ? 230 : 320} onReady={(c) => (inst.current = c)} onEvents={events} />
        <div className="donut-center">
          <div className="donut-value">{h ? fmtVal(h.value, spec.fmt) : spec.centerValue}</div>
          <div className="donut-label">{h ? `${h.name}` : spec.centerLabel}</div>
          {h && <div className="donut-pct">{((h.value / total) * 100).toFixed(1)}%</div>}
        </div>
      </div>
      <ul className="donut-legend">
        {items.map((it, i) => { const c = toneColor(it, i); const p = (it.value / total) * 100
          return (
            <li key={it.name} className={hover === i ? 'on' : ''} onMouseEnter={() => hi(i)} onMouseLeave={lo} style={{ '--c': c, '--c2': mix(c, 0.35), animationDelay: `${i * 60}ms` }}>
              <span className="lg-dot" />
              <span className="lg-name">{it.name}</span>
              <span className="lg-val">{fmtVal(it.value, spec.fmt)}</span>
              <span className="lg-pct">{p < 0.1 ? '<0.1' : p.toFixed(1)}%</span>
              <i className="lg-bar"><b style={{ width: `${Math.max(p, 1.5)}%` }} /></i>
            </li>)
        })}
      </ul>
    </div>
  )
}

const CHIPS = { overdue: 'bad', 'due within 90 days': 'warn', 'on track': 'good', upcoming: 'brand', done: 'neutral', approved: 'good', rejected: 'bad', paid: 'good', unpaid: 'warn', yes: 'good', no: 'bad', free: 'good', open: 'brand', 'in progress': 'warn', requested: 'brand', 'unassigned': 'neutral' }
function Cell({ v }) {
  if (v == null || v === '') return <span className="dim">—</span>
  const s = String(v)
  if (s.startsWith('✔')) return <span className="chip good"><Icon name="Check" size={12} />{s.slice(1).trim()}</span>
  if (s.startsWith('✖')) return <span className="chip bad"><Icon name="X" size={12} />{s.slice(1).trim()}</span>
  const t = CHIPS[s.toLowerCase()]; if (t) return <span className={`chip ${t}`}>{s}</span>
  return <>{s}</>
}
export function TableView({ columns, rows, maxHeight = 420 }) {
  return (
    <div className="tv-wrap" style={{ maxHeight }}>
      <table className="tv">
        <thead><tr>{columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className={j === 0 ? 'first' : ''}><Cell v={v} /></td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}

/** Renders any chart spec */
export default function ChartView({ spec, height = 360, compact = false, view = 'chart', table }) {
  const { T } = useTheme()
  const option = useMemo(() => (spec.type === 'table' || spec.type === 'donut' ? null : buildOption(spec, T, { compact })), [spec, T, compact])
  if (view === 'table' || spec.type === 'table') return <TableView columns={table.columns} rows={table.rows} maxHeight={compact ? 300 : 440} />
  if (spec.type === 'donut') return <Donut spec={spec} T={T} compact={compact} />
  const h = spec.type === 'gauge' ? (compact ? 250 : 320) : spec.type === 'funnel' ? (compact ? 280 : 340) : spec.type === 'sankey' ? (compact ? 320 : 420) : spec.type === 'heatmap' ? (compact ? 300 : 400) : spec.type === 'treemap' ? (compact ? 280 : 360) : (spec.type === 'hbar' || spec.orient === 'h') ? Math.max(compact ? 280 : 300, spec.categories.length * (compact ? 26 : 34) + 40) : height
  return <EChart option={option} height={compact && spec.type !== 'hbar' && spec.orient !== 'h' ? Math.min(h, 330) : h} />
}
