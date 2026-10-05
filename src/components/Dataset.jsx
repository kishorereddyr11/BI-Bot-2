import React, { useEffect, useMemo, useRef, useState } from 'react'
import Icon from '../icons.jsx'
import { toCSV, download } from '../lib/table.js'
import manifest from '../data/tables.json'

const PAGE = 200
const cache = new Map()
const nf = new Intl.NumberFormat('en-US', { maximumFractionDigits: 4 })
const label = (n) => n.replace(/_/g, ' ')

async function loadTable(name) {
  if (cache.has(name)) return cache.get(name)
  const res = await fetch(`/data/${name}.json`); if (!res.ok) throw new Error(`Could not load ${name}`)
  const d = await res.json(); d.search = null; cache.set(name, d); return d
}
const isNum = (v) => typeof v === 'number'
const cellText = (v, col) => (v == null ? null : isNum(v) ? (Math.abs(v) >= 10000 && !/year|id|phone/i.test(col) ? nf.format(v) : String(v)) : String(v))

function Sidebar({ sel, setSel, open, close }) {
  const [term, setTerm] = useState(''); const [shut, setShut] = useState({})
  const t = term.trim().toLowerCase()
  return (
    <aside className={`sidebar ds-side ${open ? 'open' : ''}`}>
      <div className="side-head"><div><h2>Tables</h2><p>Click a table name to explore its data</p></div><button className="icon-btn only-mobile" onClick={close}><Icon name="X" size={18} /></button></div>
      <div className="filter-card"><label className="search"><Icon name="Search" size={16} /><input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Search tables…" />{term && <button onClick={() => setTerm('')}><Icon name="X" size={14} /></button>}</label></div>
      <div className="qlist">
        {manifest.map((g) => {
          const items = g.tables.filter((x) => !t || x.name.toLowerCase().replace(/_/g, ' ').includes(t)); if (!items.length) return null
          const closed = shut[g.group] && !t
          return (
            <div key={g.group} className="tgroup">
              <button className="group-head tg" onClick={() => setShut({ ...shut, [g.group]: !shut[g.group] })}><span className="cat-ico sm blue"><Icon name={g.icon} size={13} /></span>{g.group}<em>{items.length}</em><Icon name="ChevronDown" size={14} className={closed ? 'rot-neg' : ''} /></button>
              {!closed && items.map((x) => (
                <button key={x.name} className={`tbtn ${sel === x.name ? 'on' : ''}`} onClick={() => { setSel(x.name); close() }}>
                  <Icon name="Table2" size={16} /><span className="tn">{label(x.name)}</span><em>{x.rows.toLocaleString()}</em>
                </button>))}
            </div>)
        })}
      </div>
    </aside>
  )
}

