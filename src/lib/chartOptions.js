import * as echarts from 'echarts/core'
import { fmtVal, axisFmt } from './format.jsx'
import { mix, alpha } from './chartTheme.js'

const FONT = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif'
const LG = (x0, y0, x1, y1, a, b) => new echarts.graphic.LinearGradient(x0, y0, x1, y1, [{ offset: 0, color: a }, { offset: 1, color: b }])
const vGrad = (c) => LG(0, 0, 0, 1, mix(c, 0.22), c)   // top light → bottom base
const hGrad = (c) => LG(0, 0, 1, 0, c, mix(c, 0.26))   // left base → right light
const colorOf = (item, i, T) => (item && item.tone && T.tones[item.tone]) || T.palette[i % T.palette.length]

function tooltipBase(T) {
  return { backgroundColor: T.tipBg, borderColor: T.tipBorder, borderWidth: 1, padding: [10, 14], textStyle: { color: T.strong, fontFamily: FONT, fontSize: 13 },
    extraCssText: 'border-radius:14px;box-shadow:0 18px 40px -12px rgba(15,35,110,.35);backdrop-filter:blur(10px);', confine: true }
}
const dot = (c) => `<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:${c};margin-right:8px;box-shadow:0 0 0 3px ${alpha(c, 0.18)}"></span>`

