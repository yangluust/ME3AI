"""Tests for CPI10 adjustment functions."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import (
    adjust_cpi10_forecasts,
    adjusted_cpi10_availability_summary,
    adjusted_cpi10_forecaster_counts_by_survey,
    adjusted_cpi10_plot_summary_all,
    adjusted_cpi10_plot_summary_revision_ready,
    adjusted_cpi10_revision_ready_counts_by_survey,
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
                "CPI10": 2.50,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 2,
                "forecaster_id": 1,
                "CPI1": 1.20,
                "CPI10": 2.60,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 3,
                "forecaster_id": 1,
                "CPI1": 0.80,
                "CPI10": 2.70,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 4,
                "forecaster_id": 1,
                "CPI1": 0.40,
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


def test_adjusted_cpi10_availability_summary_uses_non_missing_rows():
    """Availability summary should report the non-missing window only."""
    adjusted = pd.DataFrame(
        [
            {"survey_year": 1968, "survey_quarter": 4, "forecaster_id": 1, "adjusted_cpi10": pd.NA},
            {"survey_year": 1969, "survey_quarter": 1, "forecaster_id": 1, "adjusted_cpi10": 2.0},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 1, "adjusted_cpi10": 2.1},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 2, "adjusted_cpi10": 2.2},
        ]
    )

    summary = adjusted_cpi10_availability_summary(adjusted_cpi10=adjusted)

    assert summary["first_survey_year"] == 1969
    assert summary["first_survey_quarter"] == 1
    assert summary["last_survey_year"] == 1969
    assert summary["last_survey_quarter"] == 2
    assert summary["n_surveys_with_data"] == 2
    assert summary["n_rows_with_data"] == 3


def test_adjusted_cpi10_forecaster_counts_by_survey_counts_unique_ids():
    """Forecaster counts should use unique ids among non-missing rows."""
    adjusted = pd.DataFrame(
        [
            {"survey_year": 1969, "survey_quarter": 1, "forecaster_id": 1, "adjusted_cpi10": 2.0},
            {"survey_year": 1969, "survey_quarter": 1, "forecaster_id": 2, "adjusted_cpi10": 2.1},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 1, "adjusted_cpi10": 2.2},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 2, "adjusted_cpi10": pd.NA},
        ]
    )

    counts = adjusted_cpi10_forecaster_counts_by_survey(adjusted_cpi10=adjusted)

    expected = [
        {"survey_year": 1969, "survey_quarter": 1, "n_forecasters_with_adjusted_cpi10": 2},
        {"survey_year": 1969, "survey_quarter": 2, "n_forecasters_with_adjusted_cpi10": 1},
    ]
    assert counts.to_dict("records") == expected


def test_adjusted_cpi10_revision_ready_counts_by_survey_uses_previous_quarter():
    """Revision-ready counts should require the same forecaster in consecutive surveys."""
    adjusted = pd.DataFrame(
        [
            {"survey_year": 1968, "survey_quarter": 4, "forecaster_id": 1, "adjusted_cpi10": 1.9},
            {"survey_year": 1968, "survey_quarter": 4, "forecaster_id": 2, "adjusted_cpi10": 2.0},
            {"survey_year": 1969, "survey_quarter": 1, "forecaster_id": 1, "adjusted_cpi10": 2.1},
            {"survey_year": 1969, "survey_quarter": 1, "forecaster_id": 3, "adjusted_cpi10": 2.2},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 1, "adjusted_cpi10": 2.3},
            {"survey_year": 1969, "survey_quarter": 2, "forecaster_id": 3, "adjusted_cpi10": pd.NA},
        ]
    )

    counts = adjusted_cpi10_revision_ready_counts_by_survey(adjusted_cpi10=adjusted)

    expected = [
        {
            "survey_year": 1969,
            "survey_quarter": 1,
            "n_forecasters_with_prev_quarter_adjusted_cpi10": 1,
        },
        {
            "survey_year": 1969,
            "survey_quarter": 2,
            "n_forecasters_with_prev_quarter_adjusted_cpi10": 1,
        },
    ]
    assert counts.to_dict("records") == expected


def test_adjusted_cpi10_plot_summary_all_computes_survey_statistics():
    """All-forecaster plot summary should compute mean/median by survey."""
    forecast_individual = pd.DataFrame(
        [
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 1, "CPI10": 2.0},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 2, "CPI10": 4.0},
            {"survey_year": 2000, "survey_quarter": 2, "forecaster_id": 1, "CPI10": 3.0},
        ]
    )
    adjusted = pd.DataFrame(
        [
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 1, "adjusted_cpi10": 1.0},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 2, "adjusted_cpi10": 5.0},
            {"survey_year": 2000, "survey_quarter": 2, "forecaster_id": 1, "adjusted_cpi10": 2.0},
        ]
    )

    summary = adjusted_cpi10_plot_summary_all(
        forecast_individual=forecast_individual,
        adjusted_cpi10=adjusted,
    )

    expected = [
        {
            "survey_year": 2000,
            "survey_quarter": 1,
            "mean_cpi10": 3.0,
            "median_cpi10": 3.0,
            "mean_adjusted_cpi10": 3.0,
            "median_adjusted_cpi10": 3.0,
        },
        {
            "survey_year": 2000,
            "survey_quarter": 2,
            "mean_cpi10": 3.0,
            "median_cpi10": 3.0,
            "mean_adjusted_cpi10": 2.0,
            "median_adjusted_cpi10": 2.0,
        },
    ]
    assert summary.to_dict("records") == expected


def test_adjusted_cpi10_plot_summary_revision_ready_filters_to_previous_quarter_panel():
    """Revision-ready plot summary should keep only forecasters present in the previous survey."""
    forecast_individual = pd.DataFrame(
        [
            {"survey_year": 1999, "survey_quarter": 4, "forecaster_id": 1, "CPI10": 2.0},
            {"survey_year": 1999, "survey_quarter": 4, "forecaster_id": 2, "CPI10": 3.0},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 1, "CPI10": 4.0},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 3, "CPI10": 6.0},
        ]
    )
    adjusted = pd.DataFrame(
        [
            {"survey_year": 1999, "survey_quarter": 4, "forecaster_id": 1, "adjusted_cpi10": 1.5},
            {"survey_year": 1999, "survey_quarter": 4, "forecaster_id": 2, "adjusted_cpi10": 2.5},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 1, "adjusted_cpi10": 3.5},
            {"survey_year": 2000, "survey_quarter": 1, "forecaster_id": 3, "adjusted_cpi10": 5.5},
        ]
    )

    summary = adjusted_cpi10_plot_summary_revision_ready(
        forecast_individual=forecast_individual,
        adjusted_cpi10=adjusted,
    )

    expected = [
        {
            "survey_year": 2000,
            "survey_quarter": 1,
            "mean_cpi10": 4.0,
            "median_cpi10": 4.0,
            "mean_adjusted_cpi10": 3.5,
            "median_adjusted_cpi10": 3.5,
        }
    ]
    assert summary.to_dict("records") == expected
