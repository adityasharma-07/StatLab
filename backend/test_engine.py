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


def test_penguins_body_mass_by_species_known_answer(penguins):
    result = engine.run_group_comparison(penguins, "body_mass_g", "species")

    assert result["status"] == "ok"
    assert result["test"] == "Kruskal-Wallis"
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