// ───────────────────────── cartesian (bar / hbar / line / area / combo)
function cartesian(spec, T, o) {
  const horiz = spec.type === 'hbar' || spec.orient === 'h'
  const defKind = spec.type === 'line' || spec.type === 'area' ? 'line' : 'bar'
  const cats = spec.categories
  const multi = spec.series.length > 1
  const hasAx1 = spec.series.some((s) => s.axis === 1)
  const stacked = !!spec.stacked
  const compact = o.compact
  const cols = spec.series.map((s, i) => colorOf(s, i, T))
  const maxVal = Math.max(...spec.series[0].data)

  const series = spec.series.map((s, i) => {
    const kind = s.kind || defKind, c = cols[i], sf = s.fmt || spec.fmt
    if (kind === 'line') {
      const area = spec.type === 'area'
      return {
        type: 'line', name: s.name, data: s.data, yAxisIndex: s.axis || 0, smooth: spec.smooth !== false, stack: stacked && area ? 'total' : undefined,
        symbol: 'circle', symbolSize: 8, showSymbol: s.data.length <= 24, z: 5,
        lineStyle: { width: compact ? 2.5 : 3.5, color: c, shadowColor: alpha(c, 0.45), shadowBlur: 14, shadowOffsetY: 6 },
        itemStyle: { color: c, borderColor: T.card, borderWidth: 2 },
        areaStyle: area ? { color: LG(0, 0, 0, 1, alpha(c, stacked ? 0.75 : 0.42), alpha(c, stacked ? 0.18 : 0.02)) } : undefined,
        emphasis: { focus: 'series', lineStyle: { width: 4.5 } },
        animationDuration: 1400, animationEasing: 'cubicOut',
      }
    }
    const pts = s.data.map((v, k) => {
      let col = c
      if (spec.pointTones) col = T.tones[spec.pointTones[k]] || c
      else if (spec.rank && multi === false) col = spec.tone ? T.tones[spec.tone] : v === maxVal ? T.tones.gold : c
      return { value: v, itemStyle: { color: horiz ? hGrad(col) : vGrad(col), shadowColor: alpha(col, 0.35), shadowBlur: stacked ? 0 : 10, shadowOffsetY: horiz ? 0 : 4 } }
    })
    const stackKey = stacked ? 'total' : s.stack
    const lastOfStack = !stacked || i === spec.series.length - 1
    return {
      type: 'bar', name: s.name, data: pts, yAxisIndex: s.axis || 0, stack: stackKey, z: 3,
      barMaxWidth: horiz ? (compact ? 16 : 24) : (compact ? 30 : 44), barGap: '12%',
      itemStyle: { borderRadius: stackKey ? 3 : horiz ? [0, 9, 9, 0] : [9, 9, 0, 0], borderColor: stackKey ? T.card : undefined, borderWidth: stackKey ? 1.5 : 0, color: horiz ? hGrad(c) : vGrad(c) },
      label: !stackKey && !compact && (horiz || cats.length <= 12) && !hasAx1 ? { show: true, position: horiz ? 'right' : 'top', color: T.text, fontFamily: FONT, fontWeight: 600, fontSize: 12, distance: 8, formatter: (p) => axisFmt(p.value, sf) === '–' ? '' : fmtVal(p.value, sf).replace(/ (days|min)$/, '') } : { show: false },
      emphasis: { focus: 'series', itemStyle: { shadowBlur: 22, shadowColor: alpha(c, 0.6) } },
      animationDelay: (idx) => idx * 55 + i * 90, animationDuration: 900, animationEasing: 'cubicOut',
    }
  })

  const valAxis = (idx) => {
    const ss = spec.series.filter((s) => (s.axis || 0) === idx); const f = (ss[0] && ss[0].fmt) || spec.fmt
    return { type: 'value', position: horiz ? 'bottom' : idx ? 'right' : 'left', max: spec.max, min: 0, name: !compact && spec.yNames ? spec.yNames[idx] : undefined,
      nameTextStyle: { color: T.muted, fontFamily: FONT, fontSize: 11, align: idx ? 'right' : 'left' }, axisLine: { show: false }, axisTick: { show: false },
      splitLine: { show: idx === 0, lineStyle: { color: T.grid, type: [4, 5] } }, axisLabel: { color: T.muted, fontFamily: FONT, fontSize: 11, formatter: (v) => axisFmt(v, f) } }
  }
  const catAxis = { type: 'category', data: cats, boundaryGap: spec.type === 'area' || (defKind === 'line' && !spec.series.some((s) => s.kind === 'bar')) ? false : true,
    axisLine: { lineStyle: { color: T.grid } }, axisTick: { show: false }, inverse: false,
    axisLabel: { color: T.text, fontFamily: FONT, fontSize: compact ? 10.5 : 12, margin: 12,
      ...(horiz ? { interval: 0, width: compact ? 110 : 170, overflow: 'truncate' }
        : cats.length <= 12 ? { interval: 0, hideOverlap: false, width: compact ? Math.max(48, 330 / cats.length) : Math.max(70, 880 / cats.length - 10), overflow: 'break', lineHeight: 15, rotate: 0 }
        : { interval: 'auto', hideOverlap: true, rotate: cats.some((c) => String(c).length > 6) && cats.length <= 30 ? 28 : 0 }) } }

  return {
    animation: o.animate !== false, textStyle: { fontFamily: FONT },
    color: cols,
    legend: multi ? { top: 0, left: 'center', icon: 'roundRect', itemWidth: 14, itemHeight: 8, itemGap: compact ? 12 : 22, textStyle: { color: T.text, fontFamily: FONT, fontSize: compact ? 11 : 12.5 }, inactiveColor: T.muted } : undefined,
    grid: { left: 8, right: hasAx1 ? 10 : horiz ? 56 : 12, top: multi ? (compact ? 38 : 52) : (spec.yNames ? 36 : 22), bottom: 6, containLabel: true },
    tooltip: { ...tooltipBase(T), trigger: 'axis', axisPointer: { type: horiz || defKind === 'bar' ? 'shadow' : 'line', shadowStyle: { color: alpha(cols[0], 0.07) }, lineStyle: { color: alpha(cols[0], 0.5), width: 2 } },
      formatter: (ps) => {
        ps = Array.isArray(ps) ? ps : [ps]
        const rows = ps.map((p) => { const s = spec.series[p.seriesIndex]; const v = typeof p.value === 'object' && p.value !== null ? p.value.value ?? p.data.value : p.value
          return `<div style="display:flex;justify-content:space-between;gap:22px;margin-top:5px"><span>${dot(cols[p.seriesIndex])}${p.seriesName}</span><b>${fmtVal(v, s.fmt || spec.fmt)}</b></div>` }).join('')
        const tot = stacked && ps.length > 1 && !spec.percent ? `<div style="display:flex;justify-content:space-between;margin-top:8px;padding-top:7px;border-top:1px solid ${T.grid}"><span style="color:${T.muted}">Total</span><b>${fmtVal(ps.reduce((a, p) => a + (+p.value || +(p.data && p.data.value) || 0), 0), spec.fmt)}</b></div>` : ''
        return `<div style="min-width:170px"><div style="font-weight:700;margin-bottom:2px">${ps[0].axisValueLabel}</div>${rows}${tot}</div>` } },
    xAxis: horiz ? valAxis(0) : catAxis,
    yAxis: horiz ? { ...catAxis, boundaryGap: true } : (hasAx1 ? [valAxis(0), valAxis(1)] : valAxis(0)),
    series,
  }
}

