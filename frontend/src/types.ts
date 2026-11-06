// Mirrors the Pydantic models in backend/schemas.py. Keep the two in sync.

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

// Column profile of an uploaded CSV, plus the id used to refer back to it.
export interface UploadResponse extends ColumnProfile {
  session_id: string
  filename: string
}

// A built-in dataset or an uploaded CSV session.
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

export interface GroupComparisonResult {
  status: 'ok'
  analysis: 'group_comparison'
  value_col: string
  group_col: string
  test: 'Kruskal-Wallis'
  statistic: number
  p_value: number
  significant: boolean
  group_count: number
  n: number
  groups: GroupSummary[]
}

export interface ContingencyTable {
  rows: string[] // categories of col_a
  cols: string[] // categories of col_b
  counts: number[][] // counts[i][j] = rows with rows[i] and cols[j]
}

export interface ChiSquareResult {
  status: 'ok'
  analysis: 'chi_square'
  col_a: string
  col_b: string
  test: string
  chi2: number
  p_value: number
  dof: number
  significant: boolean
  n: number
  contingency: ContingencyTable
  expected: number[][]
}

export interface Point {
  x: number
  y: number
}

export interface RegressionResult {
  status: 'ok'
  analysis: 'regression'
  col_a: string // x axis
  col_b: string // y axis
  test: string
  slope: number
  intercept: number
  r_squared: number
  p_value: number
  significant: boolean
  direction: 'positive' | 'negative'
  n: number
  points: Point[]
}

// The "analysis" field says which of these came back.
export type AnalyzeResponse = GroupComparisonResult | ChiSquareResult | RegressionResult | AnalysisProblem
