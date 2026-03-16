"""Tests for CPI10 adjustment functions."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import adjust_cpi10_forecasts, get_quarter_specific_value


def _sample_forecast_individual() -> pd.DataFrame:
    """Create minimal cleaned wide table for one forecaster and survey year."""
    return pd.DataFrame(
        [
            {
                "survey_year": 2026,
                "survey_quarter": 1,
                "variable": "CPI",
                "forecaster_id": 1,
                "CPI1": 1.0,
                "CPI10": 2.50,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 2,
                "variable": "CPI",
                "forecaster_id": 1,
                "CPI1": 1.20,
                "CPI10": 2.60,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 3,
                "variable": "CPI",
                "forecaster_id": 1,
                "CPI1": 0.80,
                "CPI10": 2.70,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 4,
                "variable": "CPI",
                "forecaster_id": 1,
                "CPI1": 0.40,
                "CPI10": 2.80,
            },
            {
                "survey_year": 2026,
                "survey_quarter": 2,
                "variable": "CPI10",
                "forecaster_id": 1,
                "CPI1": pd.NA,
                "CPI10": 9.99,
            },
        ]
    )


def test_get_quarter_specific_value_reads_cpi_row_only():
    """Helper should read from the CPI row, not another variable row."""
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
    assert by_quarter[2] == 2.60 - 1.20 / 40
    assert by_quarter[3] == 2.70 - (1.20 + 0.80) / 40
    assert by_quarter[4] == 2.80 - (1.20 + 0.80 + 0.40) / 40
