"""Engine tests. Fixtures are synthetic data or the bundled public datasets only."""

import numpy as np
import pandas as pd
import pytest

import engine


def make_groups(samples: dict) -> pd.DataFrame:
    """Build a long-format frame from {"group name": array of values}."""
    frames = [pd.DataFrame({"group": name, "value": values}) for name, values in samples.items()]
    return pd.concat(frames, ignore_index=True)


@pytest.fixture
def penguins() -> pd.DataFrame:
    return engine.load_builtin("penguins")


@pytest.fixture
def tips() -> pd.DataFrame:
    return engine.load_builtin("tips")


# --- profile_columns --------------------------------------------------------

def test_profile_columns_classifies_known_frame():
    df = pd.DataFrame({
        "height": np.linspace(150, 200, 30),          # numeric, many values
        "rating": [1, 2, 3] * 10,                     # numeric but low-cardinality
        "color": ["red", "green", "blue"] * 10,       # text category
        "member": [True, False] * 15,                 # bool category
        "constant": ["same"] * 30,                    # only 1 group -> excluded
        "id": [f"row-{i}" for i in range(30)],        # too many groups -> excluded
    })
    profile = engine.profile_columns(df)

    assert profile["numeric"] == ["height", "rating"]
    assert profile["categorical"] == ["rating", "color", "member"]
    assert [item["column"] for item in profile["excluded"]] == ["constant", "id"]
    assert profile["row_count"] == 30


def test_profile_columns_on_tips(tips):
    profile = engine.profile_columns(tips)
    assert profile["numeric"] == ["total_bill", "tip", "size"]
    assert set(profile["categorical"]) == {"sex", "smoker", "day", "time", "size"}


# --- group comparison -------------------------------------------------------

def test_clearly_different_groups_are_significant():
    rng = np.random.default_rng(0)
    df = make_groups({
        "low": rng.normal(10, 1, 40),
        "mid": rng.normal(20, 1, 40),
        "high": rng.normal(30, 1, 40),
    })
    result = engine.run_group_comparison(df, "value", "group")

    assert result["status"] == "ok"
    assert result["significant"] is True
    assert result["group_count"] == 3
    assert len(result["pairwise"]) == 3


def test_overlapping_groups_are_not_significant():
    rng = np.random.default_rng(1)
    df = make_groups({
        "a": rng.normal(50, 5, 40),
        "b": rng.normal(50, 5, 40),
        "c": rng.normal(50, 5, 40),
    })
    result = engine.run_group_comparison(df, "value", "group")

    assert result["status"] == "ok"
    assert result["significant"] is False
    assert result["pairwise"] == []


def test_normal_equal_variance_groups_choose_anova():
    rng = np.random.default_rng(42)
    df = make_groups({
        "a": rng.normal(10, 2, 50),
        "b": rng.normal(12, 2, 50),
        "c": rng.normal(14, 2, 50),
    })
    result = engine.run_group_comparison(df, "value", "group")

    assert result["test"] == "ANOVA"
    assert all(item["normal"] for item in result["assumptions"]["normality"])
    assert result["assumptions"]["equal_variance"] is True
    assert result["significant"] is True
    assert result["posthoc_test"] == "Tukey HSD"
    assert len(result["pairwise"]) == 3


def test_skewed_groups_choose_kruskal_wallis():
    rng = np.random.default_rng(42)
    df = make_groups({
        "a": rng.exponential(1.0, 50),
        "b": rng.exponential(2.0, 50),
        "c": rng.exponential(4.0, 50),
    })
    result = engine.run_group_comparison(df, "value", "group")

    assert result["test"] == "Kruskal-Wallis"
    assert any(not item["normal"] for item in result["assumptions"]["normality"])
    assert "non-normal" in result["test_reason"]


def test_penguins_body_mass_by_species_known_answer(penguins):
    result = engine.run_group_comparison(penguins, "body_mass_g", "species")

    assert result["status"] == "ok"

    # Adelie fails Shapiro-Wilk and Levene shows unequal variance, so the
    # engine must recommend Kruskal-Wallis rather than ANOVA.
    normality = {item["group"]: item for item in result["assumptions"]["normality"]}
    assert normality["Adelie"]["normal"] is False
    assert normality["Adelie"]["shapiro_p"] == pytest.approx(0.03, abs=0.015)
    assert result["assumptions"]["levene_p"] == pytest.approx(0.006, abs=0.002)
    assert result["assumptions"]["equal_variance"] is False
    assert result["test"] == "Kruskal-Wallis"
    assert "Adelie" in result["test_reason"]

    assert result["statistic"] == pytest.approx(217.6, abs=0.1)
    assert result["p_value"] < 1e-40
    assert result["significant"] is True
    assert result["n"] == 342  # 344 rows minus 2 with a missing body mass

    medians = {group["name"]: group["median"] for group in result["groups"]}
    assert medians == {"Adelie": 3700, "Chinstrap": 3700, "Gentoo": 5000}

    # Gentoo is the heavy species; Adelie and Chinstrap are indistinguishable.
    pairs = {(pair["group_a"], pair["group_b"]): pair["significant"] for pair in result["pairwise"]}
    assert pairs[("Adelie", "Gentoo")] is True
    assert pairs[("Chinstrap", "Gentoo")] is True
    assert pairs[("Adelie", "Chinstrap")] is False
    assert medians["Gentoo"] > medians["Adelie"]


