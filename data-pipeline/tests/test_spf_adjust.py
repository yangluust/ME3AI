"""Tests for forecast-revision construction functions."""

import sys
from pathlib import Path

import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import (
    adjust_cpi10_forecasts,
    construct_long_term_inflation_expectation,
    construct_inflation_news,
    construct_reputation_measure,
    construct_regression_dataset,
    get_quarter_specific_value,
)


def _sample_forecast_individual() -> pd.DataFrame:
    """Create minimal cleaned wide table for one forecaster and survey year."""
    return pd.DataFrame(
        [
            {
                "survey_year": 2026,
                "survey_quarter": 1,
                "forecaster_id": 1,
                "CPI1": 1.0,
                "CPI2": 1.1,
                "CPI10": 2.50,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 2,
                "forecaster_id": 1,
                "CPI1": 1.20,
                "CPI2": 1.3,
                "CPI10": 2.60,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 3,
                "forecaster_id": 1,
                "CPI1": 0.80,
                "CPI2": 0.9,
                "CPI10": 2.70,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 4,
                "forecaster_id": 1,
                "CPI1": 0.40,
                "CPI2": 0.5,
                "CPI10": 2.80,
            },
        ]
    )


def test_get_quarter_specific_value_reads_requested_horizon():
    """Helper should read the requested horizon from the keyed row."""
    forecast_individual = _sample_forecast_individual()

    value = get_quarter_specific_value(
        forecast_individual=forecast_individual,
        survey_year=2026,
        survey_quarter=2,
        forecaster_id=1,
        horizon="CPI10",
    )

    assert value == 2.60


def test_adjust_cpi10_forecasts_returns_minimal_table():
    """Adjusted output should contain keys plus adjusted variable only."""
    forecast_individual = _sample_forecast_individual()

    adjusted = adjust_cpi10_forecasts(forecast_individual=forecast_individual)

    assert list(adjusted.columns) == [
        "survey_year",
        "survey_quarter",
        "forecaster_id",
        "adjusted_cpi10",
    ]


def test_adjust_cpi10_forecasts_applies_quarter_rules():
    """Adjustment should follow Q1/Q2/Q3/Q4 rules from the source of truth."""
    forecast_individual = _sample_forecast_individual()

    adjusted = adjust_cpi10_forecasts(forecast_individual=forecast_individual)
    by_quarter = {
        int(row.survey_quarter): float(row.adjusted_cpi10)
        for row in adjusted.itertuples(index=False)
    }

    assert by_quarter[1] == 2.50
    assert by_quarter[2] == (2.60 * 40 - 1.20) / 39
    assert by_quarter[3] == (2.70 * 40 - (1.20 + 0.80)) / 38
    assert by_quarter[4] == (2.80 * 40 - (1.20 + 0.80 + 0.40)) / 37


def test_construct_long_term_inflation_expectation_returns_x_table():
    """Long-term expectation constructor should return x keyed by forecaster."""
    forecast_individual = _sample_forecast_individual()

    x_table = construct_long_term_inflation_expectation(
        forecast_individual=forecast_individual,
    )

    assert list(x_table.columns) == [
        "survey_year",
        "survey_quarter",
        "forecaster_id",
        "x",
    ]
    assert float(x_table.loc[x_table["survey_quarter"] == 2, "x"].iloc[0]) == (
        2.60 * 40 - 1.20
    ) / 39


def test_construct_inflation_news_returns_minimal_table():
    """Inflation news output should contain keys plus inflation_news only."""
    forecast_individual = pd.DataFrame(
        [
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 1, "CPI1": 0.6, "CPI2": 0.7},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "CPI1": 1.0, "CPI2": 1.1},
        ]
    )

    inflation_news = construct_inflation_news(forecast_individual=forecast_individual)

    assert list(inflation_news.columns) == [
        "survey_year",
        "survey_quarter",
        "forecaster_id",
        "inflation_news",
    ]


def test_construct_inflation_news_uses_previous_survey_timing():
    """Inflation news should subtract lagged CPI2 from current-quarter CPI1."""
    forecast_individual = pd.DataFrame(
        [
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 1, "CPI1": 0.6, "CPI2": 0.7},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "CPI1": 1.0, "CPI2": 1.1},
            {"survey_year": 2026, "survey_quarter": 2, "forecaster_id": 1, "CPI1": 1.2, "CPI2": 1.3},
        ]
    )

    inflation_news = construct_inflation_news(forecast_individual=forecast_individual)
    by_quarter = {
        (int(row.survey_year), int(row.survey_quarter)): float(row.inflation_news)
        for row in inflation_news.loc[inflation_news["inflation_news"].notna()].itertuples(index=False)
    }

    assert by_quarter[(2026, 1)] == 1.0 - 0.7
    assert by_quarter[(2026, 2)] == 1.2 - 1.1
    assert pd.isna(
        inflation_news.loc[
            (inflation_news["survey_year"] == 2025)
            & (inflation_news["survey_quarter"] == 4)
            & (inflation_news["forecaster_id"] == 1),
            "inflation_news",
        ].iloc[0]
    )


