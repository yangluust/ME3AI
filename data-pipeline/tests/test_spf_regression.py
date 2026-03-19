"""Tests for forecast-revision regression functions."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_regression import (
    plot_cumulative_forecast_revision_comparison,
    run_forecast_revision_regressions,
)


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
                "matched_sample_size": 1,
            },
            {
                "survey_year": 1991,
                "survey_quarter": 4,
                "r_bar": 2.0,
                "n_bar": 1.0,
                "rho_bar_prev": 0.5,
                "z2": 1.0,
                "z3": 1.0,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 1992,
                "survey_quarter": 1,
                "r_bar": 4.0,
                "n_bar": 2.0,
                "rho_bar_prev": 0.5,
                "z2": 2.0,
                "z3": 2.0,
                "matched_sample_size": 2,
            },
            {
                "survey_year": 1992,
                "survey_quarter": 2,
                "r_bar": 6.0,
                "n_bar": 3.0,
                "rho_bar_prev": 0.5,
                "z2": 3.0,
                "z3": 3.0,
                "matched_sample_size": 2,
            },
        ]
    )


def test_run_forecast_revision_regressions_returns_statistics_and_fitted_values():
    """Regression runner should return one stats row per model and fitted columns."""
    regression_dataset = _sample_regression_dataset()

    regression_statistics, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
    )

    assert list(regression_statistics["model"]) == ["model_1", "model_2", "model_3"]
    assert list(fitted_values.columns) == [
        "survey_year",
        "survey_quarter",
        "fitted_model_1",
        "fitted_model_2",
        "fitted_model_3",
    ]


def test_run_forecast_revision_regressions_matches_exact_linear_fit():
    """Exact linear data should produce estimate 2, zero RMSE, and full fit."""
    regression_dataset = _sample_regression_dataset()

    regression_statistics, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
    )

    for row in regression_statistics.itertuples(index=False):
        assert float(row.estimate) == 2.0
        assert float(row.rmse) == 0.0
        assert int(row.sample_size) == 3
        assert float(row.adjusted_r_squared) == 1.0
        assert float(row.p_value) == 0.0

    exact_fit = fitted_values.loc[fitted_values["fitted_model_1"].notna()].copy()
    assert exact_fit["fitted_model_1"].tolist() == [2.0, 4.0, 6.0]


def test_plot_cumulative_forecast_revision_comparison_filters_from_1991_q4():
    """Comparison plot should start at 1991:Q4 and include four plotted lines."""
    regression_dataset = _sample_regression_dataset()
    _, fitted_values = run_forecast_revision_regressions(
        regression_dataset=regression_dataset,
    )

    figure, plot_panel = plot_cumulative_forecast_revision_comparison(
        regression_dataset=regression_dataset,
        fitted_values=fitted_values,
    )

    assert plot_panel[["survey_year", "survey_quarter"]].to_dict("records") == [
        {"survey_year": 1991, "survey_quarter": 4},
        {"survey_year": 1992, "survey_quarter": 1},
        {"survey_year": 1992, "survey_quarter": 2},
    ]
    assert plot_panel["cumulative_data"].tolist() == [2.0, 6.0, 12.0]
    assert len(figure.axes[0].lines) == 4
    plt.close(figure)
