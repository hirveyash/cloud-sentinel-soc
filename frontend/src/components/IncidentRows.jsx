import { formatClock } from '../api'
import { PROVIDER_NAMES } from '../providers'
import { cell } from './DataPanel'
import { SeverityTag, StatusTag } from './Tags'

function correlationTarget(key) {
  const split = key.indexOf(':')
  const kind = key.slice(0, split)
  const value = key.slice(split + 1)
  // ARNs end in ':name' or '/name'; GCP and Azure paths end in '/name'.
  return kind === 'ip' ? `Source ${value}` : value.split(/[/:]/).pop()
}

export default function IncidentRows({ incidents }) {
  return incidents.map((incident) => (
    <tr key={incident.id} className="border-b border-rule-soft last:border-b-0 hover:bg-asphalt-raised">
      <td className={cell}>
        <SeverityTag severity={incident.severity} />
      </td>
      <td className={`${cell} sm:min-w-56`}>
        <a
          href={`#/incidents/${incident.id}`}
          className="font-medium text-ink underline decoration-rule underline-offset-4 transition-colors duration-200 ease-sign hover:text-sign-yellow hover:decoration-sign-yellow"
        >
          {incident.title}
        </a>
        <p className="mt-0.5 text-xs text-muted">
          {correlationTarget(incident.correlation_key)} · {incident.event_count}{' '}
          {incident.event_count === 1 ? 'event' : 'events'} · last {formatClock(incident.last_seen)}
        </p>
      </td>
      <td className={`${cell} whitespace-nowrap`}>
        {incident.providers.map((p) => PROVIDER_NAMES[p]).join(' + ')}
      </td>
      <td className={cell}>
        <StatusTag status={incident.status} />
      </td>
    </tr>
  ))
}