def test_construct_reputation_measure_preserves_input_keys():
    """Reputation output should preserve keys and append rho."""
    x_table = pd.DataFrame(
        [
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "x": 2.1},
            {"survey_year": 2026, "survey_quarter": 2, "forecaster_id": 2, "x": 2.3},
        ]
    )
    config = {"q": 0.2, "pi_target": 2.0, "pi_NE": 1.0, "z_a": 3.0, "z_alpha": 0.5}

    rho = construct_reputation_measure(x_table=x_table, config=config)

    assert list(rho.columns) == ["survey_year", "survey_quarter", "forecaster_id", "rho"]


def test_construct_reputation_measure_applies_formula():
    """Reputation should solve the linear mixture expression row by row."""
    x_table = pd.DataFrame(
        [
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "x": 2.1},
            {"survey_year": 2026, "survey_quarter": 2, "forecaster_id": 1, "x": pd.NA},
        ]
    )
    config = {"q": 0.25, "pi_target": 2.0, "pi_NE": 1.0, "z_a": 3.0, "z_alpha": 0.0}

    rho = construct_reputation_measure(x_table=x_table, config=config)
    target_term = (1.0 - 0.25) * 2.0 + 0.25 * 3.0
    ne_term = (1.0 - 0.25) * 1.0 + 0.25 * 0.0

    assert float(rho.loc[0, "rho"]) == (2.1 - ne_term) / (target_term - ne_term)
    assert pd.isna(rho.loc[1, "rho"])


def test_construct_regression_dataset_uses_matched_sample_means():
    """Regression dataset should average only forecasters matched across s and s-1."""
    x_table = pd.DataFrame(
        [
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 1, "x": 1.0},
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 2, "x": 2.0},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "x": 1.5},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 2, "x": 2.5},
            {"survey_year": 2026, "survey_quarter": 2, "forecaster_id": 1, "x": 2.0},
        ]
    )
    inflation_news = pd.DataFrame(
        [
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "inflation_news": 0.2},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 2, "inflation_news": 0.4},
            {"survey_year": 2026, "survey_quarter": 2, "forecaster_id": 1, "inflation_news": 0.6},
        ]
    )
    reputation_measure = pd.DataFrame(
        [
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 1, "rho": 0.25},
            {"survey_year": 2025, "survey_quarter": 4, "forecaster_id": 2, "rho": 0.75},
            {"survey_year": 2026, "survey_quarter": 1, "forecaster_id": 1, "rho": 0.5},
        ]
    )

    regression_dataset = construct_regression_dataset(
        x_table=x_table,
        inflation_news=inflation_news,
        reputation_measure=reputation_measure,
    )

    row_q1 = regression_dataset.loc[
        (regression_dataset["survey_year"] == 2026)
        & (regression_dataset["survey_quarter"] == 1)
    ].iloc[0]
    row_q2 = regression_dataset.loc[
        (regression_dataset["survey_year"] == 2026)
        & (regression_dataset["survey_quarter"] == 2)
    ].iloc[0]

    assert int(row_q1["prev_survey_year"]) == 2025
    assert int(row_q1["prev_survey_quarter"]) == 4
    assert float(row_q1["r_bar"]) == pytest.approx(0.5)
    assert float(row_q1["n_bar"]) == pytest.approx(0.3)
    assert float(row_q1["rho_bar_prev"]) == pytest.approx(0.5)
    assert float(row_q1["z2"]) == pytest.approx(0.075)
    assert float(row_q1["z3"]) == pytest.approx(0.0375)
    assert int(row_q1["matched_sample_size"]) == 2

    assert int(row_q2["prev_survey_year"]) == 2026
    assert int(row_q2["prev_survey_quarter"]) == 1
    assert float(row_q2["r_bar"]) == pytest.approx(0.5)
    assert float(row_q2["n_bar"]) == pytest.approx(0.6)
    assert float(row_q2["rho_bar_prev"]) == pytest.approx(0.5)
    assert float(row_q2["z2"]) == pytest.approx(0.15)
    assert float(row_q2["z3"]) == pytest.approx(0.075)
    assert int(row_q2["matched_sample_size"]) == 1
