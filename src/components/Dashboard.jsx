import React from 'react'
import { ChartCard } from './Answer.jsx'
import { Spark } from './Chart.jsx'
import { useCountUp } from './Kpi.jsx'
import { fmtKpi } from '../lib/format.jsx'
import Icon from '../icons.jsx'
import data from '../data/answers.json'
import dash from '../data/dashboard.json'

const QBY = Object.fromEntries(data.questions.map((q) => [q.id, q]))
const ACC = { blue: '#2F6BFF', cyan: '#14C8E8', emerald: '#10D9A0', violet: '#8B5CF6', amber: '#FFB020', rose: '#FF4D9D' }

function KpiCard({ k, i }) {
  const v = useCountUp(k.num, { duration: 1300 }); const c = ACC[k.accent]
  return (
    <div className="dk" style={{ '--ac': c, animationDelay: `${i * 80}ms` }}>
      <div className="dk-top">
        <span className="dk-ico"><Icon name={k.icon} size={18} /></span>
        <span className={`delta ${k.delta.up ? 'up' : 'down'}`}><Icon name={k.delta.up ? 'ArrowUp' : 'ArrowDown'} size={12} />{Math.abs(k.delta.pct)}%</span>
      </div>
      <div className="dk-value">{fmtKpi(k.fmt === 'int' ? Math.round(v) : v, k.fmt)}</div>
      <div className="dk-label">{k.label}</div>
      <div className="dk-sub">{k.sub}</div>
      <div className="dk-spark"><Spark data={k.spark} color={c} /></div>
    </div>
  )
}

export default function Dashboard({ openQuestion, refreshKey }) {
  return (
    <div className="page dashboard" key={refreshKey}>
      <div className="page-head">
        <div><div className="eyebrow"><Icon name="Activity" size={14} />Executive overview</div><h1>HR Command Center</h1><p>The 15 most important charts across helpdesk, leave, payroll, benefits, claims, documents, people and hiring · data as of 30 Sep 2026</p></div>
        <div className="live-badge"><span />Demo data</div>
      </div>
      <div className="dk-grid">{dash.kpis.map((k, i) => <KpiCard key={k.label} k={k} i={i} />)}</div>
      <div className="dg">
        {dash.charts.map((c, i) => {
          const q = QBY[c.qid]
          return (
            <div key={c.qid} className={`dg-item ${c.span}`} style={{ animationDelay: `${160 + i * 60}ms` }}>
              <ChartCard q={q} title={c.title} subtitle={c.subtitle} compact />
              <button className="ask-link" onClick={() => openQuestion(c.qid)}>See the full explanation in Copilot<Icon name="ArrowUpRight" size={14} /></button>
            </div>)
        })}
      </div>
    </div>
  )
}
