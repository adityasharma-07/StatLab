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
