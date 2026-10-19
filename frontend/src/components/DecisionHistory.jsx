import { ArrowRight } from 'lucide-react'
import { formatClock } from '../api'
import { ACTION_LABELS, adviceLabel } from '../decisions'
import { StatusTag } from './Tags'

export default function DecisionHistory({ decisions }) {
  if (decisions.length === 0) {
    return <p className="px-4 py-4 text-muted">No decisions yet. The incident is holding for clearance.</p>
  }

  return (
    <ol className="divide-y divide-rule-soft">
      {decisions.map((d) => (
        <li key={d.id} className="px-4 py-3">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
            <span className="font-sign font-bold tracking-[0.06em] text-ink uppercase">{ACTION_LABELS[d.action]}</span>
            <StatusTag status={d.from_status} />
            <ArrowRight aria-label="to" strokeWidth={2.5} className="size-3.5 text-muted" />
            <StatusTag status={d.to_status} />
          </div>
          <p className="mt-1.5 whitespace-pre-line text-ink">{d.comment}</p>
          <p className="mt-1 text-xs text-muted">
            {d.analyst} · {formatClock(d.decided_at)} · {adviceLabel(d)}
          </p>
        </li>
      ))}
    </ol>
  )
}
