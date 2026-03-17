"""Construct forecast-revision regression inputs from cleaned SPF data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

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


def _remaining_average(
    cpi10: float | pd.NA,
    realized: float | pd.NA,
    *,
    remaining_quarters: int,
) -> float | pd.NA:
    """Convert a 40-quarter raw average into a remaining-quarter average."""
    if pd.isna(cpi10) or pd.isna(realized):
        return pd.NA
    return (40.0 * float(cpi10) - float(realized)) / float(remaining_quarters)


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
            adjusted = _remaining_average(
                cpi10,
                cpi1_q2,
                remaining_quarters=39,
            )
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
            adjusted = _remaining_average(
                cpi10,
                realized,
                remaining_quarters=38,
            )
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
            adjusted = _remaining_average(
                cpi10,
                realized,
                remaining_quarters=37,
            )

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


def construct_inflation_news(forecast_individual: pd.DataFrame) -> pd.DataFrame:
    """Return minimal table of inflation news by survey and forecaster."""
    required = {"survey_year", "survey_quarter", "forecaster_id", "CPI1", "CPI2"}
    missing = required.difference(forecast_individual.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    rows = (
        forecast_individual.loc[:, ["survey_year", "survey_quarter", "forecaster_id"]]
        .drop_duplicates()
        .sort_values(["survey_year", "survey_quarter", "forecaster_id"])
    )

    news_rows: list[dict[str, object]] = []
    for row in rows.itertuples(index=False):
        cpi1_current = _get_value_or_missing(
            forecast_individual=forecast_individual,
            survey_year=int(row.survey_year),
            survey_quarter=int(row.survey_quarter),
            forecaster_id=int(row.forecaster_id),
            horizon="CPI1",
        )
        if row.survey_quarter == 1:
            lagged_survey_year = int(row.survey_year) - 1
            lagged_survey_quarter = 4
        else:
            lagged_survey_year = int(row.survey_year)
            lagged_survey_quarter = int(row.survey_quarter) - 1

        cpi2_lagged = _get_value_or_missing(
            forecast_individual=forecast_individual,
            survey_year=lagged_survey_year,
            survey_quarter=lagged_survey_quarter,
            forecaster_id=int(row.forecaster_id),
            horizon="CPI2",
        )
        if pd.isna(cpi1_current) or pd.isna(cpi2_lagged):
            inflation_news = pd.NA
        else:
            inflation_news = float(cpi1_current) - float(cpi2_lagged)

        news_rows.append(
            {
                "survey_year": int(row.survey_year),
                "survey_quarter": int(row.survey_quarter),
                "forecaster_id": int(row.forecaster_id),
                "inflation_news": inflation_news,
            }
        )

    out = pd.DataFrame(news_rows)
    if len(out) == 0:
        return pd.DataFrame(
            columns=["survey_year", "survey_quarter", "forecaster_id", "inflation_news"]
        )
    out["survey_year"] = out["survey_year"].astype("Int64")
    out["survey_quarter"] = out["survey_quarter"].astype("Int64")
    out["forecaster_id"] = out["forecaster_id"].astype("Int64")
    out["inflation_news"] = pd.to_numeric(out["inflation_news"], errors="coerce")
    return out


def construct_reputation_measure(
    x_table: pd.DataFrame,
    *,
    config: Mapping[str, object],
) -> pd.DataFrame:
    """Return table with the same keys as x_table and one rho column."""
    required = {"survey_year", "survey_quarter", "x"}
    missing = required.difference(x_table.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    required_config = {"q", "pi_target", "pi_NE", "z_a", "z_alpha"}
    missing_config = required_config.difference(config)
    if missing_config:
        raise KeyError(f"Missing required config values: {sorted(missing_config)}")

    q = float(config["q"])
    pi_target = float(config["pi_target"])
    pi_ne = float(config["pi_NE"])
    z_a = float(config["z_a"])
    z_alpha = float(config["z_alpha"])
    target_term = (1.0 - q) * pi_target + q * z_a
    ne_term = (1.0 - q) * pi_ne + q * z_alpha
    denominator = target_term - ne_term
    if denominator == 0.0:
        raise ValueError("Reputation denominator is zero.")

    key_columns = [column for column in x_table.columns if column != "x"]
    output_rows: list[dict[str, object]] = []
    for row in x_table.itertuples(index=False):
        row_dict = row._asdict()
        x_value = _as_numeric(row_dict["x"])
        if pd.isna(x_value):
            rho = pd.NA
        else:
            rho = (float(x_value) - ne_term) / denominator

        output_row = {
            key: row_dict[key]
            for key in key_columns
        }
        output_row["rho"] = rho
        output_rows.append(output_row)

    out = pd.DataFrame(output_rows)
    if len(out) == 0:
        return pd.DataFrame(columns=[*key_columns, "rho"])

    for integer_column in ["survey_year", "survey_quarter", "forecaster_id"]:
        if integer_column in out.columns:
            out[integer_column] = pd.to_numeric(out[integer_column], errors="coerce").astype("Int64")
    out["rho"] = pd.to_numeric(out["rho"], errors="coerce")
    return out
