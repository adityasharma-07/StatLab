"""Pydantic models: the typed JSON contract between the API and the frontend.

The frontend mirrors these one-to-one as TypeScript interfaces
(frontend/src/types.ts), so the data is typed end to end.
"""

from typing import Literal

from pydantic import BaseModel


# --- datasets and columns ---------------------------------------------------

class DatasetsResponse(BaseModel):
    datasets: list[str]


class ExcludedColumn(BaseModel):
    column: str
    reason: str


class ColumnProfile(BaseModel):
    numeric: list[str]
    categorical: list[str]
    excluded: list[ExcludedColumn]
    row_count: int


class UploadResponse(ColumnProfile):
    """The column profile of an uploaded CSV, plus the id to refer to it later."""
    session_id: str
    filename: str


# --- analyze ----------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    # Exactly one of these says where the data comes from.
    dataset: str | None = None   # a built-in dataset name
    session: str | None = None   # the id of an uploaded CSV
    col_a: str
    col_b: str


class AnalysisProblem(BaseModel):
    """Returned (with HTTP 200) when the engine can't analyze the chosen columns."""
    status: Literal["insufficient_data", "invalid_columns"]
    analysis: str
    message: str


class GroupSummary(BaseModel):
    name: str
    n: int
    median: float
    mean: float
    q1: float
    q3: float
    min: float
    max: float


class PairwiseResult(BaseModel):
    group_a: str
    group_b: str
    p_value: float
    significant: bool


class NormalityCheck(BaseModel):
    group: str
    shapiro_p: float
    normal: bool


class Assumptions(BaseModel):
    normality: list[NormalityCheck]
    levene_p: float
    equal_variance: bool


class GroupComparisonResult(BaseModel):
    status: Literal["ok"]
    analysis: Literal["group_comparison"]
    value_col: str
    group_col: str
    test: Literal["ANOVA", "Kruskal-Wallis"]
    test_reason: str
    assumptions: Assumptions
    statistic: float
    p_value: float
    significant: bool
    posthoc_test: str | None
    group_count: int
    n: int
    pairwise: list[PairwiseResult]
    groups: list[GroupSummary]


class ContingencyTable(BaseModel):
    rows: list[str]          # categories of col_a
    cols: list[str]          # categories of col_b
    counts: list[list[int]]  # counts[i][j] = rows with rows[i] and cols[j]


class ChiSquareResult(BaseModel):
    status: Literal["ok"]
    analysis: Literal["chi_square"]
    col_a: str
    col_b: str
    test: str
    chi2: float
    p_value: float
    dof: int
    significant: bool
    cramers_v: float
    strength: str
    n: int
    low_expected_warning: bool
    contingency: ContingencyTable
    expected: list[list[float]]


class Point(BaseModel):
    x: float
    y: float


class CorrelationResult(BaseModel):
    status: Literal["ok"]
    analysis: Literal["correlation"]
    col_a: str  # x axis
    col_b: str  # y axis
    pearson_r: float
    pearson_p: float
    spearman_rho: float
    spearman_p: float
    slope: float
    intercept: float
    r_squared: float
    significant: bool
    strength: str
    direction: Literal["positive", "negative"]
    n: int
    points: list[Point]


# The "analysis" field tells the frontend which of these it received.
AnalyzeResponse = GroupComparisonResult | ChiSquareResult | CorrelationResult | AnalysisProblem
