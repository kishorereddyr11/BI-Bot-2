import React, { useEffect, useMemo, useRef, useState } from 'react'
import Icon from '../icons.jsx'
import { Answer } from './Answer.jsx'
import { useCountUp } from './Kpi.jsx'
import data from '../data/answers.json'

const { categories: CATS, questions: QS } = data
const CAT = Object.fromEntries(CATS.map((c) => [c.id, c]))
const QBY = Object.fromEntries(QS.map((q) => [q.id, q]))
const BADGE = { Popular: 'amber', Trend: 'cyan', Key: 'violet', New: 'emerald' }

function Hl({ text, term }) {
  if (!term) return text
  const i = text.toLowerCase().indexOf(term.toLowerCase()); if (i < 0) return text
  return <>{text.slice(0, i)}<mark>{text.slice(i, i + term.length)}</mark>{text.slice(i + term.length)}</>
}

function CategorySelect({ value, onChange }) {
  const [open, setOpen] = useState(false); const ref = useRef(null)
  useEffect(() => { const f = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }; document.addEventListener('mousedown', f); return () => document.removeEventListener('mousedown', f) }, [])
  const cur = value === 0 ? null : CAT[value]
  return (
    <div className="cat-select" ref={ref}>
      <button className={`cat-btn ${open ? 'open' : ''}`} onClick={() => setOpen(!open)}>
        <span className={`cat-ico ${cur ? cur.accent : 'blue'}`}><Icon name={cur ? cur.icon : 'Layers'} size={15} /></span>
        <span className="cat-name">{cur ? cur.name : `All Categories (${CATS.length})`}</span>
        <Icon name="ChevronDown" size={16} className="chev" />
      </button>
      {open && (
        <div className="cat-menu">
          <button className={`cat-item ${value === 0 ? 'on' : ''}`} onClick={() => { onChange(0); setOpen(false) }}>
            <span className="cat-ico blue"><Icon name="Layers" size={15} /></span><span className="cat-name">All Categories</span><em>{QS.length}</em>
          </button>
          {CATS.map((c) => (
            <button key={c.id} className={`cat-item ${value === c.id ? 'on' : ''}`} onClick={() => { onChange(c.id); setOpen(false) }}>
              <span className={`cat-ico ${c.accent}`}><Icon name={c.icon} size={15} /></span><span className="cat-name">{c.name}</span><em>{c.count}</em>
            </button>))}
        </div>)}
    </div>
  )
}

function Sidebar({ ask, asked, active, busy, open, close }) {
  const [term, setTerm] = useState(''); const [cat, setCat] = useState(0)
  const list = useMemo(() => {
    const t = term.trim().toLowerCase()
    return QS.filter((q) => (!cat || q.cat === cat) && (!t || q.q.toLowerCase().includes(t) || CAT[q.cat].name.toLowerCase().includes(t) || q.kind.toLowerCase().includes(t)))
  }, [term, cat])
  let last = null
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="side-head">
        <div><h2>Question Library</h2><p>Click any question to see the answer in the chat</p></div>
        <button className="icon-btn only-mobile" onClick={close}><Icon name="X" size={18} /></button>
      </div>
      <div className="filter-card">
        <div className="filters">
          <label className="search"><Icon name="Search" size={16} /><input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Search questions…" />{term && <button onClick={() => setTerm('')}><Icon name="X" size={14} /></button>}</label>
          <CategorySelect value={cat} onChange={setCat} />
        </div>
        <div className="showing"><span>Showing <b>{list.length}</b> question{list.length === 1 ? '' : 's'}</span>{asked.size > 0 && <span className="asked-count"><Icon name="CheckCircle2" size={13} />{asked.size} asked</span>}</div>
      </div>
      <div className="qlist">
        {list.length === 0 && <div className="empty-q"><Icon name="Search" size={26} /><p>No questions match “{term}”</p><button onClick={() => { setTerm(''); setCat(0) }}>Clear filters</button></div>}
        {list.map((q) => {
          const head = !cat && q.cat !== last ? (last = q.cat, <div key={'h' + q.cat} className="group-head"><span className={`cat-ico sm ${CAT[q.cat].accent}`}><Icon name={CAT[q.cat].icon} size={13} /></span>{CAT[q.cat].name}<em>{CAT[q.cat].count}</em></div>) : (last = q.cat, null)
          return (
            <React.Fragment key={q.id}>
              {head}
              <button className={`qcard ${active === q.id ? 'active' : ''} ${asked.has(q.id) ? 'asked' : ''}`} disabled={busy} onClick={() => { ask(q.id); close() }} style={{ '--ac': `var(--${CAT[q.cat].accent})` }}>
                <span className={`q-ico ${CAT[q.cat].accent}`}><Icon name={q.icon} size={19} /></span>
                <span className="q-body">
                  <span className="q-title"><Hl text={q.q} term={term.trim()} />{q.badge && <i className={`badge ${BADGE[q.badge]}`}>{q.badge}</i>}</span>
                  <span className="q-desc">{q.kind} · {q.src.slice(0, 2).join(', ').replace(/_/g, ' ')}</span>
                </span>
                {asked.has(q.id) ? <Icon name="CheckCircle2" size={17} className="q-go ok" /> : <Icon name="ArrowRight" size={17} className="q-go" />}
              </button>
            </React.Fragment>)
        })}
      </div>
    </aside>
  )
}

