import React, { useRef, useLayoutEffect, useState } from 'react'
import { useTheme } from '../theme.jsx'
import Icon from '../icons.jsx'

const TABS = [['copilot', 'Copilot', 'Bot'], ['dashboard', 'Dashboard', 'BarChart3'], ['dataset', 'Dataset', 'Database']]

export function Logo() {
  const [src, setSrc] = useState('/logo.png')
  return <img className="logo-img" src={src} alt="Infinyty" onError={() => src !== '/logo.webp' && setSrc('/logo.webp')} draggable="false" />
}

export default function Header({ tab, setTab, onRefresh, spinning }) {
  const { dark, toggle } = useTheme()
  const wrap = useRef(null), [pill, setPill] = useState({ left: 0, width: 0 })
  useLayoutEffect(() => {
    const el = wrap.current?.querySelector(`[data-tab="${tab}"]`); if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth })
    const f = () => { const e = wrap.current?.querySelector(`[data-tab="${tab}"]`); if (e) setPill({ left: e.offsetLeft, width: e.offsetWidth }) }
    window.addEventListener('resize', f); return () => window.removeEventListener('resize', f)
  }, [tab])
  return (
    <header className="header">
      <div className="brand">
        <div className="logo-box"><Logo /></div>
        <span className="brand-sep" />
        <div className="brand-text">
          <div className="brand-title">BI Bot</div>
          <div className="brand-sub">Conversational Analytics &amp; Data Visualization</div>
        </div>
        <div className="demo-pill" title="This app runs on dummy HR data for demonstration"><span className="demo-dot" />Demo Mode</div>
      </div>
      <div className="header-right">
        <nav className="tabs" ref={wrap}>
          <span className="tab-pill" style={{ transform: `translateX(${pill.left}px)`, width: pill.width }} />
          {TABS.map(([id, label, icon]) => (
            <button key={id} data-tab={id} className={`tab ${tab === id ? 'on' : ''}`} onClick={() => setTab(id)}><Icon name={icon} size={16} /><span>{label}</span></button>
          ))}
        </nav>
        <button className="icon-btn" onClick={onRefresh} title="Replay animations" aria-label="Refresh"><Icon name="RefreshCw" size={18} className={spinning ? 'spin' : ''} /></button>
        <button className="icon-btn" onClick={toggle} title="Toggle theme" aria-label="Toggle theme"><span className={`theme-ico ${dark ? 'is-dark' : ''}`}><Icon name="Moon" size={18} /><Icon name="Sun" size={18} /></span></button>
      </div>
    </header>
  )
}