# --- guards: bad input gives a status, never an exception -------------------

def test_single_group_is_insufficient_data():
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0], "group": ["only"] * 4})
    result = engine.run_group_comparison(df, "value", "group")
    assert result["status"] == "insufficient_data"


def test_too_few_rows_is_insufficient_data():
    df = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0], "group": ["a", "a", "b", "b"]})
    result = engine.run_group_comparison(df, "value", "group")
    assert result["status"] == "insufficient_data"


def test_all_null_column_is_insufficient_data():
    df = pd.DataFrame({"value": [np.nan] * 6, "group": ["a", "b", "c"] * 2})
    result = engine.run_group_comparison(df, "value", "group")
    assert result["status"] == "insufficient_data"


def test_unknown_column_is_reported_not_raised(penguins):
    result = engine.run_group_comparison(penguins, "no_such_column", "species")
    assert result["status"] == "invalid_columns"


# --- chi-square -------------------------------------------------------------

def test_tips_day_by_time_known_answer(tips):
    result = engine.run_chi_square(tips, "day", "time")

    assert result["status"] == "ok"
    assert result["chi2"] == pytest.approx(217.1, abs=0.1)
    assert result["p_value"] < 1e-40
    assert result["dof"] == 3
    assert result["significant"] is True
    assert result["cramers_v"] == pytest.approx(0.94, abs=0.01)

    # The heatmap data: weekends are dinner-only.
    table = result["contingency"]
    sat_row = table["counts"][table["rows"].index("Sat")]
    assert sat_row[table["cols"].index("Lunch")] == 0
    assert sat_row[table["cols"].index("Dinner")] == 87


def test_independent_categories_are_not_significant():
    rng = np.random.default_rng(3)
    df = pd.DataFrame({
        "coin": rng.choice(["heads", "tails"], 400),
        "shirt": rng.choice(["red", "green", "blue"], 400),
    })
    result = engine.run_chi_square(df, "coin", "shirt")

    assert result["status"] == "ok"
    assert result["significant"] is False
    assert result["cramers_v"] < 0.2


def test_chi_square_with_one_category_is_insufficient_data():
    df = pd.DataFrame({"a": ["x"] * 10, "b": ["y", "z"] * 5})
    result = engine.run_chi_square(df, "a", "b")
    assert result["status"] == "insufficient_data"


# --- dispatcher -------------------------------------------------------------

def test_analyze_routes_numeric_and_categorical_to_group_comparison(penguins):
    result = engine.analyze(penguins, "body_mass_g", "species")
    assert result["analysis"] == "group_comparison"

    # Column order must not matter: the numeric column is always the value.
    flipped = engine.analyze(penguins, "species", "body_mass_g")
    assert flipped["analysis"] == "group_comparison"
    assert flipped["value_col"] == "body_mass_g"
    assert flipped["statistic"] == pytest.approx(result["statistic"])


def test_analyze_routes_two_categoricals_to_chi_square(tips):
    assert engine.analyze(tips, "day", "time")["analysis"] == "chi_square"
    # `size` is numeric but low-cardinality, so it counts as categorical.
    assert engine.analyze(tips, "size", "day")["analysis"] == "chi_square"


def test_analyze_rejects_same_column_twice(tips):
    assert engine.analyze(tips, "day", "day")["status"] == "invalid_columns"


# --- correlation ------------------------------------------------------------

def test_penguins_flipper_vs_body_mass_known_answer(penguins):
    result = engine.run_correlation(penguins, "flipper_length_mm", "body_mass_g")

    assert result["status"] == "ok"
    assert result["pearson_r"] == pytest.approx(0.87, abs=0.01)
    assert result["spearman_rho"] == pytest.approx(0.84, abs=0.01)
    # 49.69 g per mm, using all 342 rows that have both measurements. (Dropping
    # rows with ANY missing value, e.g. sex, leaves 333 rows and gives ~50.2.)
    assert result["slope"] == pytest.approx(49.69, abs=0.05)
    assert result["r_squared"] == pytest.approx(0.76, abs=0.01)
    assert result["significant"] is True
    assert result["direction"] == "positive"
    assert len(result["points"]) == result["n"] == 342


def test_unrelated_numbers_are_not_correlated():
    rng = np.random.default_rng(5)
    df = pd.DataFrame({"x": rng.normal(0, 1, 200), "y": rng.normal(0, 1, 200)})
    result = engine.run_correlation(df, "x", "y")

    assert result["significant"] is False
    assert abs(result["pearson_r"]) < 0.2


def test_large_dataset_is_downsampled_for_plotting_only():
    rng = np.random.default_rng(6)
    x = rng.normal(0, 1, 2000)
    df = pd.DataFrame({"x": x, "y": 3 * x + rng.normal(0, 0.1, 2000)})
    result = engine.run_correlation(df, "x", "y")

    assert result["n"] == 2000                   # statistics use every row
    assert len(result["points"]) == 500          # the scatter plot does not
    assert result["slope"] == pytest.approx(3, abs=0.05)


def test_constant_column_correlation_is_insufficient_data():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [5.0] * 4})
    result = engine.run_correlation(df, "x", "y")
    assert result["status"] == "insufficient_data"


def test_analyze_routes_two_numerics_to_correlation(penguins):
    result = engine.analyze(penguins, "flipper_length_mm", "body_mass_g")
    assert result["analysis"] == "correlation"