// ───────────────────────── donut
function donut(spec, T, o) {
  const items = spec.items
  return {
    animation: o.animate !== false, color: items.map((it, i) => colorOf(it, i, T)),
    tooltip: { ...tooltipBase(T), trigger: 'item', formatter: (p) => `<div>${dot(p.color)}<b>${p.name}</b><div style="margin-top:4px">${fmtVal(p.value, spec.fmt)} · <b>${p.percent}%</b></div></div>` },
    series: [{
      type: 'pie', radius: ['62%', '86%'], center: ['50%', '50%'], padAngle: 2.5, startAngle: 100, avoidLabelOverlap: true, selectedMode: false,
      itemStyle: { borderRadius: 12, borderColor: T.card, borderWidth: 3 }, label: { show: false }, labelLine: { show: false },
      emphasis: { scaleSize: 7, itemStyle: { shadowBlur: 28, shadowColor: 'rgba(30,70,200,.45)' } },
      data: items.map((it, i) => { const c = colorOf(it, i, T); return { name: it.name, value: it.value, itemStyle: { color: LG(0, 0, 1, 1, mix(c, 0.28), c) } } }),
      animationType: 'expansion', animationDuration: 1100, animationEasing: 'cubicOut',
    }],
  }
}

// ───────────────────────── gauge
function gauge(spec, T, o) {
  const v = spec.value, max = spec.max || 100, good = v >= 85 ? T.tones.good : v >= 60 ? T.tones.brand : T.tones.warn
  const c1 = '#2F6BFF', c2 = good === T.tones.warn ? '#FFB020' : '#14C8E8'
  return {
    animation: o.animate !== false,
    series: [
      { type: 'gauge', startAngle: 215, endAngle: -35, min: 0, max, radius: '92%', center: ['50%', '58%'], progress: { show: true, width: 22, roundCap: true, itemStyle: { color: LG(0, 0, 1, 0, c1, c2), shadowBlur: 22, shadowColor: alpha(c1, 0.55) } },
        axisLine: { roundCap: true, lineStyle: { width: 22, color: [[1, T.track]] } }, pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
        anchor: { show: false }, title: { show: true, offsetCenter: [0, '38%'], color: T.muted, fontSize: 14, fontFamily: FONT, fontWeight: 600 },
        detail: { valueAnimation: true, offsetCenter: [0, '2%'], fontSize: 46, fontWeight: 800, fontFamily: 'Plus Jakarta Sans, Inter, sans-serif', color: T.strong, formatter: (x) => fmtVal(x, spec.fmt) },
        data: [{ value: v, name: spec.label || '' }], animationDuration: 1600, animationEasing: 'cubicOut' },
      { type: 'gauge', startAngle: 215, endAngle: -35, min: 0, max, radius: '70%', center: ['50%', '58%'], axisLine: { lineStyle: { width: 2, color: [[1, T.grid]] } }, pointer: { show: false }, axisTick: { distance: -2, length: 5, lineStyle: { color: T.muted, width: 1 } }, splitNumber: 5, splitLine: { show: false }, axisLabel: { show: false }, detail: { show: false }, silent: true, data: [] },
    ],
  }
}

