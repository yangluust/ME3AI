"""Adjust SPF 10-year CPI forecasts using realized CPI1 values.

The cleaned `forecast_individual` table is the input. This module returns a
minimal adjusted table with one row per (survey_year, survey_quarter,
forecaster_id) and one adjusted variable: adjusted_cpi10.
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
    """Extract one horizon value from the cleaned wide table."""
    if horizon not in forecast_individual.columns:
        raise KeyError(f"Missing horizon column: {horizon}")

    mask = (
        (forecast_individual["survey_year"] == survey_year)
        & (forecast_individual["survey_quarter"] == survey_quarter)
        & (forecast_individual["forecaster_id"] == forecaster_id)
    )
    matches = forecast_individual.loc[mask, horizon]
    if len(matches) == 0:
        raise KeyError(
            "No row for "
            f"(survey_year={survey_year}, survey_quarter={survey_quarter}, "
            f"forecaster_id={forecaster_id})."
        )
    if len(matches) > 1:
        raise ValueError(
            "Duplicate rows for "
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


def _get_value_or_missing(
    forecast_individual: pd.DataFrame,
    *,
    survey_year: int,
    survey_quarter: int,
    forecaster_id: int,
    horizon: str,
) -> float | pd.NA:
    """Return horizon value or missing when the required row is unavailable."""
    try:
        return get_quarter_specific_value(
            forecast_individual=forecast_individual,
            survey_year=survey_year,
            survey_quarter=survey_quarter,
            forecaster_id=forecaster_id,
            horizon=horizon,
        )
    except KeyError:
        return pd.NA


def adjust_cpi10_forecasts(forecast_individual: pd.DataFrame) -> pd.DataFrame:
    """Return minimal table of adjusted 10-year CPI forecasts."""
    required = {"survey_year", "survey_quarter", "forecaster_id", "CPI1", "CPI10"}
    missing = required.difference(forecast_individual.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    rows = (
        forecast_individual.loc[:, ["survey_year", "survey_quarter", "forecaster_id"]]
        .drop_duplicates()
        .sort_values(["survey_year", "survey_quarter", "forecaster_id"])
    )

    adjusted_rows: list[dict[str, object]] = []
    for row in rows.itertuples(index=False):
        cpi10 = _get_value_or_missing(
            forecast_individual=forecast_individual,
            survey_year=int(row.survey_year),
            survey_quarter=int(row.survey_quarter),
            forecaster_id=int(row.forecaster_id),
            horizon="CPI10",
        )

        if row.survey_quarter == 1:
            adjusted = cpi10
        elif row.survey_quarter == 2:
            cpi1_q2 = _get_value_or_missing(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            adjusted = pd.NA if pd.isna(cpi10) or pd.isna(cpi1_q2) else float(cpi10) - float(cpi1_q2) / 40
        elif row.survey_quarter == 3:
            cpi1_q2 = _get_value_or_missing(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q3 = _get_value_or_missing(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=3,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            realized = _sum_terms([cpi1_q2, cpi1_q3])
            adjusted = pd.NA if pd.isna(cpi10) or pd.isna(realized) else float(cpi10) - float(realized) / 40
        else:
            cpi1_q2 = _get_value_or_missing(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=2,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q3 = _get_value_or_missing(
                forecast_individual=forecast_individual,
                survey_year=int(row.survey_year),
                survey_quarter=3,
                forecaster_id=int(row.forecaster_id),
                horizon="CPI1",
            )
            cpi1_q4 = _get_value_or_missing(
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


def adjusted_cpi10_availability_summary(adjusted_cpi10: pd.DataFrame) -> dict[str, object]:
    """Summarize the availability window for non-missing adjusted CPI10 values."""
    required = {"survey_year", "survey_quarter", "adjusted_cpi10"}
    missing = required.difference(adjusted_cpi10.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    available = adjusted_cpi10.loc[adjusted_cpi10["adjusted_cpi10"].notna()].copy()
    if len(available) == 0:
        return {
            "first_survey_year": pd.NA,
            "first_survey_quarter": pd.NA,
            "last_survey_year": pd.NA,
            "last_survey_quarter": pd.NA,
            "n_surveys_with_data": 0,
            "n_rows_with_data": 0,
        }

    survey_keys = available[["survey_year", "survey_quarter"]].drop_duplicates()
    first_row = available.sort_values(["survey_year", "survey_quarter"]).iloc[0]
    last_row = available.sort_values(["survey_year", "survey_quarter"]).iloc[-1]
    return {
        "first_survey_year": int(first_row["survey_year"]),
        "first_survey_quarter": int(first_row["survey_quarter"]),
        "last_survey_year": int(last_row["survey_year"]),
        "last_survey_quarter": int(last_row["survey_quarter"]),
        "n_surveys_with_data": int(len(survey_keys)),
        "n_rows_with_data": int(len(available)),
    }


def adjusted_cpi10_forecaster_counts_by_survey(adjusted_cpi10: pd.DataFrame) -> pd.DataFrame:
    """Count forecasters with non-missing adjusted CPI10 by survey."""
    required = {"survey_year", "survey_quarter", "forecaster_id", "adjusted_cpi10"}
    missing = required.difference(adjusted_cpi10.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    available = adjusted_cpi10.loc[adjusted_cpi10["adjusted_cpi10"].notna()].copy()
    counts = (
        available.groupby(["survey_year", "survey_quarter"], as_index=False)["forecaster_id"]
        .nunique()
        .rename(columns={"forecaster_id": "n_forecasters_with_adjusted_cpi10"})
        .sort_values(["survey_year", "survey_quarter"])
    )
    return counts


def adjusted_cpi10_revision_ready_counts_by_survey(adjusted_cpi10: pd.DataFrame) -> pd.DataFrame:
    """Count forecasters with non-missing adjusted CPI10 in consecutive surveys."""
    required = {"survey_year", "survey_quarter", "forecaster_id", "adjusted_cpi10"}
    missing = required.difference(adjusted_cpi10.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    available = adjusted_cpi10.loc[adjusted_cpi10["adjusted_cpi10"].notna()].copy()
    if len(available) == 0:
        return pd.DataFrame(
            columns=[
                "survey_year",
                "survey_quarter",
                "n_forecasters_with_prev_quarter_adjusted_cpi10",
            ]
        )

    available = available[["survey_year", "survey_quarter", "forecaster_id"]].drop_duplicates().copy()
    available["prev_survey_year"] = available["survey_year"]
    available["prev_survey_quarter"] = available["survey_quarter"] - 1
    q1_mask = available["survey_quarter"] == 1
    available.loc[q1_mask, "prev_survey_year"] = available.loc[q1_mask, "survey_year"] - 1
    available.loc[q1_mask, "prev_survey_quarter"] = 4

    prev = available[["survey_year", "survey_quarter", "forecaster_id"]].rename(
        columns={
            "survey_year": "prev_survey_year",
            "survey_quarter": "prev_survey_quarter",
            "forecaster_id": "forecaster_id",
        }
    )
    merged = available.merge(
        prev,
        how="left",
        left_on=["prev_survey_year", "prev_survey_quarter", "forecaster_id"],
        right_on=["prev_survey_year", "prev_survey_quarter", "forecaster_id"],
        indicator=True,
    )
    revision_ready = merged.loc[merged["_merge"] == "both"]
    counts = (
        revision_ready.groupby(["survey_year", "survey_quarter"], as_index=False)["forecaster_id"]
        .nunique()
        .rename(columns={"forecaster_id": "n_forecasters_with_prev_quarter_adjusted_cpi10"})
        .sort_values(["survey_year", "survey_quarter"])
    )
    return counts
