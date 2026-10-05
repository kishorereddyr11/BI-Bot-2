import React, { useMemo, useState } from 'react'
import ChartView from './Chart.jsx'
import { KpiTile } from './Kpi.jsx'
import { Rich, plain, nowTime } from '../lib/format.jsx'
import { deriveTable, toCSV, download } from '../lib/table.js'
import Icon from '../icons.jsx'
import data from '../data/answers.json'

const rows = data.rows
export function ChartCard({ q, title, subtitle, compact = false, showSource = false }) {
  const [view, setView] = useState('chart'); const [done, setDone] = useState(false)
  const table = useMemo(() => deriveTable(q.chart), [q])
  const isTable = q.chart.type === 'table'
  const csv = () => download(`${(title || q.q).replace(/[^a-z0-9]+/gi, '_').slice(0, 60)}.csv`, toCSV(table.columns, table.rows))
  return (
    <div className="chart-card">
      <div className="chart-head">
        <div className="chart-title"><span>{title || q.q}</span>{subtitle && <small>{subtitle}</small>}</div>
        <div className="chart-tools">
          {!isTable && (
            <div className="seg">
              <button className={view === 'chart' ? 'on' : ''} onClick={() => setView('chart')}><Icon name="BarChart3" size={14} />Chart</button>
              <button className={view === 'table' ? 'on' : ''} onClick={() => setView('table')}><Icon name="Table2" size={14} />Table</button>
            </div>)}
          <button className="tool-btn" onClick={csv} title="Download as CSV"><Icon name="FileSpreadsheet" size={16} /></button>
        </div>
      </div>
      <div className="chart-body"><ChartView key={view} spec={q.chart} view={view} table={table} compact={compact} /></div>
    </div>
  )
}

export function Answer({ q, time }) {
  const [copied, setCopied] = useState(false); const [open, setOpen] = useState(false)
  const copy = () => { navigator.clipboard?.writeText(plain(q.briefing)); setCopied(true); setTimeout(() => setCopied(false), 1600) }
  const recs = q.src.reduce((a, s) => a + (rows[s] || 0), 0)
  return (
    <div className="answer">
      <div className="answer-top"><span>BI Bot</span><span>{time}</span></div>
      <section className="briefing">
        <div className="briefing-head">
          <span><Icon name="Sparkles" size={15} />Executive briefing</span>
          <button className="mini-btn" onClick={copy} title="Copy">{copied ? <Icon name="Check" size={15} /> : <Icon name="Copy" size={15} />}</button>
        </div>
        <p><Rich text={q.briefing} /></p>
      </section>
      <div className="kpi-row" data-n={q.kpis.length}>{q.kpis.map((k, i) => <KpiTile key={i} k={k} i={i} />)}</div>
      <ChartCard q={q} />
      <section className="takeaways">
        <div className="takeaways-head"><Icon name="Lightbulb" size={15} />Key takeaways</div>
        <ul>{q.insights.map((t, i) => <li key={i} style={{ animationDelay: `${i * 110}ms` }}><Icon name="Zap" size={14} /><span><Rich text={t} /></span></li>)}</ul>
      </section>
      <footer className="answer-foot">
        <button className="how" onClick={() => setOpen(!open)}><Icon name="Layers" size={15} />How was this calculated?<Icon name="ChevronDown" size={14} className={open ? 'rot' : ''} /></button>
        <span className="verified"><Icon name="CheckCircle2" size={15} />Computed live from the workbook · {q.src.join(', ')} · {recs.toLocaleString()} records</span>
        {open && <div className="how-body">This answer is calculated directly from <b>{q.src.map((s) => s.replace(/_/g, ' ')).join(', ')}</b> in the HR workbook, as of <b>30 Sep 2026</b>. Calendar-based columns (days open, SLA met, net pay, leave days, etc.) are recalculated with the same rules as the Excel formulas. All data is dummy and generated for this demo.</div>}
      </footer>
    </div>
  )
}
