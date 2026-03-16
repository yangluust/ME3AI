"""Adjust SPF 10-year CPI forecasts using realized CPI1 values.

The cleaned `forecast_individual` table is the input. This module returns a
minimal adjusted table with one row per (survey_year, survey_quarter,
forecaster_id) for variable CPI and one adjusted variable: adjusted_cpi10.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _as_numeric(value: object) -> float | pd.NA:
    """Convert SPF cell content to numeric, coercing placeholders to missing."""
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return pd.NA
    return float(numeric)


def get_quarter_specific_value(
    forecast_individual: pd.DataFrame,
    *,
    survey_year: int,
    survey_quarter: int,
    forecaster_id: int,
    horizon: str,
) -> float | pd.NA:
    """Extract one CPI horizon value from the cleaned wide table."""
    if horizon not in forecast_individual.columns:
        raise KeyError(f"Missing horizon column: {horizon}")

    mask = (
        (forecast_individual["variable"] == "CPI")
        & (forecast_individual["survey_year"] == survey_year)
        & (forecast_individual["survey_quarter"] == survey_quarter)
        & (forecast_individual["forecaster_id"] == forecaster_id)
    )
    matches = forecast_individual.loc[mask, horizon]
    if len(matches) == 0:
        raise KeyError(
            "No CPI row for "
            f"(survey_year={survey_year}, survey_quarter={survey_quarter}, "
            f"forecaster_id={forecaster_id})."
        )
    if len(matches) > 1:
        raise ValueError(
            "Duplicate CPI rows for "
            f"(survey_year={survey_year}, survey_quarter={survey_quarter}, "
            f"forecaster_id={forecaster_id})."
        )
    return _as_numeric(matches.iloc[0])


def _sum_terms(terms: Iterable[float | pd.NA]) -> float | pd.NA:
    """Sum numeric terms; return missing if any required term is missing."""
    values = list(terms)
    if any(pd.isna(value) for value in values):
        return pd.NA
    return float(sum(float(value) for value in values))


def adjust_cpi10_forecasts(forecast_individual: pd.DataFrame) -> pd.DataFrame:
    """Return minimal table of adjusted 10-year CPI forecasts."""
    required = {"survey_year", "survey_quarter", "variable", "forecaster_id", "CPI1", "CPI10"}
    missing = required.difference(forecast_individual.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    cpi_rows = (
        forecast_individual.loc[
            forecast_individual["variable"] == "CPI",
            ["survey_year", "survey_quarter", "forecaster_id"],
        ]
        .drop_duplicates()
        .sort_values(["survey_year", "survey_quarter", "forecaster_id"])
    )

    adjusted_rows: list[dict[str, object]] = []
    for row in cpi_rows.itertuples(index=False):
        cpi10 = get_quarter_specific_value(
            forecast_individual=forecast_individual,
            survey_year=int(row.survey_year),
            survey_quarter=int(row.survey_quarter),
            forecaster_id=int(row.forecaster_id),
            horizon="CPI10",
        )

        if row.survey_quarter == 1:
            adjusted = cpi10
        elif row.survey_quarter == 2:
            cpi1_q2 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            adjusted = pd.NA if pd.isna(cpi10) or pd.isna(cpi1_q2) else float(cpi10) - float(cpi1_q2) / 40
        elif row.survey_quarter == 3:
            cpi1_q2 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q3 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=3,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            realized = _sum_terms([cpi1_q2, cpi1_q3])
            adjusted = pd.NA if pd.isna(cpi10) or pd.isna(realized) else float(cpi10) - float(realized) / 40
        else:
            cpi1_q2 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q3 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=3,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q4 = get_quarter_specific_value(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=4,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            realized = _sum_terms([cpi1_q2, cpi1_q3, cpi1_q4])
            adjusted = pd.NA if pd.isna(cpi10) or pd.isna(realized) else float(cpi10) - float(realized) / 40

        adjusted_rows.append(
            {
                "survey_year": int(row.survey_year),
                "survey_quarter": int(row.survey_quarter),
                "forecaster_id": int(row.forecaster_id),
                "adjusted_cpi10": adjusted,
            }
        )

    out = pd.DataFrame(adjusted_rows)
    if len(out) == 0:
        return pd.DataFrame(columns=["survey_year", "survey_quarter", "forecaster_id", "adjusted_cpi10"])
    out["survey_year"] = out["survey_year"].astype("Int64")
    out["survey_quarter"] = out["survey_quarter"].astype("Int64")
    out["forecaster_id"] = out["forecaster_id"].astype("Int64")
    out["adjusted_cpi10"] = pd.to_numeric(out["adjusted_cpi10"], errors="coerce")
    return out
