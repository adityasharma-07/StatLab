import type { ColumnProfile } from './types'

export type ColumnKind = 'numeric' | 'categorical'

export interface ColumnOption {
  name: string
  kind: ColumnKind
}

// A low-cardinality numeric column appears in both profile lists. The engine
// treats it as categorical, so label it that way.
export function columnOptions(profile: ColumnProfile): ColumnOption[] {
  const options: ColumnOption[] = []
  for (const name of profile.numeric) {
    if (!profile.categorical.includes(name)) options.push({ name, kind: 'numeric' })
  }
  for (const name of profile.categorical) {
    options.push({ name, kind: 'categorical' })
  }
  return options
}

// Mirrors the routing in the engine's analyze(). The engine has the final say.
export function describePair(a: ColumnOption | undefined, b: ColumnOption | undefined): string {
  if (!a || !b) return ''
  if (a.name === b.name) return 'Pick two different columns.'

  const pair = `${a.kind} × ${b.kind}`
  if (a.kind === 'numeric' && b.kind === 'numeric') return `${pair} → linear regression`
  if (a.kind === 'categorical' && b.kind === 'categorical') return `${pair} → chi-square test of independence`
  return `${pair} → group comparison (Kruskal-Wallis)`
}
