import { formatClock } from '../api'
import { PROVIDER_NAMES } from '../providers'
import { cell } from './DataPanel'
import { SeverityTag } from './Tags'

export default function EventRows({ events }) {
  return events.map((event) => (
    <tr key={event.id} className="border-b border-rule-soft last:border-b-0 hover:bg-asphalt-raised">
      <td className={`${cell} whitespace-nowrap text-muted`} title={event.observed_at}>
        {formatClock(event.observed_at)}
      </td>
      <td className={`${cell} sm:min-w-52`}>
        <p className="text-ink">{event.title}</p>
        <p className="mt-1">
          <SeverityTag severity={event.severity} />
        </p>
      </td>
      <td className={`${cell} whitespace-nowrap`}>{PROVIDER_NAMES[event.provider]}</td>
      <td className={`${cell} whitespace-nowrap text-muted`}>{event.source}</td>
    </tr>
  ))
}
