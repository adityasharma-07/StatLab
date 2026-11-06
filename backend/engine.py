"""Statistics engine. Takes a DataFrame and column names, returns plain dicts.

No FastAPI imports here, so it can be tested without a server.
"""

from pathlib import Path

import pandas as pd
import scikit_posthocs
from scipy import stats

DATA_DIR = Path(__file__).parent / "data"
BUILTIN_DATASETS = ["penguins", "tips"]

ALPHA = 0.05

# A numeric column with few distinct values is really a grouping column,
# e.g. party size in the tips dataset runs 1-6.
MAX_NUMERIC_CATEGORIES = 10

# More groups than this and the comparison stops being readable.
MAX_GROUPS = 20

# Shapiro-Wilk needs n >= 3.
MIN_GROUP_SIZE = 3


def list_builtin_datasets() -> list[str]:
    return list(BUILTIN_DATASETS)


def load_builtin(name: str) -> pd.DataFrame:
    if name not in BUILTIN_DATASETS:
        raise ValueError(f"Unknown dataset: {name}")
    # Nulls are left in; each analysis drops them for its own two columns.
    return pd.read_csv(DATA_DIR / f"{name}.csv")


def is_numeric_column(series: pd.Series) -> bool:
    # pandas counts bools as numeric, but True/False is a category here.
    if pd.api.types.is_bool_dtype(series):
        return False
    return pd.api.types.is_numeric_dtype(series)


def profile_columns(df: pd.DataFrame) -> dict:
    """Sort columns into numeric, categorical and unusable."""
    numeric = []
    categorical = []
    excluded = []

    for column in df.columns:
        series = df[column]
        distinct = int(series.nunique(dropna=True))

        if distinct < 2:
            excluded.append({"column": column, "reason": "fewer than 2 distinct values"})
            continue

        if is_numeric_column(series):
            numeric.append(column)
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


def problem(analysis: str, status: str, message: str) -> dict:
    # Returned instead of raising, so bad column choices don't become 500s.
    return {"status": status, "analysis": analysis, "message": message}


def missing_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column not in df.columns]


def summarize_group(name: str, values: pd.Series) -> dict:
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
    """Post-hoc for Kruskal-Wallis: which specific pairs of groups differ."""
    # Bonferroni corrects for the number of pairs being tested at once.
    matrix = scikit_posthocs.posthoc_dunn(
        clean, val_col=value_col, group_col=group_col, p_adjust="bonferroni"
    )

    # The matrix is symmetric, so only walk the upper triangle.
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
    """Post-hoc for ANOVA. Tukey adjusts for multiple comparisons itself."""
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
    """Test the two things ANOVA needs: normal groups and equal variances."""
    # Both tests have a null of "the assumption holds", so p > alpha passes.
    normality = []
    for name, values in zip(group_names, groups):
        shapiro_p = float(stats.shapiro(values).pvalue)
        normality.append({
            "group": str(name),
            "shapiro_p": shapiro_p,
            "normal": shapiro_p > ALPHA,
        })

    levene_p = float(stats.levene(*groups).pvalue)

    return {
        "normality": normality,
        "levene_p": levene_p,
        "equal_variance": levene_p > ALPHA,
    }


def explain_test_choice(assumptions: dict) -> str:
    """Build the sentence shown in the UI explaining the chosen test."""
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
    """Compare a numeric column across the groups of a categorical column."""
    analysis = "group_comparison"

    missing = missing_columns(df, [value_col, group_col])
    if missing:
        return problem(analysis, "invalid_columns", f"Column not found: {', '.join(missing)}")
    if not is_numeric_column(df[value_col]):
        return problem(analysis, "invalid_columns", f"'{value_col}' is not numeric, so it can't be the measured value.")

    clean = df[[value_col, group_col]].dropna()

    group_names = sorted(clean[group_col].unique(), key=str)
    groups = [clean.loc[clean[group_col] == name, value_col] for name in group_names]

    # Catch the cases scipy would raise on, and explain them instead.
    if len(groups) < 2:
        return problem(analysis, "insufficient_data", f"'{group_col}' needs at least 2 groups to compare (found {len(groups)}).")
    if len(groups) > MAX_GROUPS:
        return problem(analysis, "insufficient_data", f"'{group_col}' has {len(groups)} groups, which is too many to compare meaningfully (max {MAX_GROUPS}).")
    for name, values in zip(group_names, groups):
        if len(values) < MIN_GROUP_SIZE:
            return problem(analysis, "insufficient_data", f"Group '{name}' has only {len(values)} value(s); each group needs at least {MIN_GROUP_SIZE}.")
    if clean[value_col].nunique() < 2:
        return problem(analysis, "insufficient_data", f"Every value of '{value_col}' is identical, so there is nothing to compare.")

    assumptions = check_assumptions(group_names, groups)
    all_normal = all(item["normal"] for item in assumptions["normality"])
    use_anova = all_normal and assumptions["equal_variance"]

    if use_anova:
        test = "ANOVA"
        statistic, p_value = stats.f_oneway(*groups)
    else:
        test = "Kruskal-Wallis"
        statistic, p_value = stats.kruskal(*groups)

    significant = bool(p_value < ALPHA)

    # Only look for which pairs differ once the overall test says some pair does.
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


