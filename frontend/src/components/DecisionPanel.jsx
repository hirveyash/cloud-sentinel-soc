import { useId, useState } from 'react'
import { formatClock } from '../api'
import { ACTION_LABELS, ACTIONS } from '../decisions'

const MIN_COMMENT = 10
const ANALYST_KEY = 'sentinel.analyst'

function rememberedAnalyst() {
  try {
    return localStorage.getItem(ANALYST_KEY) ?? ''
  } catch {
    return ''
  }
}

const FIELD =
  'w-full border border-rule bg-asphalt px-3 py-2 text-ink placeholder:text-muted/70 transition-colors duration-200 ease-sign focus:border-sign-yellow focus:outline-none'

export default function DecisionPanel({ incident, onDecided }) {
  const ids = useId()
  const [action, setAction] = useState(null)
  const [comment, setComment] = useState('')
  const [analyst, setAnalyst] = useState(rememberedAnalyst)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [recorded, setRecorded] = useState(null)

  if (incident.status === 'resolved') {
    return (
      <div className="p-4 sm:p-5">
        <p className="font-sign text-lg font-bold tracking-[0.06em] uppercase">Resolved</p>
        <p className="mt-1 text-muted">
          This incident is closed and its decisions are in the audit log. New activity from the same source opens a
          new incident.
        </p>
      </div>
    )
  }

  const chosen = ACTIONS.find((a) => a.id === action)
  const commentLength = comment.trim().length
  const ready = chosen && commentLength >= MIN_COMMENT && analyst.trim().length >= 2 && !submitting

  async function submit(e) {
    e.preventDefault()
    if (!ready) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`/api/incidents/${incident.id}/decisions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, comment, analyst }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(typeof body.detail === 'string' ? body.detail : 'Check the comment and analyst name, then retry.')
        return
      }
      try {
        localStorage.setItem(ANALYST_KEY, analyst.trim())
      } catch {
        // Storage unavailable: the name just won't be prefilled next time.
      }
      setRecorded(body)
      setAction(null)
      setComment('')
      onDecided()
    } catch {
      setError('The backend did not answer. Nothing was recorded; retry when it is back.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4 p-4 sm:p-5" noValidate>
      <fieldset>
        <legend className="text-sm text-muted">
          Choose a decision. Nothing changes until you record it with a comment.
        </legend>
        <div className="mt-3 grid gap-2">
          {ACTIONS.map((a) => {
            const current = a.status === incident.status
            const checked = action === a.id
            return (
              <label
                key={a.id}
                className={`flex gap-3 border px-3 py-2.5 transition-colors duration-200 ease-sign ${
                  current
                    ? 'cursor-not-allowed border-rule-soft opacity-50'
                    : checked
                      ? 'cursor-pointer border-sign-yellow bg-asphalt-raised'
                      : 'cursor-pointer border-rule hover:border-muted'
                }`}
              >
                <input
                  type="radio"
                  name={`${ids}-action`}
                  value={a.id}
                  checked={checked}
                  disabled={current}
                  onChange={() => setAction(a.id)}
                  className="mt-1 size-4 shrink-0 accent-sign-yellow"
                />
                <span>
                  <span
                    className={`block font-sign text-base font-bold tracking-[0.06em] uppercase ${checked ? 'text-sign-yellow' : 'text-ink'}`}
                  >
                    {a.label}
                    {current && <span className="ml-2 text-xs text-muted">Current status</span>}
                  </span>
                  <span className="block text-sm text-muted">{a.help}</span>
                </span>
              </label>
            )
          })}
        </div>
      </fieldset>

      <div>
        <div className="flex items-baseline justify-between gap-3">
          <label htmlFor={`${ids}-comment`} className="text-xs font-semibold tracking-[0.1em] text-muted uppercase">
            Comment (required)
          </label>
          <span className={`text-xs ${commentLength >= MIN_COMMENT ? 'text-muted' : 'text-sign-yellow'}`}>
            {commentLength < MIN_COMMENT ? `${MIN_COMMENT - commentLength} more characters` : `${commentLength} characters`}
          </span>
        </div>
        <textarea
          id={`${ids}-comment`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          maxLength={2000}
          placeholder="What you decided and why, e.g. which playbook steps you approved."
          className={`${FIELD} mt-1.5 resize-y`}
        />
      </div>

      <div>
        <label htmlFor={`${ids}-analyst`} className="text-xs font-semibold tracking-[0.1em] text-muted uppercase">
          Analyst
        </label>
        <input
          id={`${ids}-analyst`}
          value={analyst}
          onChange={(e) => setAnalyst(e.target.value)}
          maxLength={80}
          autoComplete="name"
          placeholder="Your name"
          className={`${FIELD} mt-1.5`}
        />
      </div>

      {error && (
        <p role="alert" className="border border-sign-yellow px-3 py-2 text-sm text-ink">
          {error}
        </p>
      )}
      {recorded && !error && (
        <p role="status" className="text-sm text-muted">
          Recorded {ACTION_LABELS[recorded.action].toLowerCase()} at {formatClock(recorded.decided_at)}.
        </p>
      )}

      <button
        type="submit"
        disabled={!ready}
        className="w-full bg-sign-yellow px-4 py-3 font-sign text-base font-bold tracking-[0.08em] text-sign-black uppercase transition-colors duration-200 ease-sign hover:bg-sign-white disabled:cursor-not-allowed disabled:bg-asphalt-raised disabled:text-muted"
      >
        {submitting ? 'Recording…' : chosen ? `Record decision: ${chosen.label}` : 'Record decision'}
      </button>
    </form>
  )
}
