import { useEffect, useState } from 'react'
import { formatClock, useDashboard } from './api'
import AuditLog from './components/AuditLog'
import DataPanel from './components/DataPanel'
import EventRows from './components/EventRows'
import HoldSign from './components/HoldSign'
import IncidentDetail from './components/IncidentDetail'
import IncidentRows from './components/IncidentRows'
import ProviderGrid from './components/ProviderGrid'
import SignArray from './components/SignArray'
import { PROVIDERS } from './providers'

const zoneName =
  new Intl.DateTimeFormat(undefined, { timeZoneName: 'short' })
    .formatToParts(new Date())
    .find((part) => part.type === 'timeZoneName')?.value ?? ''

// Minimal hash routing: '#/' dashboard, '#/incidents/<id>' an incident, '#/audit' the audit log.
function readRoute() {
  const hash = window.location.hash
  const incident = hash.match(/^#\/incidents\/([\w-]+)$/)?.[1]
  if (incident) return { view: 'incident', id: incident }
  if (hash === '#/audit') return { view: 'audit' }
  return { view: 'dashboard' }
}

function useRoute() {
  const [route, setRoute] = useState(readRoute)

  useEffect(() => {
    const onChange = () => {
      setRoute(readRoute())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  return route
}

const NAV = [
  { href: '#/', label: 'Dashboard', view: 'dashboard' },
  { href: '#/audit', label: 'Audit log', view: 'audit' },
]

function App() {
  const route = useRoute()
  const { status, checkedAt, summary, incidents, events } = useDashboard()

  return (
    <div className="min-h-screen">
      <header className="border-b border-rule">
        <div className="mx-auto flex h-13 max-w-400 items-center gap-4 px-4 sm:gap-6 sm:px-8">
          <p className="font-sign text-lg font-bold tracking-[0.06em] whitespace-nowrap uppercase">
            Cloud <span className="text-sign-yellow">Sentinel</span>
            <span className="ml-2 hidden text-sm font-semibold text-muted sm:inline">v2.0</span>
          </p>
          <nav aria-label="Primary" className="flex gap-4 self-stretch sm:gap-6">
            {NAV.map((item) => {
              const current = route.view === item.view
              return (
                <a
                  key={item.view}
                  href={item.href}
                  aria-current={current ? 'page' : undefined}
                  className={`flex items-center text-sm font-semibold tracking-[0.08em] whitespace-nowrap uppercase transition-colors duration-200 ease-sign hover:text-sign-yellow ${
                    current ? 'shadow-[inset_0_-2px_0_var(--color-sign-yellow)]' : 'text-muted'
                  }`}
                >
                  {item.label}
                </a>
              )
            })}
          </nav>
          <p className="ml-auto hidden text-sm whitespace-nowrap text-muted sm:block">
            {checkedAt ? (
              <>
                <span className="hidden sm:inline">Checked </span>
                {formatClock(checkedAt)} {zoneName}
              </>
            ) : (
              'Checking…'
            )}
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-400 px-4 py-6 sm:px-8 sm:py-7">
        {route.view === 'incident' && <IncidentDetail key={route.id} id={route.id} />}
        {route.view === 'audit' && <AuditLog />}
        {route.view === 'dashboard' && (
          <Dashboard status={status} summary={summary} incidents={incidents} events={events} />
        )}
      </main>
    </div>
  )
}

function Dashboard({ status, summary, incidents, events }) {
  const live = status === 'operational'

  // Counts from an unreachable backend would be invented, so show them as unknown.
  const providers = live ? summary.providers : null
  const counts = providers && Object.fromEntries(PROVIDERS.map((p) => [p.id, providers[p.id].events_24h]))
  const connected = providers ? PROVIDERS.filter((p) => providers[p.id].connected).length : 0

  return (
    <>
      <h1 className="sr-only">Cloud Sentinel dashboard</h1>

      <SignArray status={status} counts={counts} connected={connected} awaiting={summary?.awaiting_clearance} />
      <div aria-hidden="true" className="hold-line my-6" />
      <ProviderGrid providers={providers} />

      <div className="mt-6 grid gap-5 xl:grid-cols-[1.25fr_1fr]">
        <DataPanel
          id="incidents-title"
          title="Live incidents"
          badge={<HoldSign awaiting={live ? summary.awaiting_clearance : null} />}
          columns={['Severity', 'Incident', 'Provider', 'Status']}
          isEmpty={incidents.length === 0}
          emptyTitle="No incidents on the field"
          emptyBody="New incidents hold here until an analyst investigates, keeps open, or resolves them."
          stale={!live}
        >
          <IncidentRows incidents={incidents} />
        </DataPanel>
        <DataPanel
          id="events-title"
          title="Security events"
          columns={['Time', 'Event', 'Provider', 'Source']}
          isEmpty={events.length === 0}
          emptyTitle="No events received"
          emptyBody="Findings from AWS, GCP and Azure appear here as they are polled."
          stale={!live}
        >
          <EventRows events={events} />
        </DataPanel>
      </div>
    </>
  )
}

export default App
