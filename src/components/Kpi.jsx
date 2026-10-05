import React, { useEffect, useRef, useState } from 'react'
import { fmtKpi } from '../lib/format.jsx'
import Icon from '../icons.jsx'

export function useCountUp(target, { duration = 1100, enabled = true } = {}) {
  const [v, setV] = useState(enabled ? 0 : target)
  useEffect(() => {
    if (!enabled || typeof target !== 'number') { setV(target); return }
    let raf, t0
    const step = (t) => { t0 = t0 || t; const p = Math.min(1, (t - t0) / duration); const e = 1 - Math.pow(1 - p, 3); setV(target * e); if (p < 1) raf = requestAnimationFrame(step) }
    raf = requestAnimationFrame(step); return () => cancelAnimationFrame(raf)
  }, [target, enabled])
  return v
}

/** small KPI tile used inside chat answers */
export function KpiTile({ k, i = 0 }) {
  const v = useCountUp(k.num, { enabled: k.fmt !== 'text' })
  const shown = k.fmt === 'text' ? k.num : (k.fmt === 'int' ? Math.round(v) : v)
  return (
    <div className={`kpi-tile ${k.tone || ''}`} style={{ animationDelay: `${i * 90}ms` }}>
      <div className="kpi-label">{k.label}</div>
      <div className="kpi-value">{fmtKpi(shown, k.fmt)}</div>
      {k.sub && (
        <div className="kpi-sub">
          {k.tone === 'up' && <Icon name="TrendingUp" size={13} />}
          {k.tone === 'down' && <Icon name="TrendingDown" size={13} />}
          <span>{k.sub}</span>
        </div>
      )}
    </div>
  )
}
