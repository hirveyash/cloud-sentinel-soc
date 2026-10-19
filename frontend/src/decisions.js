export const ACTIONS = [
  {
    id: 'investigate',
    label: 'Investigate',
    status: 'investigating',
    help: 'Take ownership and work the evidence. The incident stays on the board.',
  },
  {
    id: 'keep_open',
    label: 'Keep open',
    status: 'open',
    help: 'Acknowledge it and keep watching. No response action yet.',
  },
  {
    id: 'resolve',
    label: 'Resolve',
    status: 'resolved',
    help: 'Close it. Say what was done, or why no action is needed.',
  },
]

export const ACTION_LABELS = Object.fromEntries(ACTIONS.map((a) => [a.id, a.label]))

// Which advice the analyst had on screen when deciding (recorded by the backend).
export function adviceLabel(d) {
  if (d.briefing_generator === 'llm') return `Advice on screen: ${d.briefing_model} briefing`
  if (d.briefing_generator === 'template') return 'Advice on screen: rule-based briefing'
  return 'No briefing was available'
}
