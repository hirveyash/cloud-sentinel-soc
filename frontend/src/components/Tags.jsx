// Sign-form tags for table rows. Red stays reserved for holds (DESIGN.md Sign Colour Rule),
// so severity is encoded by how lit the yellow sign is.
const BASE =
  'inline-block border px-2 py-0.5 font-sign text-xs leading-tight font-bold tracking-[0.08em] whitespace-nowrap uppercase'

const SEVERITY = {
  critical: 'border-sign-yellow bg-sign-yellow text-sign-black',
  high: 'border-sign-yellow text-sign-yellow',
  medium: 'border-muted text-ink',
  low: 'border-rule text-muted',
}

const STATUS = {
  new: { label: 'Hold', className: 'border-sign-red bg-sign-red text-sign-white' },
  investigating: { label: 'Investigating', className: 'border-sign-yellow text-sign-yellow' },
  open: { label: 'Kept open', className: 'border-muted text-ink' },
  resolved: { label: 'Resolved', className: 'border-rule text-muted' },
}

export function SeverityTag({ severity }) {
  return <span className={`${BASE} ${SEVERITY[severity]}`}>{severity}</span>
}

export function StatusTag({ status }) {
  const s = STATUS[status]
  return <span className={`${BASE} ${s.className}`}>{s.label}</span>
}
