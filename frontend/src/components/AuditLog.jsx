import { useEffect, useState } from 'react'
import { formatClock } from '../api'
import { ACTION_LABELS, adviceLabel } from '../decisions'
import { StatusTag } from './Tags'

const dateFormat = new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: '2-digit' })

export default function AuditLog() {
  const [state, setState] = useState({ decisions: null, error: false })

  useEffect(() => {
    let cancelled = false
    fetch('/api/audit')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error())))
      .then((decisions) => !cancelled && setState({ decisions, error: false }))
      .catch(() => !cancelled && setState({ decisions: null, error: true }))
    return () => {
      cancelled = true
    }
  }, [])

  const { decisions, error } = state

  return (
    <div>
      <header className="border-b border-rule pb-5">
        <h1 className="font-sign text-[clamp(1.5rem,2.4vw,2.25rem)] leading-tight font-bold tracking-[0.02em] uppercase">
          Audit log
        </h1>
        <p className="mt-1 max-w-[70ch] text-muted">
          Every analyst decision, newest first. Entries are append-only: the database rejects edits, so this is the
          complete record of who changed what, why, and which briefing they had in front of them.
        </p>
      </header>

      <section aria-label="Decisions" className="mt-6 border border-rule">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm md:min-w-[56rem]">
            <thead className="bg-asphalt-raised">
              <tr className="border-b border-rule">
                {['Time', 'Analyst', 'Decision', 'Incident', 'Comment'].map((c) => (
                  <th
                    key={c}
                    scope="col"
                    className="px-3 py-2.5 text-xs font-semibold tracking-[0.1em] whitespace-nowrap text-muted uppercase sm:px-4"
                  >
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {decisions?.map((d) => (
                <tr key={d.id} className="border-b border-rule-soft align-top last:border-b-0">
                  <td className="px-3 py-3 whitespace-nowrap text-muted sm:px-4" title={d.decided_at}>
                    {formatClock(d.decided_at)}
                    <span className="block text-xs">{dateFormat.format(new Date(d.decided_at))}</span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap sm:px-4">{d.analyst}</td>
                  <td className="px-3 py-3 sm:px-4">
                    <p className="font-sign font-bold tracking-[0.06em] uppercase">{ACTION_LABELS[d.action]}</p>
                    <p className="mt-1 flex flex-wrap gap-1">
                      <StatusTag status={d.from_status} />
                      <StatusTag status={d.to_status} />
                    </p>
                  </td>
                  <td className="px-3 py-3 sm:px-4">
                    <a
                      href={`#/incidents/${d.incident_id}`}
                      className="underline decoration-rule underline-offset-4 transition-colors duration-200 ease-sign hover:text-sign-yellow hover:decoration-sign-yellow"
                    >
                      {d.incident_title}
                    </a>
                  </td>
                  <td className="max-w-[48ch] px-3 py-3 sm:px-4">
                    <p className="whitespace-pre-line">{d.comment}</p>
                    <p className="mt-1 text-xs text-muted">{adviceLabel(d)}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {(!decisions || decisions.length === 0) && (
          <div className="grid min-h-60 place-items-center px-6 py-12 text-center">
            <div>
              <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">
                {error ? 'Backend unreachable' : decisions ? 'No decisions recorded' : 'Loading'}
              </p>
              {decisions && (
                <p className="mx-auto mt-1 max-w-[42ch] text-muted">
                  Decisions appear here when an analyst investigates, keeps open, or resolves an incident.
                </p>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
