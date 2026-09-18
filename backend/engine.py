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
    - excluded: columns that can't be analyzed (a single constant value, or a
      text column with too many groups). Flagged with a reason, not an error.
    """
    numeric = []
    categorical = []
    excluded = []

    for column in df.columns:
        series = df[column]
        distinct = int(series.nunique(dropna=True))

        # A constant (or entirely empty) column can't show any relationship.
        if distinct < 2:
            excluded.append({"column": column, "reason": "fewer than 2 distinct values"})
            continue

        if is_numeric_column(series):
            numeric.append(column)
            # A numeric column with few distinct values can ALSO act as a group.
            if distinct <= MAX_NUMERIC_CATEGORIES:
                categorical.append(column)
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


def tukey_pairwise(group_names: list, groups: list[pd.Series]) -> list[dict]:
    # Tukey's HSD: the standard follow-up to ANOVA (the parametric counterpart
    # of Dunn's test). It compares every pair of group means and already
    # adjusts its p-values for the number of comparisons.
    p_values = stats.tukey_hsd(*groups).pvalue

    pairs = []
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            p_value = float(p_values[i][j])
            pairs.append({
                "group_a": str(group_names[i]),
                "group_b": str(group_names[j]),
                "p_value": p_value,
                "significant": p_value < ALPHA,
            })
    return pairs


def check_assumptions(group_names: list, groups: list[pd.Series]) -> dict:
    """Check the two assumptions ANOVA relies on: normality and equal variance."""
    # Shapiro-Wilk: tests whether one sample looks normally distributed.
    # Its null hypothesis is "the data IS normal", so a SMALL p-value (< 0.05)
    # is evidence AGAINST normality. ANOVA needs every group to be roughly normal.
    normality = []
    for name, values in zip(group_names, groups):
        shapiro_p = float(stats.shapiro(values).pvalue)
        normality.append({
            "group": str(name),
            "shapiro_p": shapiro_p,
            "normal": shapiro_p > ALPHA,
        })

    # Levene's test: tests whether the groups have equal variances (similar
    # spread). Same logic: a small p-value means the variances differ.
    levene_p = float(stats.levene(*groups).pvalue)

    return {
        "normality": normality,
        "levene_p": levene_p,
        "equal_variance": levene_p > ALPHA,
    }


def explain_test_choice(assumptions: dict) -> str:
    """A short human-readable reason for the ANOVA vs Kruskal-Wallis choice."""
    non_normal = [item["group"] for item in assumptions["normality"] if not item["normal"]]

    if not non_normal and assumptions["equal_variance"]:
        return (
            "All groups look normally distributed (Shapiro-Wilk p > 0.05) and have similar "
            "variances (Levene p > 0.05), so one-way ANOVA is appropriate."
        )

    reasons = []
    if non_normal:
        reasons.append(f"data is non-normal in {', '.join(non_normal)} (Shapiro-Wilk p < 0.05)")
    if not assumptions["equal_variance"]:
        reasons.append("group variances are unequal (Levene p < 0.05)")
    return f"ANOVA's assumptions don't hold: {' and '.join(reasons)}, so the non-parametric Kruskal-Wallis test was used."


def run_group_comparison(df: pd.DataFrame, value_col: str, group_col: str) -> dict:
    """Does a numeric measure differ across the groups of a categorical column?

    Checks ANOVA's assumptions first, then runs ANOVA if they hold or
    Kruskal-Wallis if they don't.
    """
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

    # 4. Check assumptions BEFORE choosing the test. This is the heart of the app.
    assumptions = check_assumptions(group_names, groups)
    all_normal = all(item["normal"] for item in assumptions["normality"])
    use_anova = all_normal and assumptions["equal_variance"]

    if use_anova:
        # One-way ANOVA: parametric test comparing group MEANS. More powerful
        # than Kruskal-Wallis, but only valid when every group is roughly
        # normal and the groups have similar variances.
        test = "ANOVA"
        statistic, p_value = stats.f_oneway(*groups)
    else:
        # Kruskal-Wallis: non-parametric test for whether groups differ. It
        # compares RANKS rather than raw values, so it doesn't assume the data
        # is normally distributed. Used when ANOVA's assumptions fail.
        test = "Kruskal-Wallis"
        statistic, p_value = stats.kruskal(*groups)

    significant = bool(p_value < ALPHA)

    # 5. Post-hoc only when the overall test is significant: if there's no
    #    evidence that ANY group differs, hunting for pairs is just fishing.
    #    Each test has its matching follow-up: Tukey for ANOVA, Dunn for KW.
    pairwise = []
    posthoc_test = None
    if significant and use_anova:
        posthoc_test = "Tukey HSD"
        pairwise = tukey_pairwise(group_names, groups)
    elif significant:
        posthoc_test = "Dunn (Bonferroni-adjusted)"
        pairwise = dunn_pairwise(clean, value_col, group_col)

    return {
        "status": "ok",
        "analysis": analysis,
        "value_col": value_col,
        "group_col": group_col,
        "test": test,
        "test_reason": explain_test_choice(assumptions),
        "assumptions": assumptions,
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": significant,
        "posthoc_test": posthoc_test,
        "group_count": len(groups),
        "n": int(len(clean)),
        "pairwise": pairwise,
        "groups": [summarize_group(str(name), values) for name, values in zip(group_names, groups)],
    }


# ---------------------------------------------------------------------------
# Categorical x categorical: chi-square test of independence
# ---------------------------------------------------------------------------

def describe_strength(value: float) -> str:
    # Common rule-of-thumb labels (Cohen) for effect sizes on a 0-1 scale,
    # used for both Cramér's V and the absolute correlation coefficient.
    size = abs(value)
    if size < 0.1:
        return "negligible"
    if size < 0.3:
        return "weak"
    if size < 0.5:
        return "moderate"
    return "strong"


def run_chi_square(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Are two categorical columns associated, or independent of each other?"""
    analysis = "chi_square"

    missing = missing_columns(df, [col_a, col_b])
    if missing:
        return problem(analysis, "invalid_columns", f"Column not found: {', '.join(missing)}")

    clean = df[[col_a, col_b]].dropna()

    # The contingency table counts how many rows fall into each combination of
    # categories (e.g. day=Sat & time=Dinner). It's the input to the test and
    # also what the frontend draws as a heatmap.
    contingency = pd.crosstab(clean[col_a], clean[col_b])

    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return problem(analysis, "insufficient_data", "Each column needs at least 2 categories (after dropping missing values).")
    if max(contingency.shape) > MAX_GROUPS:
        return problem(analysis, "insufficient_data", f"Too many categories to compare meaningfully (max {MAX_GROUPS} per column).")

    # Chi-square test of independence: compares the OBSERVED counts with the
    # counts we would EXPECT if the two columns were unrelated. A big gap
    # between them (large chi2, small p) means the columns are associated.
    # (For 2x2 tables scipy applies Yates' continuity correction by default.)
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    # Cramér's V: effect size for chi-square, from 0 (no association) to 1
    # (perfect association). Needed because with enough rows even a trivial
    # association gets a tiny p-value; V says how STRONG the association is.
    n = int(contingency.to_numpy().sum())
    cramers_v = float((chi2 / (n * (min(contingency.shape) - 1))) ** 0.5)

    # The chi-square approximation is unreliable when expected counts are
    # small. Rule of thumb: warn if more than 20% of cells expect fewer than 5.
    low_expected_share = float((expected < 5).mean())

    return {
        "status": "ok",
        "analysis": analysis,
        "col_a": col_a,
        "col_b": col_b,
        "test": "Chi-square test of independence",
        "chi2": float(chi2),
        "p_value": float(p_value),
        "dof": int(dof),
        "significant": bool(p_value < ALPHA),
        "cramers_v": cramers_v,
        "strength": describe_strength(cramers_v),
        "n": n,
        "low_expected_warning": low_expected_share > 0.2,
        "contingency": {
            "rows": [str(label) for label in contingency.index],
            "cols": [str(label) for label in contingency.columns],
            "counts": contingency.to_numpy().tolist(),
        },
        "expected": expected.round(2).tolist(),
    }


