import { formatClock } from '../api'
import { PROVIDERS } from '../providers'

const FEED_LABEL = { poll: 'Connected', injection: 'Demo feed' }

// providers is null when the backend can't vouch for its numbers.
export default function ProviderGrid({ providers }) {
  return (
    <section aria-label="Events by cloud provider" className="grid border border-rule md:grid-cols-3">
      {PROVIDERS.map((p) => {
        const info = providers?.[p.id]
        const tag = info?.connected ? 'Connected' : (FEED_LABEL[info?.channel] ?? 'Not connected')

        return (
          <article
            key={p.id}
            id={`provider-${p.id}`}
            className="scroll-mt-6 border-rule px-5 py-4 not-last:border-b md:not-last:border-r md:not-last:border-b-0"
          >
            <header className="flex items-baseline justify-between gap-3">
              <h2 className="font-sign text-xl leading-none font-bold tracking-[0.06em] uppercase">{p.name}</h2>
              <span className="border border-rule px-2 py-0.5 font-sign text-xs font-semibold tracking-[0.1em] text-muted uppercase">
                {tag}
              </span>
            </header>
            <p className="mt-0.5 text-sm text-muted">{p.source}</p>

            <p className={`mt-3 font-sign text-[3.5rem] leading-none font-bold ${info ? '' : 'text-muted'}`}>
              {info ? info.events_24h : '—'}
            </p>
            <dl className="mt-3 flex gap-6 text-sm">
              <div>
                <dt className="text-xs tracking-[0.1em] text-muted uppercase">Window</dt>
                <dd>Last 24 h</dd>
              </div>
              <div>
                <dt className="text-xs tracking-[0.1em] text-muted uppercase">Last event</dt>
                <dd>{info?.last_event_at ? formatClock(info.last_event_at) : 'None yet'}</dd>
              </div>
            </dl>
          </article>
        )
      })}
    </section>
  )
}
