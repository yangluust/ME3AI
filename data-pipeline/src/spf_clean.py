"""Clean SPF individual forecast files into 3NF CSV tables.

Reads Individual_*.xlsx from input dir, reshapes to long form (one row per
survey_year, survey_quarter, variable, forecaster_id, horizon, value), and
writes forecast_individual.csv plus survey.csv and forecaster_survey.csv
for referential integrity. All horizons are kept.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# First columns in Individual_*.xlsx per SPF documentation (year, quarter, ID, industry).
ID_COLUMNS = ["YEAR", "QUARTER", "ID", "INDUSTRY"]


def _variable_from_filename(path: Path) -> str:
    """Extract variable code from Individual_VAR.xlsx filename."""
    stem = path.stem
    if stem.startswith("Individual_"):
        return stem.replace("Individual_", "", 1)
    return stem


def load_individual_sheet(path: Path) -> pd.DataFrame:
    """Load one Individual_*.xlsx file; return long-form dataframe with variable."""
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        raise ValueError(f"Empty sheet in {path.name}")
    header = [str(v).strip() if v is not None else "" for v in rows[0]]
    id_cols = [c for c in ID_COLUMNS if c in header]
    if len(id_cols) < 3:
        raise ValueError(f"Expected at least YEAR, QUARTER, ID in {path.name}; got {header[:5]}")
    horizon_cols = [c for c in header if c not in id_cols]
    if not horizon_cols:
        raise ValueError(f"No horizon columns in {path.name}")

    raw = pd.DataFrame(rows[1:], columns=header)
    long = raw.melt(
        id_vars=id_cols,
        value_vars=horizon_cols,
        var_name="horizon",
        value_name="value",
    )
    long = long.rename(
        columns={
            "YEAR": "survey_year",
            "QUARTER": "survey_quarter",
            "ID": "forecaster_id",
        }
    )
    long["variable"] = _variable_from_filename(path)
    return long


def build_forecast_individual(df_long: pd.DataFrame) -> pd.DataFrame:
    """Build 3NF forecast_individual table: (survey_year, survey_quarter, variable, forecaster_id, horizon, value)."""
    cols = ["survey_year", "survey_quarter", "variable", "forecaster_id", "horizon", "value"]
    out = df_long[cols].copy()
    out["survey_year"] = out["survey_year"].astype("Int64")
    out["survey_quarter"] = out["survey_quarter"].astype("Int64")
    out["forecaster_id"] = out["forecaster_id"].astype("Int64")
    return out


def build_survey(df_long: pd.DataFrame) -> pd.DataFrame:
    """Build survey table: (survey_year, survey_quarter)."""
    out = df_long[["survey_year", "survey_quarter"]].drop_duplicates()
    out = out.sort_values(["survey_year", "survey_quarter"])
    out["survey_year"] = out["survey_year"].astype("Int64")
    out["survey_quarter"] = out["survey_quarter"].astype("Int64")
    return out


def build_forecaster_survey(df_long: pd.DataFrame) -> pd.DataFrame:
    """Build forecaster_survey table: (survey_year, survey_quarter, forecaster_id, industry)."""
    if "INDUSTRY" not in df_long.columns:
        return pd.DataFrame(columns=["survey_year", "survey_quarter", "forecaster_id", "industry"])
    out = (
        df_long[["survey_year", "survey_quarter", "forecaster_id", "INDUSTRY"]]
        .drop_duplicates()
        .rename(columns={"INDUSTRY": "industry"})
    )
    out = out.sort_values(["survey_year", "survey_quarter", "forecaster_id"])
    out["survey_year"] = out["survey_year"].astype("Int64")
    out["survey_quarter"] = out["survey_quarter"].astype("Int64")
    out["forecaster_id"] = out["forecaster_id"].astype("Int64")
    return out


def clean_individual_to_3nf(
    input_dir: Path,
    cleaned_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read all Individual_*.xlsx from input_dir; build 3NF tables; return (forecast_individual, survey, forecaster_survey)."""
    paths = sorted(input_dir.glob("Individual_*.xlsx"))
    if not paths:
        raise FileNotFoundError(f"No Individual_*.xlsx files in {input_dir}")

    frames: list[pd.DataFrame] = []
    for path in paths:
        frames.append(load_individual_sheet(path=path))

    df_long = pd.concat(frames, ignore_index=True)

    forecast_individual = build_forecast_individual(df_long=df_long)
    survey = build_survey(df_long=df_long)
    forecaster_survey = build_forecaster_survey(df_long=df_long)

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    forecast_individual.to_csv(cleaned_dir / "forecast_individual.csv", index=False)
    survey.to_csv(cleaned_dir / "survey.csv", index=False)
    forecaster_survey.to_csv(cleaned_dir / "forecaster_survey.csv", index=False)

    return forecast_individual, survey, forecaster_survey