export default function Dataset({ refreshKey }) {
  const [sel, setSel] = useState('Helpdesk_Tickets'); const [data, setData] = useState(null); const [err, setErr] = useState(null)
  const [page, setPage] = useState(0); const [sort, setSort] = useState(null); const [q, setQ] = useState(''); const [drawer, setDrawer] = useState(false)
  const scroller = useRef(null)
  const meta = useMemo(() => manifest.flatMap((g) => g.tables).find((x) => x.name === sel), [sel])
  useEffect(() => { let live = true; setData(null); setErr(null); setPage(0); setSort(null); setQ('')
    loadTable(sel).then((d) => live && setData(d)).catch((e) => live && setErr(e.message)); return () => { live = false } }, [sel, refreshKey])
  useEffect(() => { setPage(0) }, [q, sort])
  useEffect(() => { scroller.current && scroller.current.scrollTo({ top: 0 }) }, [page, sel])

  const idx = useMemo(() => {
    if (!data) return []
    let ids = null; const t = q.trim().toLowerCase()
    if (t) { if (!data.search) data.search = data.rows.map((r) => r.join('\u0001').toLowerCase()); ids = []; data.search.forEach((s, i) => { if (s.includes(t)) ids.push(i) }) }
    else ids = data.rows.map((_, i) => i)
    if (sort) {
      const c = sort.col, d = sort.dir === 'asc' ? 1 : -1, rows = data.rows
      ids = ids.slice().sort((a, b) => { const x = rows[a][c], y = rows[b][c]; if (x == null) return y == null ? 0 : 1; if (y == null) return -1
        return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * d })
    }
    return ids
  }, [data, q, sort])
  const pages = Math.max(1, Math.ceil(idx.length / PAGE)), from = idx.length ? page * PAGE + 1 : 0, to = Math.min(idx.length, (page + 1) * PAGE)
  const slice = data ? idx.slice(page * PAGE, page * PAGE + PAGE) : []
  const nextSort = (c) => setSort((s) => (!s || s.col !== c ? { col: c, dir: 'asc' } : s.dir === 'asc' ? { col: c, dir: 'desc' } : null))
  const csv = () => data && download(`${sel}.csv`, toCSV(data.columns, data.rows))

  return (
    <div className="copilot dataset">
      <Sidebar sel={sel} setSel={setSel} open={drawer} close={() => setDrawer(false)} />
      {drawer && <div className="scrim" onClick={() => setDrawer(false)} />}
      <section className="ds-main" key={sel}>
        <div className="ds-head">
          <button className="fab-inline only-mobile" onClick={() => setDrawer(true)}><Icon name="PanelLeft" size={18} />Tables</button>
          <div className="ds-title"><span className="ds-ico"><Icon name="Table2" size={22} /></span>
            <div><h1>{label(sel)}</h1><p>{meta?.about}</p></div></div>
          <div className="ds-stats"><span><b>{meta?.rows.toLocaleString()}</b>rows</span><span><b>{meta?.cols}</b>columns</span></div>
          <div className="ds-actions">
            <label className="search ds-search"><Icon name="Search" size={15} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search in this table…" />{q && <button onClick={() => setQ('')}><Icon name="X" size={14} /></button>}</label>
            <button className="btn-primary" onClick={csv} disabled={!data}><Icon name="Download" size={16} />Download CSV</button>
          </div>
        </div>
        <div className="ds-card">
          <div className="ds-scroll" ref={scroller}>
            {err && <div className="ds-state"><Icon name="Info" size={28} /><p>{err}</p></div>}
            {!data && !err && <div className="ds-state"><div className="loader"><i /><i /><i /></div><p>Loading {label(sel)}…</p><div className="skeleton">{Array.from({ length: 9 }).map((_, i) => <span key={i} style={{ width: `${70 + ((i * 37) % 30)}%` }} />)}</div></div>}
            {data && (
              <table className="dt">
                <thead><tr><th className="rn">#</th>{data.columns.map((c, i) => (
                  <th key={c} onClick={() => nextSort(i)} className={sort?.col === i ? 'sorted' : ''}><span>{c.replace(/_/g, ' ')}<Icon name={sort?.col === i ? (sort.dir === 'asc' ? 'ArrowUp' : 'ArrowDown') : 'ArrowUpDown'} size={13} /></span></th>))}</tr></thead>
                <tbody>{slice.map((ri, k) => { const r = data.rows[ri]; return (
                  <tr key={ri}><td className="rn">{page * PAGE + k + 1}</td>{r.map((v, j) => { const t = cellText(v, data.columns[j]); return <td key={j} className={isNum(v) ? 'num' : ''} title={t && t.length > 30 ? t : undefined}>{t == null ? <span className="dim">—</span> : t}</td> })}</tr>) })}
                  {data && idx.length === 0 && <tr><td colSpan={data.columns.length + 1} className="none">No rows match “{q}”</td></tr>}</tbody>
              </table>)}
          </div>
          <div className="ds-foot">
            <span className="range">Showing <b>{from.toLocaleString()}–{to.toLocaleString()}</b> of <b>{idx.length.toLocaleString()}</b> rows{q && ' (filtered)'}</span>
            <div className="pager">
              <button onClick={() => setPage(0)} disabled={page === 0}><Icon name="ChevronsLeft" size={16} /></button>
              <button onClick={() => setPage(page - 1)} disabled={page === 0}><Icon name="ChevronLeft" size={16} />Previous</button>
              <span className="pg">Page <b>{page + 1}</b> of {pages}</span>
              <button onClick={() => setPage(page + 1)} disabled={page >= pages - 1}>Next<Icon name="ChevronRight" size={16} /></button>
              <button onClick={() => setPage(pages - 1)} disabled={page >= pages - 1}><Icon name="ChevronsRight" size={16} /></button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
