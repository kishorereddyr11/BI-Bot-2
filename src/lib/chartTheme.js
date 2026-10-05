// Infinyty-inspired palette: royal blue, cyan, violet, magenta, gold, emerald
export const PALETTE = ['#2F6BFF', '#14C8E8', '#8B5CF6', '#FF4D9D', '#FFB020', '#10D9A0', '#FF7A3D', '#6C7BFF', '#2DD4BF', '#F43F5E']
export const TONES = { good: '#10D9A0', bad: '#FF4D6D', warn: '#FFB020', neutral: '#8A97B8', brand: '#2F6BFF', accent: '#8B5CF6', gold: '#FFB020' }

export function mix(hex, t, to = '#ffffff') {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
  const a = p(hex), b = p(to)
  return '#' + a.map((v, i) => Math.round(v + (b[i] - v) * t).toString(16).padStart(2, '0')).join('')
}
export const alpha = (hex, a) => hex + Math.round(a * 255).toString(16).padStart(2, '0')

export function chartTheme(dark) {
  return {
    dark,
    text: dark ? '#C9D4F5' : '#33415F',
    strong: dark ? '#F1F5FF' : '#0B1B4D',
    muted: dark ? '#7F8DB8' : '#7A87A6',
    grid: dark ? 'rgba(255,255,255,0.07)' : 'rgba(30,64,175,0.09)',
    card: dark ? '#0E1634' : '#FFFFFF',
    tipBg: dark ? 'rgba(12,19,50,0.96)' : 'rgba(255,255,255,0.97)',
    tipBorder: dark ? 'rgba(120,150,255,0.25)' : 'rgba(47,107,255,0.18)',
    track: dark ? 'rgba(255,255,255,0.07)' : '#E8EEFB',
    palette: PALETTE,
    tones: TONES,
  }
}