// ───────────────────────── funnel
function funnel(spec, T, o) {
  const first = spec.items[0].value
  const seq = ['#2F6BFF', '#4A7FFF', '#14C8E8', '#10D9A0', '#8B5CF6', '#FF4D9D']
  return {
    animation: o.animate !== false,
    tooltip: { ...tooltipBase(T), trigger: 'item', formatter: (p) => `${dot(p.color && p.color.colorStops ? p.color.colorStops[0].color : p.color)}<b>${p.name}</b><div style="margin-top:4px">${fmtVal(p.value, spec.fmt)} · ${((p.value / first) * 100).toFixed(1)}% of the start</div>` },
    series: [{
      type: 'funnel', left: '3%', right: o.compact ? '50%' : '38%', top: 8, bottom: 8, minSize: '10%', maxSize: '100%', gap: 5, sort: 'none',
      label: { show: true, position: 'right', fontFamily: FONT, color: T.text, fontSize: o.compact ? 11.5 : 13.5, lineHeight: 20,
        formatter: (p) => `{n|${p.name}}\n{v|${fmtVal(p.value, spec.fmt)}}  {p|${((p.value / first) * 100).toFixed(p.value / first < 0.1 ? 1 : 0)}%}`,
        rich: { n: { fontWeight: 700, color: T.strong, fontSize: o.compact ? 12 : 14, fontFamily: FONT }, v: { fontWeight: 800, color: T.text, fontSize: o.compact ? 12 : 14, fontFamily: FONT }, p: { color: T.muted, fontSize: 11.5, fontFamily: FONT } } },
      labelLine: { show: true, length: 18, lineStyle: { color: T.grid, width: 1.5, type: 'dashed' } },
      itemStyle: { borderWidth: 0, borderRadius: 6, shadowBlur: 16, shadowColor: 'rgba(30,70,200,.28)' }, emphasis: { itemStyle: { shadowBlur: 28 } },
      data: spec.items.map((it, i) => { const c = seq[i % seq.length]; return { name: it.name, value: it.value, itemStyle: { color: LG(0, 0, 1, 0, c, mix(c, 0.22)) } } }),
      animationDuration: 1100, animationEasing: 'cubicOut',
    }],
  }
}

// ───────────────────────── heatmap
function heatmap(spec, T, o) {
  const vals = spec.data.map((d) => d[2]), mx = Math.max(...vals)
  const range = T.dark ? ['#16204a', '#2F6BFF', '#14C8E8', '#FFB020'] : ['#EAF1FF', '#9DBBFF', '#2F6BFF', '#7B2FF0']
  const showLbl = spec.data.length <= 90
  return {
    animation: o.animate !== false,
    tooltip: { ...tooltipBase(T), trigger: 'item', formatter: (p) => `<b>${spec.ys[p.value[1]]}</b> · ${spec.xs[p.value[0]]}<div style="margin-top:4px">${dot(p.color)}${fmtVal(p.value[2], spec.fmt)}</div>` },
    grid: { left: 4, right: 10, top: 6, bottom: o.compact ? 34 : 44, containLabel: true },
    xAxis: { type: 'category', data: spec.xs, splitArea: { show: false }, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: T.text, fontFamily: FONT, fontSize: 12 } },
    yAxis: { type: 'category', data: spec.ys, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: T.text, fontFamily: FONT, fontSize: 12, width: 130, overflow: 'truncate' } },
    visualMap: { min: 0, max: mx, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 14, itemHeight: o.compact ? 120 : 220, text: ['High', 'Low'], textStyle: { color: T.muted, fontFamily: FONT, fontSize: 11 }, inRange: { color: range } },
    series: [{ type: 'heatmap', data: spec.data, itemStyle: { borderRadius: 7, borderColor: T.card, borderWidth: 3 },
      label: { show: showLbl && !o.compact, fontFamily: FONT, fontWeight: 600, fontSize: 11, formatter: (p) => (p.value[2] ? fmtVal(p.value[2], spec.fmt === 'inr' ? 'inr' : 'int') : ''), color: '#fff', textShadowColor: 'rgba(0,0,0,.35)', textShadowBlur: 3 },
      emphasis: { itemStyle: { shadowBlur: 16, shadowColor: 'rgba(47,107,255,.55)' } }, animationDuration: 900 }],
  }
}

