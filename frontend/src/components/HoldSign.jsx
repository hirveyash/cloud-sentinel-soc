// Mandatory hold sign: lit red only when incidents are actually waiting.
// label replaces the count wording on the lit sign, e.g. on a single incident.
export default function HoldSign({ awaiting, label }) {
  const base = 'px-2 py-0.5 font-sign text-sm font-bold tracking-[0.08em] uppercase'

  if (awaiting == null) {
    return <span className={`${base} border border-rule text-muted`}>Hold · no data</span>
  }
  if (awaiting === 0) {
    return <span className={`${base} border border-sign-red text-[#ff6b7f]`}>Hold · clear</span>
  }
  return (
    <span className={`${base} border border-sign-red bg-sign-red text-sign-white`}>
      Hold · {label ?? `${awaiting} awaiting clearance`}
    </span>
  )
}