# ---------------------------------------------------------------------------
# Dispatcher: pick the analysis from the two columns' types
# ---------------------------------------------------------------------------

def column_kind(series: pd.Series) -> str:
    """'numeric' or 'categorical', using the same rule as profile_columns."""
    if not is_numeric_column(series):
        return "categorical"
    # A numeric column with only a few distinct values (e.g. tips `size`)
    # behaves like a set of groups, so treat it as categorical.
    if series.nunique(dropna=True) <= MAX_NUMERIC_CATEGORIES:
        return "categorical"
    return "numeric"


def analyze(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Run the right analysis for a pair of columns, based on their types."""
    missing = missing_columns(df, [col_a, col_b])
    if missing:
        return problem("none", "invalid_columns", f"Column not found: {', '.join(missing)}")
    if col_a == col_b:
        return problem("none", "invalid_columns", "Pick two different columns.")

    kind_a = column_kind(df[col_a])
    kind_b = column_kind(df[col_b])

    # numeric + categorical (in either order): compare the numeric measure
    # across the categorical column's groups.
    if kind_a == "numeric" and kind_b == "categorical":
        return run_group_comparison(df, value_col=col_a, group_col=col_b)
    if kind_a == "categorical" and kind_b == "numeric":
        return run_group_comparison(df, value_col=col_b, group_col=col_a)

    # categorical + categorical: are the two sets of categories associated?
    if kind_a == "categorical" and kind_b == "categorical":
        return run_chi_square(df, col_a, col_b)

    # numeric + numeric: correlation (added in the next step).
    return problem("correlation", "invalid_columns", "Numeric x numeric analysis is not available yet.")
