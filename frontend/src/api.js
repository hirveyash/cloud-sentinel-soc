import { useEffect, useState } from 'react'

const POLL_INTERVAL_MS = 5000

async function getJson(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`)
  return res.json()
}

// Polls the backend; status is 'checking' until the first answer, then 'operational' or 'offline'.
export function useDashboard() {
  const [state, setState] = useState({
    status: 'checking',
    checkedAt: null,
    summary: null,
    incidents: [],
    events: [],
  })

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const [summary, incidents, events] = await Promise.all([
          getJson('/api/summary'),
          getJson('/api/incidents'),
          getJson('/api/events?limit=50'),
        ])
        if (!cancelled) {
          setState({ status: 'operational', checkedAt: new Date(), summary, incidents, events })
        }
      } catch {
        // Keep the last rows on screen but stop vouching for them.
        if (!cancelled) setState((s) => ({ ...s, status: 'offline', checkedAt: new Date(), summary: null }))
      }
    }

    poll()
    const timer = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  return state
}

const clockFormat = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

export function formatClock(value) {
  return clockFormat.format(typeof value === 'string' ? new Date(value) : value)
}