def describe_strength(value: float) -> str:
    """Cohen's rule-of-thumb labels for a 0-1 effect size."""
    size = abs(value)
    if size < 0.1:
        return "negligible"
    if size < 0.3:
        return "weak"
    if size < 0.5:
        return "moderate"
    return "strong"


def run_chi_square(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Test whether two categorical columns are associated."""
    analysis = "chi_square"

    missing = missing_columns(df, [col_a, col_b])
    if missing:
        return problem(analysis, "invalid_columns", f"Column not found: {', '.join(missing)}")

    clean = df[[col_a, col_b]].dropna()

    # Counts per category combination: the test input and the heatmap data.
    contingency = pd.crosstab(clean[col_a], clean[col_b])

    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        return problem(analysis, "insufficient_data", "Each column needs at least 2 categories (after dropping missing values).")
    if max(contingency.shape) > MAX_GROUPS:
        return problem(analysis, "insufficient_data", f"Too many categories to compare meaningfully (max {MAX_GROUPS} per column).")

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    # Effect size, since a large n makes even a trivial association significant.
    n = int(contingency.to_numpy().sum())
    cramers_v = float((chi2 / (n * (min(contingency.shape) - 1))) ** 0.5)

    # Chi-square gets unreliable when expected counts are small.
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


# Points beyond this are sampled down for the scatter plot only.
MAX_SCATTER_POINTS = 500


def run_correlation(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Correlate two numeric columns and fit a line. col_a is x, col_b is y."""
    analysis = "correlation"

    missing = missing_columns(df, [col_a, col_b])
    if missing:
        return problem(analysis, "invalid_columns", f"Column not found: {', '.join(missing)}")
    for column in [col_a, col_b]:
        if not is_numeric_column(df[column]):
            return problem(analysis, "invalid_columns", f"'{column}' is not numeric.")

    clean = df[[col_a, col_b]].dropna()
    x = clean[col_a]
    y = clean[col_b]

    if len(clean) < MIN_GROUP_SIZE:
        return problem(analysis, "insufficient_data", f"Need at least {MIN_GROUP_SIZE} rows with both values present (found {len(clean)}).")
    if x.nunique() < 2 or y.nunique() < 2:
        return problem(analysis, "insufficient_data", "A column with a single constant value can't be correlated with anything.")

    pearson_r, pearson_p = stats.pearsonr(x, y)

    # Spearman runs on ranks, so a big gap from Pearson points to a
    # non-linear or outlier-driven relationship.
    spearman_rho, spearman_p = stats.spearmanr(x, y)

    regression = stats.linregress(x, y)

    # Statistics above use every row; only the plot is downsampled.
    plotted = clean
    if len(clean) > MAX_SCATTER_POINTS:
        plotted = clean.sample(n=MAX_SCATTER_POINTS, random_state=0)
    points = [{"x": float(row_x), "y": float(row_y)} for row_x, row_y in zip(plotted[col_a], plotted[col_b])]

    return {
        "status": "ok",
        "analysis": analysis,
        "col_a": col_a,
        "col_b": col_b,
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
        "slope": float(regression.slope),
        "intercept": float(regression.intercept),
        "r_squared": float(regression.rvalue ** 2),
        "significant": bool(pearson_p < ALPHA),
        "strength": describe_strength(pearson_r),
        "direction": "positive" if pearson_r > 0 else "negative",
        "n": int(len(clean)),
        "points": points,
    }


def column_kind(series: pd.Series) -> str:
    """'numeric' or 'categorical', matching the rule in profile_columns."""
    if not is_numeric_column(series):
        return "categorical"
    if series.nunique(dropna=True) <= MAX_NUMERIC_CATEGORIES:
        return "categorical"
    return "numeric"


def analyze(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Pick and run the analysis that fits the two columns' types."""
    missing = missing_columns(df, [col_a, col_b])
    if missing:
        return problem("none", "invalid_columns", f"Column not found: {', '.join(missing)}")
    if col_a == col_b:
        return problem("none", "invalid_columns", "Pick two different columns.")

    kind_a = column_kind(df[col_a])
    kind_b = column_kind(df[col_b])

    if kind_a == "numeric" and kind_b == "categorical":
        return run_group_comparison(df, value_col=col_a, group_col=col_b)
    if kind_a == "categorical" and kind_b == "numeric":
        return run_group_comparison(df, value_col=col_b, group_col=col_a)

    if kind_a == "categorical" and kind_b == "categorical":
        return run_chi_square(df, col_a, col_b)

    return run_correlation(df, col_a, col_b)
