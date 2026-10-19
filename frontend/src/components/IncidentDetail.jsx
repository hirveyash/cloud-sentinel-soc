import { ArrowLeft, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { formatClock } from '../api'
import { PROVIDER_NAMES } from '../providers'
import DecisionHistory from './DecisionHistory'
import DecisionPanel from './DecisionPanel'
import HoldSign from './HoldSign'
import { SeverityTag, StatusTag } from './Tags'

const TAG = 'inline-block border px-2 py-0.5 font-sign text-xs font-bold tracking-[0.08em] whitespace-nowrap uppercase'
const LABEL = 'text-xs font-semibold tracking-[0.1em] text-muted uppercase'

function getJson(path) {
  return fetch(path).then((res) =>
    res.ok ? res.json() : Promise.reject(new Error(res.status === 404 ? 'not-found' : 'error')),
  )
}

// Incident plus its decision history; reload() refetches after a decision.
function useIncident(id) {
  const [state, setState] = useState({ incident: null, decisions: [], error: null })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    Promise.all([getJson(`/api/incidents/${id}`), getJson(`/api/incidents/${id}/decisions`)])
      .then(([incident, decisions]) => !cancelled && setState({ incident, decisions, error: null }))
      .catch((err) => !cancelled && setState((s) => ({ ...s, error: err.message })))
    return () => {
      cancelled = true
    }
  }, [id, version])

  return { ...state, reload: () => setVersion((v) => v + 1) }
}

const BRIEFING_POLL_MS = 2500

