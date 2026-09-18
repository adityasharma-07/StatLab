"""StatScope statistics engine.

Pure Python: pandas + scipy + scikit-posthocs. This file knows nothing about
HTTP or FastAPI. Every function takes a DataFrame and column names and returns
a plain dict, so it can be unit-tested (and reused) without a web server.
"""

from pathlib import Path

import pandas as pd
import scikit_posthocs
from scipy import stats

DATA_DIR = Path(__file__).parent / "data"
BUILTIN_DATASETS = ["penguins", "tips"]

# p-values below this are called "statistically significant" (the usual convention).
ALPHA = 0.05

# A numeric column with this many distinct values or fewer is treated as
# categorical (e.g. party `size` in the tips dataset: 1-6).
MAX_NUMERIC_CATEGORIES = 10

# A categorical column with more groups than this is too fragmented to compare.
MAX_GROUPS = 20

# Each group needs at least this many values for the tests to be meaningful
# (Shapiro-Wilk also requires n >= 3).
MIN_GROUP_SIZE = 3


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def list_builtin_datasets() -> list[str]:
    return list(BUILTIN_DATASETS)


def load_builtin(name: str) -> pd.DataFrame:
    # The CSVs are snapshots of seaborn's public sample datasets, bundled in
    # the repo so the app works offline. Missing values are NOT dropped here;
    # each analysis drops nulls only for the two columns it actually uses.
    if name not in BUILTIN_DATASETS:
        raise ValueError(f"Unknown dataset: {name}")
    return pd.read_csv(DATA_DIR / f"{name}.csv")


# ---------------------------------------------------------------------------
# Column profiling
# ---------------------------------------------------------------------------

def is_numeric_column(series: pd.Series) -> bool:
    # Booleans count as numeric in pandas, but True/False is really a category.
    if pd.api.types.is_bool_dtype(series):
        return False
    return pd.api.types.is_numeric_dtype(series)


def profile_columns(df: pd.DataFrame) -> dict:
    """Classify each column so the frontend can offer sensible pickers.

    - numeric: columns with a numeric dtype (the things you can measure).
    - categorical: columns you can group by: text/bool columns, or numeric
      columns with only a few distinct values.
    - excluded: columns that look categorical but can't be used as groups
      (only 1 group, or too many groups). Flagged with a reason, not an error.
    """
    numeric = []
    categorical = []
    excluded = []

    for column in df.columns:
        series = df[column]
        distinct = int(series.nunique(dropna=True))

        if is_numeric_column(series):
            numeric.append(column)
            # A numeric column with few distinct values can ALSO act as a group.
            if 2 <= distinct <= MAX_NUMERIC_CATEGORIES:
                categorical.append(column)
            continue

        if distinct < 2:
            excluded.append({"column": column, "reason": "fewer than 2 distinct values"})
        elif distinct > MAX_GROUPS:
            excluded.append({"column": column, "reason": f"too many groups ({distinct}) to compare"})
        else:
            categorical.append(column)

    return {
        "numeric": numeric,
        "categorical": categorical,
        "excluded": excluded,
        "row_count": int(len(df)),
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def problem(analysis: str, status: str, message: str) -> dict:
    # Every "can't analyze this" case returns the same small shape instead of
    # raising, so the API never turns bad input into a 500 error.
    return {"status": status, "analysis": analysis, "message": message}


def missing_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column not in df.columns]


# ---------------------------------------------------------------------------
# Numeric x categorical: group comparison
# ---------------------------------------------------------------------------

def summarize_group(name: str, values: pd.Series) -> dict:
    # The five-number summary (+ mean) is exactly what a box plot draws.
    return {
        "name": name,
        "n": int(len(values)),
        "median": float(values.median()),
        "mean": float(values.mean()),
        "q1": float(values.quantile(0.25)),
        "q3": float(values.quantile(0.75)),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def dunn_pairwise(clean: pd.DataFrame, value_col: str, group_col: str) -> list[dict]:
    # Dunn's test: the standard follow-up to Kruskal-Wallis. KW only says "at
    # least one group differs"; Dunn's compares every pair to find WHICH ones.
    # Bonferroni adjustment corrects for running many comparisons at once
    # (otherwise some pairs would look significant purely by chance).
    matrix = scikit_posthocs.posthoc_dunn(
        clean, val_col=value_col, group_col=group_col, p_adjust="bonferroni"
    )

    # The result is a symmetric matrix; walk the upper triangle so each pair
    # appears once.
    names = list(matrix.index)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p_value = float(matrix.iloc[i, j])
            pairs.append({
                "group_a": str(names[i]),
                "group_b": str(names[j]),
                "p_value": p_value,
                "significant": p_value < ALPHA,
            })
    return pairs


def run_group_comparison(df: pd.DataFrame, value_col: str, group_col: str) -> dict:
    """Does a numeric measure differ across the groups of a categorical column?"""
    analysis = "group_comparison"

    missing = missing_columns(df, [value_col, group_col])
    if missing:
        return problem(analysis, "invalid_columns", f"Column not found: {', '.join(missing)}")
    if not is_numeric_column(df[value_col]):
        return problem(analysis, "invalid_columns", f"'{value_col}' is not numeric, so it can't be the measured value.")

    # 1. Only drop rows that are null in the two columns we actually use.
    clean = df[[value_col, group_col]].dropna()

    # 2. One array of values per group.
    group_names = sorted(clean[group_col].unique(), key=str)
    groups = [clean.loc[clean[group_col] == name, value_col] for name in group_names]

    # 3. Guards: return a clear status instead of letting scipy raise.
    if len(groups) < 2:
        return problem(analysis, "insufficient_data", f"'{group_col}' needs at least 2 groups to compare (found {len(groups)}).")
    if len(groups) > MAX_GROUPS:
        return problem(analysis, "insufficient_data", f"'{group_col}' has {len(groups)} groups, which is too many to compare meaningfully (max {MAX_GROUPS}).")
    for name, values in zip(group_names, groups):
        if len(values) < MIN_GROUP_SIZE:
            return problem(analysis, "insufficient_data", f"Group '{name}' has only {len(values)} value(s); each group needs at least {MIN_GROUP_SIZE}.")
    if clean[value_col].nunique() < 2:
        return problem(analysis, "insufficient_data", f"Every value of '{value_col}' is identical, so there is nothing to compare.")

    # 4. Kruskal-Wallis: non-parametric test for whether groups differ. It
    #    compares RANKS rather than raw values, so it doesn't assume the data
    #    is normally distributed (unlike ANOVA).
    statistic, p_value = stats.kruskal(*groups)
    significant = bool(p_value < ALPHA)

    # 5. Post-hoc only when the overall test is significant: if there's no
    #    evidence that ANY group differs, hunting for pairs is just fishing.
    pairwise = dunn_pairwise(clean, value_col, group_col) if significant else []

    return {
        "status": "ok",
        "analysis": analysis,
        "value_col": value_col,
        "group_col": group_col,
        "test": "Kruskal-Wallis",
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": significant,
        "group_count": len(groups),
        "n": int(len(clean)),
        "pairwise": pairwise,
        "groups": [summarize_group(str(name), values) for name, values in zip(group_names, groups)],
    }
