"""Request and response models. Mirrored in frontend/src/types.ts."""

from typing import Literal

from pydantic import BaseModel


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
    """Column profile of an uploaded CSV, plus the id used to refer back to it."""
    session_id: str
    filename: str


class AnalyzeRequest(BaseModel):
    # Exactly one of these is set.
    dataset: str | None = None
    session: str | None = None
    col_a: str
    col_b: str


class AnalysisProblem(BaseModel):
    """Returned with HTTP 200 when the chosen columns can't be analyzed."""
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


class GroupComparisonResult(BaseModel):
    status: Literal["ok"]
    analysis: Literal["group_comparison"]
    value_col: str
    group_col: str
    test: Literal["Kruskal-Wallis"]
    statistic: float
    p_value: float
    significant: bool
    group_count: int
    n: int
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
    n: int
    contingency: ContingencyTable
    expected: list[list[float]]


class Point(BaseModel):
    x: float
    y: float


class RegressionResult(BaseModel):
    status: Literal["ok"]
    analysis: Literal["regression"]
    col_a: str  # x axis
    col_b: str  # y axis
    test: str
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    significant: bool
    direction: Literal["positive", "negative"]
    n: int
    points: list[Point]


# The "analysis" field tells the frontend which of these it received.
AnalyzeResponse = GroupComparisonResult | ChiSquareResult | RegressionResult | AnalysisProblem