// ───────────────────────── treemap
function treemap(spec, T, o) {
  const data = spec.items.map((it, i) => { const c = T.palette[i % T.palette.length]; return { name: it.name, value: it.value, itemStyle: { color: c, borderColor: T.card, borderWidth: 3, gapWidth: 3, borderRadius: 12, shadowBlur: 14, shadowColor: alpha(c, 0.35) } } })
  return {
    animation: o.animate !== false,
    tooltip: { ...tooltipBase(T), formatter: (p) => `${dot(p.color)}<b>${p.name}</b><div style="margin-top:4px">${fmtVal(p.value, spec.fmt)}</div>` },
    series: [{ type: 'treemap', roam: false, nodeClick: false, breadcrumb: { show: false }, left: 0, right: 0, top: 0, bottom: 0, squareRatio: 1.1,
      label: { show: true, position: 'insideTopLeft', padding: [8, 10], overflow: 'truncate', color: '#fff', fontFamily: FONT, fontWeight: 700, fontSize: o.compact ? 11 : 13,
        formatter: (p) => `{n|${p.name}}\n{v|${fmtVal(p.value, spec.fmt)}}`, rich: { n: { color: '#fff', fontWeight: 700, fontSize: o.compact ? 11 : 13, fontFamily: FONT, textShadowColor: 'rgba(0,0,0,.25)', textShadowBlur: 2 }, v: { color: 'rgba(255,255,255,.88)', fontSize: o.compact ? 10 : 12, fontFamily: FONT, lineHeight: 20 } } },
      itemStyle: { borderRadius: 12 }, emphasis: { itemStyle: { shadowBlur: 24 } }, data, animationDuration: 1000, animationEasing: 'cubicOut' }],
  }
}

// ───────────────────────── sankey
function sankey(spec, T, o) {
  let l = 0, r = 0
  const nodes = spec.nodes.map((n) => { const c = n.side === 'left' ? T.palette[l++ % T.palette.length] : T.palette[(r++ + 3) % T.palette.length]; return { name: n.name, itemStyle: { color: c, borderRadius: 4 }, label: { color: T.text } } })
  return {
    animation: o.animate !== false,
    tooltip: { ...tooltipBase(T), trigger: 'item', formatter: (p) => p.dataType === 'edge' ? `<b>${p.data.source}</b> → <b>${p.data.target}</b><div style="margin-top:4px">${fmtVal(p.data.value, spec.fmt)} candidates</div>` : `<b>${p.name}</b><div style="margin-top:4px">${fmtVal(p.value, spec.fmt)} candidates</div>` },
    series: [{ type: 'sankey', left: 8, right: o.compact ? 110 : 230, top: 10, bottom: 10, nodeWidth: 16, nodeGap: o.compact ? 12 : 22, draggable: false, layoutIterations: 0, emphasis: { focus: 'adjacency' },
      lineStyle: { color: 'gradient', opacity: 0.38, curveness: 0.55 }, label: { fontFamily: FONT, fontSize: o.compact ? 10 : 12, fontWeight: 600, color: T.text, overflow: 'truncate', width: o.compact ? 105 : 220 },
      data: nodes, links: spec.links, animationDuration: 1100 }],
  }
}

export function buildOption(spec, T, o = {}) {
  switch (spec.type) {
    case 'donut': return donut(spec, T, o)
    case 'gauge': return gauge(spec, T, o)
    case 'funnel': return funnel(spec, T, o)
    case 'heatmap': return heatmap(spec, T, o)
    case 'treemap': return treemap(spec, T, o)
    case 'sankey': return sankey(spec, T, o)
    default: return cartesian(spec, T, o)
  }
}

export function sparkOption(data, color, T) {
  return { animation: true, grid: { left: 2, right: 2, top: 4, bottom: 2 }, xAxis: { type: 'category', show: false, boundaryGap: false, data: data.map((_, i) => i) }, yAxis: { type: 'value', show: false, min: 'dataMin' },
    series: [{ type: 'line', data, smooth: true, symbol: 'none', lineStyle: { width: 2.5, color, shadowColor: alpha(color, 0.5), shadowBlur: 8 }, areaStyle: { color: LG(0, 0, 0, 1, alpha(color, 0.38), alpha(color, 0)) }, animationDuration: 1400 }] }
}
