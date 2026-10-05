import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { chartTheme } from './lib/chartTheme.js'

const Ctx = createContext(null)
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'light')
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('bibot-theme', theme) } catch (e) { /* ignore */ }
  }, [theme])
  const value = useMemo(() => ({ theme, dark: theme === 'dark', T: chartTheme(theme === 'dark'), toggle: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) }), [theme])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
export const useTheme = () => useContext(Ctx)