// Briefings are generated in the background; poll until the backend says 'ready'.
function useBriefing(id, eventCount) {
  const [state, setState] = useState({ briefing: null, loading: true, error: false })
  const [request, setRequest] = useState({ refresh: false, n: 0 })

  useEffect(() => {
    if (eventCount == null) return
    let cancelled = false
    let timer
    let refresh = request.refresh

    async function poll() {
      try {
        const res = await fetch(`/api/incidents/${id}/briefing${refresh ? '?refresh=true' : ''}`)
        if (!res.ok) throw new Error()
        const { state: s, briefing } = await res.json()
        if (cancelled) return
        refresh = false
        setState({ briefing, loading: s !== 'ready', error: false })
        if (s !== 'ready') timer = setTimeout(poll, BRIEFING_POLL_MS)
      } catch {
        if (!cancelled) setState((prev) => ({ ...prev, loading: false, error: true }))
      }
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [id, eventCount, request])

  const regenerate = () => {
    setState((s) => ({ ...s, loading: true, error: false }))
    setRequest((r) => ({ refresh: true, n: r.n + 1 }))
  }

  return { ...state, regenerate }
}

function Section({ title, children, aside }) {
  return (
    <section className="border-t border-rule pt-4 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-sign text-base font-bold tracking-[0.08em] uppercase">{title}</h3>
        {aside}
      </div>
      <div className="mt-2">{children}</div>
    </section>
  )
}

function Briefing({ state, onRegenerate }) {
  const { briefing, loading, error } = state

  if (!briefing && loading) {
    return (
      <div className="grid min-h-80 place-items-center px-6 text-center">
        <div>
          <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">Generating briefing</p>
          <p className="mt-1 max-w-[42ch] text-muted">
            The local model is reading the evidence. This usually takes 10 to 20 seconds.
          </p>
        </div>
      </div>
    )
  }

  if (!briefing) {
    return (
      <div className="grid min-h-80 place-items-center px-6 text-center">
        <div>
          <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">Briefing unavailable</p>
          <p className="mt-1 max-w-[42ch] text-muted">
            {error ? 'The backend did not return a briefing.' : ''} Check that the API is running, then retry.
          </p>
          <button
            type="button"
            onClick={onRegenerate}
            className="mt-4 border border-sign-yellow px-3 py-1.5 font-sign text-sm font-bold tracking-[0.08em] text-sign-yellow uppercase transition-colors duration-200 ease-sign hover:bg-sign-yellow hover:text-sign-black"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-5 p-4 transition-opacity duration-200 ease-sign sm:p-5 ${loading ? 'opacity-50' : ''}`}>
      <p className="text-base text-ink">{briefing.summary}</p>

      <Section
        title="Why it was flagged"
        aside={
          briefing.technique_id && (
            <span className="text-sm text-muted">
              MITRE ATT&CK {briefing.technique_id} · {briefing.technique_name}
            </span>
          )
        }
      >
        <ul className="space-y-1.5">
          {briefing.why_flagged.map((reason) => (
            <li key={reason} className="flex gap-2.5">
              <span aria-hidden="true" className="mt-2 size-1.5 shrink-0 bg-sign-yellow" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Risk if ignored">
        <p>{briefing.risk_if_ignored}</p>
      </Section>

      <Section
        title="Playbook preview"
        aside={<span className="text-sm text-muted">Nothing runs without an analyst decision</span>}
      >
        <ol className="divide-y divide-rule-soft border border-rule">
          {briefing.playbook.map((step, i) => (
            <li key={step.action} className="flex gap-3 px-3 py-3 sm:px-4">
              <span className="w-5 shrink-0 font-sign text-lg leading-6 font-bold text-muted">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="font-medium text-ink">{step.action}</p>
                  <span
                    className={`${TAG} ${step.reversible ? 'border-rule text-muted' : 'border-sign-yellow text-sign-yellow'}`}
                  >
                    {step.reversible ? 'Reversible' : 'Irreversible'}
                  </span>
                </div>
                <p className="mt-0.5 text-muted">{step.rationale}</p>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-4 text-sm text-muted">
        <p>
          {briefing.generator === 'llm'
            ? `Generated locally by ${briefing.model} · confidence ${briefing.confidence} · ${formatClock(briefing.generated_at)}`
            : 'Rule-based briefing: the local model was unavailable'}
        </p>
        <button
          type="button"
          onClick={onRegenerate}
          disabled={loading}
          className="inline-flex items-center gap-1.5 border border-rule px-2.5 py-1 font-sign text-sm font-bold tracking-[0.08em] text-ink uppercase transition-colors duration-200 ease-sign hover:border-sign-yellow hover:text-sign-yellow disabled:cursor-wait disabled:opacity-60"
        >
          <RefreshCw aria-hidden="true" strokeWidth={2.5} className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Updating' : 'Regenerate'}
        </button>
      </footer>
    </div>
  )
}

function Fact({ term, children }) {
  return (
    <div>
      <dt className={LABEL}>{term}</dt>
      <dd className="mt-0.5">{children}</dd>
    </div>
  )
}

function Panel({ id, title, badge, className = '', children }) {
  return (
    <section aria-labelledby={id} className={`min-w-0 border border-rule ${className}`}>
      <header className="flex flex-wrap items-center gap-3 border-b border-rule bg-asphalt-raised px-4 py-3">
        <h2 id={id} className="font-sign text-lg leading-none font-bold tracking-[0.08em] uppercase">
          {title}
        </h2>
        {badge}
      </header>
      {children}
    </section>
  )
}

export default function IncidentDetail({ id }) {
  const { incident, decisions, error, reload } = useIncident(id)
  const briefing = useBriefing(id, incident?.event_count)

  const back = (
    <a
      href="#/"
      className="inline-flex items-center gap-1.5 text-sm font-semibold tracking-[0.08em] text-muted uppercase transition-colors duration-200 ease-sign hover:text-sign-yellow"
    >
      <ArrowLeft aria-hidden="true" strokeWidth={2.5} className="size-4" />
      Dashboard
    </a>
  )

  if (!incident) {
    return (
      <div>
        {back}
        <div className="mt-6 grid min-h-80 place-items-center border border-rule px-6 text-center">
          <div>
            <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">
              {error === 'not-found' ? 'Incident not found' : error ? 'Backend unreachable' : 'Loading incident'}
            </p>
            {error === 'not-found' && (
              <p className="mt-1 text-muted">It may have been cleared by a reset.</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  const target = incident.correlation_key.slice(incident.correlation_key.indexOf(':') + 1)

  return (
    <div>
      {back}

      <header className="mt-4 border-b border-rule pb-5">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityTag severity={incident.severity} />
          <StatusTag status={incident.status} />
        </div>
        <h1 className="mt-3 font-sign text-[clamp(1.5rem,2.4vw,2.25rem)] leading-tight font-bold tracking-[0.02em]">
          {incident.title}
        </h1>
        <dl className="mt-4 grid grid-cols-2 gap-x-8 gap-y-3 text-sm sm:flex sm:flex-wrap">
          <Fact term="Clouds">{incident.providers.map((p) => PROVIDER_NAMES[p]).join(' + ')}</Fact>
          <Fact term={incident.correlation_key.startsWith('ip:') ? 'Source IP' : 'Resource'}>
            <span className="break-all">{target}</span>
          </Fact>
          <Fact term="Events">{incident.event_count}</Fact>
          <Fact term="First seen">{formatClock(incident.first_seen)}</Fact>
          <Fact term="Last seen">{formatClock(incident.last_seen)}</Fact>
        </dl>
      </header>

      {/* Wide screens: read on the left, decide on the right (sticky). Narrow screens flatten
          the columns so the decision follows the briefing instead of trailing the evidence. */}
      <div className="mt-6 grid items-start gap-5 xl:grid-cols-[1.4fr_1fr]">
        <div className="contents xl:grid xl:min-w-0 xl:gap-5">
          <Panel id="briefing-title" title="Analyst briefing" className="order-1">
            <Briefing state={briefing} onRegenerate={briefing.regenerate} />
          </Panel>

          <Panel id="evidence-title" title={`Evidence · ${incident.events.length}`} className="order-4">
            <ol className="divide-y divide-rule-soft">
              {incident.events.map((e) => (
                <li key={e.id} className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                    <span className="text-muted">{formatClock(e.observed_at)}</span>
                    <span>{PROVIDER_NAMES[e.provider]}</span>
                    <span className="text-muted">{e.source}</span>
                    <SeverityTag severity={e.severity} />
                  </div>
                  <p className="mt-1 font-medium text-ink">{e.title}</p>
                  <p className="mt-0.5 text-sm text-muted">{e.description}</p>
                  <p className="mt-1 text-xs break-all text-muted">{e.resource}</p>
                </li>
              ))}
            </ol>
          </Panel>
        </div>

        <div className="contents xl:sticky xl:top-6 xl:grid xl:min-w-0 xl:gap-5">
          <Panel
            id="decision-title"
            title="Analyst decision"
            className="order-2"
            badge={incident.status === 'new' && <HoldSign awaiting={1} label="Awaiting clearance" />}
          >
            <DecisionPanel incident={incident} onDecided={reload} />
          </Panel>

          <Panel id="history-title" title="Decision history" className="order-3">
            <DecisionHistory decisions={decisions} />
          </Panel>
        </div>
      </div>
    </div>
  )
}
