import type { ColumnProfile } from './types'

export type ColumnKind = 'numeric' | 'categorical'

export interface ColumnOption {
  name: string
  kind: ColumnKind
}

// Every usable column, labeled with the type the engine will treat it as.
// A low-cardinality numeric column (like tips "size") appears in BOTH of the
// profile's lists; the engine treats it as categorical, so we label it that way.
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

// Preview which analysis a pair of columns will trigger. This mirrors the
// routing in the engine's analyze() dispatcher (the engine has the final say).
export function describePair(a: ColumnOption | undefined, b: ColumnOption | undefined): string {
  if (!a || !b) return ''
  if (a.name === b.name) return 'Pick two different columns.'

  const pair = `${a.kind} × ${b.kind}`
  if (a.kind === 'numeric' && b.kind === 'numeric') return `${pair} → correlation + linear regression`
  if (a.kind === 'categorical' && b.kind === 'categorical') return `${pair} → chi-square test of independence`
  return `${pair} → group comparison (ANOVA or Kruskal-Wallis, chosen by assumption checks)`
}
