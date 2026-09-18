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

// The column profile of an uploaded CSV, plus the id to refer to it later.
export interface UploadResponse extends ColumnProfile {
  session_id: string
  filename: string
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

export interface NormalityCheck {
  group: string
  shapiro_p: number
  normal: boolean
}

export interface Assumptions {
  normality: NormalityCheck[]
  levene_p: number
  equal_variance: boolean
}

export interface GroupComparisonResult {
  status: 'ok'
  analysis: 'group_comparison'
  value_col: string
  group_col: string
  test: 'ANOVA' | 'Kruskal-Wallis'
  test_reason: string
  assumptions: Assumptions
  statistic: number
  p_value: number
  significant: boolean
  posthoc_test: string | null
  group_count: number
  n: number
  pairwise: PairwiseResult[]
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
  cramers_v: number
  strength: string
  n: number
  low_expected_warning: boolean
  contingency: ContingencyTable
  expected: number[][]
}

export interface Point {
  x: number
  y: number
}

export interface CorrelationResult {
  status: 'ok'
  analysis: 'correlation'
  col_a: string // x axis
  col_b: string // y axis
  pearson_r: number
  pearson_p: number
  spearman_rho: number
  spearman_p: number
  slope: number
  intercept: number
  r_squared: number
  significant: boolean
  strength: string
  direction: 'positive' | 'negative'
  n: number
  points: Point[]
}

// The "analysis" field tells us which of these we received.
export type AnalyzeResponse = GroupComparisonResult | ChiSquareResult | CorrelationResult | AnalysisProblem