function Typing({ q }) {
  return (
    <div className="msg bot"><div className="avatar bot"><Icon name="Bot" size={20} /></div>
      <div className="typing"><span className="dots"><i /><i /><i /></span><span>Analysing <b>{q.src[0].replace(/_/g, ' ')}</b> and building your chart…</span></div></div>
  )
}

function Stat({ n, label, icon }) { const v = useCountUp(n, { duration: 1400 }); return <div className="hero-stat"><Icon name={icon} size={18} /><b>{Math.round(v)}</b><span>{label}</span></div> }
function Welcome({ ask }) {
  const picks = [1, 4, 25, 49, 84, 96].map((id) => QBY[id])
  return (
    <div className="welcome">
      <div className="hero">
        <div className="hero-orb"><Icon name="Bot" size={38} /></div>
        <h1>Hi, I’m <span className="grad">BI Bot</span></h1>
        <p>Your HR analytics copilot. Pick any question from the library and I’ll answer it with a chart, key numbers and a plain-English explanation.</p>
        <div className="hero-stats"><Stat n={QS.length} label="Questions" icon="MessageSquare" /><Stat n={CATS.length} label="Categories" icon="Layers" /><Stat n={34} label="Data tables" icon="Database" /></div>
      </div>
      <div className="try-title"><Icon name="Sparkles" size={15} />Try one of these</div>
      <div className="try-grid">
        {picks.map((q, i) => (
          <button key={q.id} className="try-card" onClick={() => ask(q.id)} style={{ animationDelay: `${i * 70}ms`, '--ac': `var(--${CAT[q.cat].accent})` }}>
            <span className={`q-ico ${CAT[q.cat].accent}`}><Icon name={q.icon} size={20} /></span>
            <span><b>{q.q}</b><small>{CAT[q.cat].name} · {q.kind}</small></span><Icon name="ArrowUpRight" size={17} className="q-go" />
          </button>))}
      </div>
    </div>
  )
}

export default function Copilot({ messages, ask, clear, asked, busy, active, drawer, setDrawer, refreshKey }) {
  const chat = useRef(null)
  useEffect(() => {
    const el = chat.current; if (!el || !messages.length) return
    const lastUser = [...el.querySelectorAll('[data-user]')].pop()
    requestAnimationFrame(() => lastUser && el.scrollTo({ top: lastUser.offsetTop - 18, behavior: 'smooth' }))
  }, [messages.length])
  const suggestions = useMemo(() => {
    const lastQ = active ? QBY[active] : null
    const pool = lastQ ? QS.filter((q) => q.cat === lastQ.cat && !asked.has(q.id)).concat(QS.filter((q) => q.cat !== lastQ.cat && q.badge && !asked.has(q.id))) : QS.filter((q) => q.badge === 'Popular')
    return pool.slice(0, 8)
  }, [active, asked])
  return (
    <div className="copilot">
      <Sidebar ask={ask} asked={asked} active={active} busy={busy} open={drawer} close={() => setDrawer(false)} />
      {drawer && <div className="scrim" onClick={() => setDrawer(false)} />}
      <section className="chat">
        <button className="fab only-mobile" onClick={() => setDrawer(true)}><Icon name="MessageSquare" size={18} />Questions</button>
        <div className="chat-scroll" ref={chat} key={refreshKey}>
          <div className="chat-inner">
            {messages.length === 0 && <Welcome ask={ask} />}
            {messages.map((m) => m.role === 'user'
              ? <div className="msg user" key={m.id} data-user><div className="bubble"><div className="bubble-top"><span>You</span><span>{m.time}</span></div><p>{QBY[m.qid].q}</p></div><div className="avatar user"><Icon name="MousePointerClick" size={18} /></div></div>
              : m.typing ? <Typing key={m.id} q={QBY[m.qid]} />
              : <div className="msg bot" key={m.id}><div className="avatar bot"><Icon name="Bot" size={20} /></div><Answer q={QBY[m.qid]} time={m.time} /></div>)}
          </div>
        </div>
        <div className="composer">
          <div className="suggest"><span className="suggest-title"><Icon name="Lightbulb" size={14} />{active ? 'Ask next' : 'Suggested questions'}</span>
            <div className="chips">{suggestions.map((q) => <button key={q.id} className="chip-q" disabled={busy} onClick={() => ask(q.id)}><Icon name="Sparkles" size={13} />{q.q}</button>)}</div></div>
          <div className="input-row">
            <div className="input-fake" aria-disabled="true"><Icon name="Lock" size={15} /><input disabled placeholder="Select a question from the Question Library to analyze…" /></div>
            <button className="send" disabled aria-label="Send"><Icon name="Send" size={18} /></button>
            <button className="trash" onClick={clear} disabled={!messages.length} title="Clear chat" aria-label="Clear chat"><Icon name="Trash2" size={18} /></button>
          </div>
        </div>
      </section>
    </div>
  )
}
