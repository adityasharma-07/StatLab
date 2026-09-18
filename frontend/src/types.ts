// TypeScript mirrors of the Pydantic models in backend/schemas.py.
// Keep the two files in sync: together they are the typed API contract.

export interface DatasetsResponse {
  datasets: string[]
}

export interface ExcludedColumn {
  column: string
  reason: string
}

export interface ColumnProfile {
  numeric: string[]
  categorical: string[]
  excluded: ExcludedColumn[]
  row_count: number
}

// Where the data comes from: a built-in dataset or an uploaded CSV session.
export interface DataSource {
  dataset?: string
  session?: string
}

export interface AnalyzeRequest extends DataSource {
  col_a: string
  col_b: string
}

export interface AnalysisProblem {
  status: 'insufficient_data' | 'invalid_columns'
  analysis: string
  message: string
}

export interface GroupSummary {
  name: string
  n: number
  median: number
  mean: number
  q1: number
  q3: number
  min: number
  max: number
}

export interface PairwiseResult {
  group_a: string
  group_b: string
  p_value: number
  significant: boolean
}

export interface GroupComparisonResult {
  status: 'ok'
  analysis: 'group_comparison'
  value_col: string
  group_col: string
  test: string
  statistic: number
  p_value: number
  significant: boolean
  group_count: number
  n: number
  pairwise: PairwiseResult[]
  groups: GroupSummary[]
}

export type AnalyzeResponse = GroupComparisonResult | AnalysisProblem
