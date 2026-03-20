"""Tests for forecast-revision regression functions."""

import sys
from typing import Dict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_regression import (
    build_specification_comparison_panel,
    plot_cumulative_forecast_revision_comparison,
    plot_specification_comparison,
    run_forecast_revision_regressions,
)


def _sample_regression_config() -> Dict[str, int]:
    """Create the default bounded sample window used in tests."""
    return {
        "sample_start_year": 1991,
        "sample_start_quarter": 4,
        "sample_end_year": 2024,
        "sample_end_quarter": 2,
    }


def _sample_regression_dataset() -> pd.DataFrame:
    """Create a small survey-level regression dataset with exact linear fits."""
    return pd.DataFrame(
        [
            {
                "survey_year": 1991,
                "survey_quarter": 3,
                "r_bar": pd.NA,
                "n_bar": pd.NA,
                "rho_bar_prev": 0.5,
                "z2": pd.NA,
                "z3": pd.NA,
                "zP": pd.NA,
                "matched_sample_size": 1,
            },
            {
                "survey_year": 1991,
                "survey_quarter": 4,
                "r_bar": 3.0,
                "n_bar": 1.0,
                "rho_bar_prev": 0.5,
                "z2": 1.0,
                "z3": 1.0,
                "zP": 0.125,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 1992,
                "survey_quarter": 1,
                "r_bar": 5.0,
                "n_bar": 2.0,
                "rho_bar_prev": 0.5,
                "z2": 2.0,
                "z3": 2.0,
                "zP": 0.25,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 1992,
                "survey_quarter": 2,
                "r_bar": 7.0,
                "n_bar": 3.0,
                "rho_bar_prev": 0.5,
                "z2": 3.0,
                "z3": 3.0,
                "zP": 0.375,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 2024,
                "survey_quarter": 2,
                "r_bar": 9.0,
                "n_bar": 4.0,
                "rho_bar_prev": 0.5,
                "z2": 4.0,
                "z3": 4.0,
                "zP": 0.5,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 2024,
                "survey_quarter": 3,
                "r_bar": 11.0,
                "n_bar": 5.0,
                "rho_bar_prev": 0.5,
                "z2": 5.0,
                "z3": 5.0,
                "zP": 0.625,
                "matched_sample_size": 2,
            },
        ]
    )


def test_run_forecast_revision_regressions_returns_statistics_and_fitted_values():
    """Regression runner should return one stats row per model and fitted columns."""
    regression_dataset = _sample_regression_dataset()

    regression_statistics, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
        config=_sample_regression_config(),
    )

    assert list(regression_statistics["model"]) == ["model_1", "model_2", "model_3", "model_P"]
    assert list(fitted_values.columns) == [
        "survey_year",
        "survey_quarter",
        "fitted_model_1",
        "fitted_model_2",
        "fitted_model_3",
        "fitted_model_P",
    ]


def test_run_forecast_revision_regressions_matches_exact_linear_fit():
    """Exact linear data should produce intercept 1, slope 2, zero RMSE, and full fit."""
    regression_dataset = _sample_regression_dataset()

    regression_statistics, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
        config=_sample_regression_config(),
    )

    expected_estimates = {
        "model_1": 2.0,
        "model_2": 2.0,
        "model_3": 2.0,
        "model_P": 16.0,
    }
    for row in regression_statistics.itertuples(index=False):
        assert float(row.estimate) == pytest.approx(expected_estimates[str(row.model)])
        assert float(row.rmse) == pytest.approx(0.0)
        assert int(row.sample_size) == 4
        assert float(row.adjusted_r_squared) == pytest.approx(1.0)
        assert float(row.p_value) == pytest.approx(0.0)

    exact_fit = fitted_values.loc[fitted_values["fitted_model_1"].notna()].copy()
    assert exact_fit["fitted_model_1"].tolist() == pytest.approx([3.0, 5.0, 7.0, 9.0])


def test_plot_cumulative_forecast_revision_comparison_filters_from_1991_q4():
    """Comparison plot should use the bounded 1991:Q4 to 2024:Q2 window."""
    regression_dataset = _sample_regression_dataset()
    _, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
        config=_sample_regression_config(),
    )

    figure, plot_panel = plot_cumulative_forecast_revision_comparison(
        regression_dataset=regression_dataset,
        fitted_values=fitted_values,
        config=_sample_regression_config(),
    )

    assert plot_panel[["survey_year", "survey_quarter"]].to_dict("records") == [
        {"survey_year": 1991, "survey_quarter": 4},
        {"survey_year": 1992, "survey_quarter": 1},
        {"survey_year": 1992, "survey_quarter": 2},
        {"survey_year": 2024, "survey_quarter": 2},
    ]
    assert plot_panel["cumulative_data"].tolist() == pytest.approx([3.0, 8.0, 15.0, 24.0])
    assert len(figure.axes[0].lines) == 5
    plt.close(figure)


def test_run_forecast_revision_regressions_uses_configured_sample_window():
    """Changing the config window should change the estimation sample."""
    regression_dataset = _sample_regression_dataset()
    config = {
        "sample_start_year": 1992,
        "sample_start_quarter": 1,
        "sample_end_year": 2024,
        "sample_end_quarter": 2,
    }

    regression_statistics, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
        config=config,
    )

    for row in regression_statistics.itertuples(index=False):
        assert int(row.sample_size) == 3
    assert fitted_values["fitted_model_1"].tolist() == pytest.approx([5.0, 7.0, 9.0])


def test_build_specification_comparison_panel_aligns_series_by_survey():
    """Comparison panel should align raw and adjusted survey-level series by date."""
    raw_dataset = _sample_regression_dataset()
    adjusted_dataset = _sample_regression_dataset().copy()
    adjusted_dataset["r_bar"] = adjusted_dataset["r_bar"].where(
        adjusted_dataset["r_bar"].isna(),
        adjusted_dataset["r_bar"] + 1.0,
    )

    comparison_panel = build_specification_comparison_panel(
        regression_datasets={
            "raw_cpi10": raw_dataset,
            "adjusted_cpi10": adjusted_dataset,
        },
        value_column="r_bar",
        config=_sample_regression_config(),
    )

    assert comparison_panel["raw_cpi10"].tolist() == pytest.approx([3.0, 5.0, 7.0, 9.0])
    assert comparison_panel["adjusted_cpi10"].tolist() == pytest.approx([4.0, 6.0, 8.0, 10.0])


def test_plot_specification_comparison_draws_two_specification_lines():
    """Specification comparison plot should include raw and adjusted lines."""
    comparison_panel = pd.DataFrame(
        [
            {
                "survey_year": 1991,
                "survey_quarter": 4,
                "raw_cpi10": 1.0,
                "adjusted_cpi10": 1.5,
            },
            {
                "survey_year": 1992,
                "survey_quarter": 1,
                "raw_cpi10": 2.0,
                "adjusted_cpi10": 2.5,
            },
        ]
    )

    figure = plot_specification_comparison(
        comparison_panel=comparison_panel,
        raw_column="raw_cpi10",
        adjusted_column="adjusted_cpi10",
        title="Comparison",
        y_label="Value",
    )

    assert len(figure.axes[0].lines) == 2
    plt.close(figure)
