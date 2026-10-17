import { useEffect, useState } from 'react'

/**
 * Cuenta regresiva en segundos. `start(n)` la reinicia; devuelve los segundos
 * que faltan (0 cuando terminó).
 */
export function useCountdown() {
  const [until, setUntil] = useState(0)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!until) return undefined
    const timer = window.setInterval(() => {
      const current = Date.now()
      setNow(current)
      if (current >= until) window.clearInterval(timer)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [until])

  const remaining = until ? Math.max(0, Math.ceil((until - now) / 1000)) : 0

  function start(seconds) {
    const current = Date.now()
    setNow(current)
    setUntil(seconds > 0 ? current + seconds * 1000 : 0)
  }

  return [remaining, start]
}
