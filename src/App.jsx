import React, { useCallback, useMemo, useRef, useState } from 'react'
import { ThemeProvider } from './theme.jsx'
import Header from './components/Header.jsx'
import Copilot from './components/Copilot.jsx'
import Dashboard from './components/Dashboard.jsx'
import Dataset from './components/Dataset.jsx'
import { nowTime } from './lib/format.jsx'

function Shell() {
  const [tab, setTab] = useState('copilot'); const [messages, setMessages] = useState([]); const [drawer, setDrawer] = useState(false)
  const [spin, setSpin] = useState(false); const [rk, setRk] = useState({ copilot: 0, dashboard: 0, dataset: 0 }); const seq = useRef(0); const timer = useRef(null)
  const busy = messages.some((m) => m.typing)
  const asked = useMemo(() => new Set(messages.filter((m) => m.role === 'user').map((m) => m.qid)), [messages])
  const active = useMemo(() => [...messages].reverse().find((m) => m.role === 'user')?.qid, [messages])

  const ask = useCallback((qid) => {
    if (timer.current) return
    const id = ++seq.current, time = nowTime()
    setMessages((m) => [...m, { id: 'u' + id, role: 'user', qid, time }, { id: 'b' + id, role: 'bot', qid, typing: true, time }])
    timer.current = setTimeout(() => { timer.current = null; setMessages((m) => m.map((x) => (x.id === 'b' + id ? { ...x, typing: false, time: nowTime() } : x))) }, 1100 + Math.random() * 500)
  }, [])
  const clear = useCallback(() => { clearTimeout(timer.current); timer.current = null; setMessages([]) }, [])
  const openQuestion = useCallback((qid) => { setTab('copilot'); setTimeout(() => ask(qid), 250) }, [ask])
  const refresh = () => { setRk((r) => ({ ...r, [tab]: r[tab] + 1 })); setSpin(true); setTimeout(() => setSpin(false), 800) }

  return (
    <div className="app">
      <div className="bg-orbs" aria-hidden="true"><i /><i /><i /></div>
      <Header tab={tab} setTab={setTab} onRefresh={refresh} spinning={spin} />
      <main className="main">
        {tab === 'copilot' && <Copilot messages={messages} ask={ask} clear={clear} asked={asked} busy={busy} active={active} drawer={drawer} setDrawer={setDrawer} refreshKey={rk.copilot} />}
        {tab === 'dashboard' && <Dashboard openQuestion={openQuestion} refreshKey={rk.dashboard} />}
        {tab === 'dataset' && <Dataset refreshKey={rk.dataset} />}
      </main>
    </div>
  )
}
export default function App() { return <ThemeProvider><Shell /></ThemeProvider> }
