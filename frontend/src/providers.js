export const PROVIDERS = [
  { id: 'aws', name: 'AWS', source: 'Security Hub' },
  { id: 'gcp', name: 'GCP', source: 'Security Command Center' },
  { id: 'azure', name: 'Azure', source: 'Defender for Cloud' },
]

export const PROVIDER_NAMES = Object.fromEntries(PROVIDERS.map((p) => [p.id, p.name]))
