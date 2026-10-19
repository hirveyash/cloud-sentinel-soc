import { ArrowDown } from 'lucide-react'
import { PROVIDERS } from '../providers'

const STATUS = {
  checking: {
    label: 'Checking systems',
    detail: () => 'Contacting backend',
    panel: 'bg-sign-black text-sign-yellow/75 border-4 border-dashed border-sign-yellow/60',
  },
  operational: {
    label: 'All systems operational',
    detail: (connected, awaiting) =>
      `Backend online · ${connected} of ${PROVIDERS.length} clouds connected · ${
        awaiting ? `${awaiting} holding for clearance` : 'nothing holding'
      }`,
    panel: 'bg-sign-black text-sign-yellow border-4 border-sign-yellow',
  },
  offline: {
    label: 'Backend unreachable',
    detail: () => 'Start the API on port 8000. Retrying every 15 s',
    panel: 'bg-sign-red text-sign-white border-4 border-sign-red',
  },
}

// counts is null when the backend can't vouch for them.
export default function SignArray({ status, counts, connected, awaiting }) {
  const s = STATUS[status]

  return (
    <section
      aria-label="System status"
      className="grid gap-1 bg-sign-black p-1 lg:grid-cols-[1.6fr_repeat(3,1fr)]"
    >
      <div
        role="status"
        className={`flex min-h-24 flex-col justify-center px-6 py-3 transition-colors duration-200 ease-sign ${s.panel}`}
      >
        <p className="font-sign text-[clamp(1.75rem,2.2vw,2.25rem)] leading-none font-bold tracking-[0.03em] uppercase">
          {s.label}
        </p>
        <p className="mt-2 text-sm opacity-90">{s.detail(connected, awaiting)}</p>
      </div>

      <div className="grid grid-cols-3 gap-1 lg:contents">
        {PROVIDERS.map((p) => {
          const count = counts?.[p.id]
          const live = count != null

          return (
            <a
              key={p.id}
              href={`#provider-${p.id}`}
              className={`group flex min-h-24 items-center justify-between gap-2 px-3 py-3 transition-colors duration-200 ease-sign sm:gap-3 sm:px-4 ${
                live
                  ? 'bg-sign-yellow text-sign-black hover:bg-sign-white'
                  : 'bg-asphalt-raised text-muted hover:text-ink'
              }`}
            >
              <span className="font-sign leading-none font-bold uppercase">
                <span className="block text-base tracking-[0.08em] sm:text-lg">{p.name}</span>
                <span className="mt-1 flex items-baseline gap-1.5 whitespace-nowrap">
                  <span className="text-[clamp(1.75rem,2.6vw,2.5rem)]">{live ? count : '—'}</span>
                  <span className="text-xs tracking-[0.08em] sm:text-sm">
                    {live ? (count === 1 ? 'event' : 'events') : 'no data'}
                  </span>
                </span>
              </span>
              <ArrowDown
                aria-hidden="true"
                strokeWidth={3}
                className="size-4 shrink-0 transition-transform duration-200 ease-sign group-hover:translate-y-0.5 sm:size-7"
              />
            </a>
          )
        })}
      </div>
    </section>
  )
}
