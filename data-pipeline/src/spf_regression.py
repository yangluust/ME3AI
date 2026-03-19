"""Estimate forecast-revision regressions and construct comparison figures."""

from __future__ import annotations

import math
from collections.abc import Mapping

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def _validate_regression_dataset(regression_dataset: pd.DataFrame) -> None:
    """Require the columns needed for the survey-level regressions."""
    required = {"survey_year", "survey_quarter", "r_bar", "n_bar", "z2", "z3", "zP"}
    missing = required.difference(regression_dataset.columns)
    if missing:
        raise KeyError(f"Missing required regression_dataset columns: {sorted(missing)}")


def _validate_regression_config(config: Mapping[str, object]) -> None:
    """Require regression config values needed for sample selection."""
    required = {
        "sample_start_year",
        "sample_start_quarter",
        "sample_end_year",
        "sample_end_quarter",
    }
    missing = required.difference(config)
    if missing:
        raise KeyError(f"Missing required regression config values: {sorted(missing)}")

    start_year = int(config["sample_start_year"])
    start_quarter = int(config["sample_start_quarter"])
    end_year = int(config["sample_end_year"])
    end_quarter = int(config["sample_end_quarter"])
    if start_quarter not in {1, 2, 3, 4}:
        raise ValueError("sample_start_quarter must be in {1, 2, 3, 4}.")
    if end_quarter not in {1, 2, 3, 4}:
        raise ValueError("sample_end_quarter must be in {1, 2, 3, 4}.")
    if (start_year, start_quarter) > (end_year, end_quarter):
        raise ValueError("Regression sample start must not be after the end.")


def _restrict_to_sample_window(
    regression_dataset: pd.DataFrame,
    *,
    config: Mapping[str, object],
) -> pd.DataFrame:
    """Return the bounded survey sample used for estimation and plotting."""
    _validate_regression_config(config=config)
    sample_start_year = int(config["sample_start_year"])
    sample_start_quarter = int(config["sample_start_quarter"])
    sample_end_year = int(config["sample_end_year"])
    sample_end_quarter = int(config["sample_end_quarter"])

    return regression_dataset.loc[
        (
            (regression_dataset["survey_year"] > sample_start_year)
            | (
                (regression_dataset["survey_year"] == sample_start_year)
                & (regression_dataset["survey_quarter"] >= sample_start_quarter)
            )
        )
        & (
            (regression_dataset["survey_year"] < sample_end_year)
            | (
                (regression_dataset["survey_year"] == sample_end_year)
                & (regression_dataset["survey_quarter"] <= sample_end_quarter)
            )
        )
    ].copy()


def _sample_window_label(config: Mapping[str, object]) -> str:
    """Return sample window label for reporting and figure titles."""
    _validate_regression_config(config=config)
    return (
        f"{int(config['sample_start_year'])}:Q{int(config['sample_start_quarter'])}"
        f" to {int(config['sample_end_year'])}:Q{int(config['sample_end_quarter'])}"
    )


def format_x_definition_label(x_definition: str) -> str:
    """Return readable label for one x-definition specification."""
    labels = {
        "raw_cpi10": "Raw CPI10",
        "adjusted_cpi10": "Adjusted CPI10",
    }
    if x_definition not in labels:
        raise ValueError(f"Unsupported x_definition label: {x_definition}")
    return labels[x_definition]


def _fit_ols_with_constant(
    regression_dataset: pd.DataFrame,
    *,
    regressor_column: str,
    model_label: str,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Estimate one OLS regression with intercept and return stats plus fitted values."""
    working = regression_dataset.loc[
        :, ["survey_year", "survey_quarter", "r_bar", regressor_column]
    ].copy()
    working["r_bar"] = pd.to_numeric(working["r_bar"], errors="coerce")
    working[regressor_column] = pd.to_numeric(working[regressor_column], errors="coerce")
    working = working.loc[working["r_bar"].notna() & working[regressor_column].notna()].copy()
    if len(working) < 2:
        raise ValueError(f"{model_label} requires at least two observations.")

    x = working[regressor_column].to_numpy(dtype=float)
    y = working["r_bar"].to_numpy(dtype=float)
    design_matrix = np.column_stack([np.ones(len(working), dtype=float), x])
    if np.linalg.matrix_rank(design_matrix) < 2:
        raise ValueError(f"{model_label} design matrix is rank deficient.")

    coefficients, _, _, _ = np.linalg.lstsq(design_matrix, y, rcond=None)
    intercept = float(coefficients[0])
    estimate = float(coefficients[1])
    fitted = design_matrix @ coefficients
    residuals = y - fitted
    sample_size = len(working)
    degrees_of_freedom = sample_size - 2
    if degrees_of_freedom <= 0:
        raise ValueError(f"{model_label} requires at least three observations.")
    ssr = float(np.dot(residuals, residuals))
    rmse = math.sqrt(ssr / sample_size)
    centered_tss = float(np.dot(y - y.mean(), y - y.mean()))
    if centered_tss == 0.0:
        adjusted_r_squared = math.nan
    else:
        rsquared = 1.0 - ssr / centered_tss
        adjusted_r_squared = 1.0 - ((sample_size - 1.0) / degrees_of_freedom) * (1.0 - rsquared)

    if ssr == 0.0:
        p_value = 0.0
    else:
        variance = ssr / degrees_of_freedom
        xtx_inverse = np.linalg.inv(design_matrix.T @ design_matrix)
        standard_error = math.sqrt(float(variance * xtx_inverse[1, 1]))
        if standard_error == 0.0:
            p_value = 0.0
        else:
            t_statistic = estimate / standard_error
            p_value = float(2.0 * stats.t.sf(abs(t_statistic), df=degrees_of_freedom))

    fitted_values = working.loc[:, ["survey_year", "survey_quarter"]].copy()
    fitted_values[f"fitted_{model_label}"] = fitted

    statistics_row = {
        "model": model_label,
        "regressor": regressor_column,
        "estimate": estimate,
        "p_value": p_value,
        "adjusted_r_squared": adjusted_r_squared,
        "rmse": rmse,
        "sample_size": sample_size,
    }
    return statistics_row, fitted_values


def run_forecast_revision_regressions(
    regression_dataset: pd.DataFrame,
    *,
    config: Mapping[str, object],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate the forecast-revision regressions with intercepts."""
    _validate_regression_dataset(regression_dataset=regression_dataset)
    regression_dataset = _restrict_to_sample_window(
        regression_dataset=regression_dataset,
        config=config,
    )

    model_specs = [
        ("model_1", "n_bar"),
        ("model_2", "z2"),
        ("model_3", "z3"),
        ("model_P", "zP"),
    ]
    statistics_rows: list[dict[str, object]] = []
    fitted_values: pd.DataFrame | None = None
    for model_label, regressor_column in model_specs:
        statistics_row, model_fitted = _fit_ols_with_constant(
            regression_dataset=regression_dataset,
            regressor_column=regressor_column,
            model_label=model_label,
        )
        statistics_rows.append(statistics_row)
        if fitted_values is None:
            fitted_values = model_fitted
        else:
            fitted_values = fitted_values.merge(
                model_fitted,
                how="outer",
                on=["survey_year", "survey_quarter"],
            )

    regression_statistics = pd.DataFrame(statistics_rows)
    regression_statistics["sample_size"] = pd.to_numeric(
        regression_statistics["sample_size"], errors="coerce"
    ).astype("Int64")
    fitted_values = fitted_values.sort_values(["survey_year", "survey_quarter"]).reset_index(drop=True)
    for integer_column in ["survey_year", "survey_quarter"]:
        fitted_values[integer_column] = pd.to_numeric(
            fitted_values[integer_column], errors="coerce"
        ).astype("Int64")
    return regression_statistics, fitted_values


def plot_cumulative_forecast_revision_comparison(
    regression_dataset: pd.DataFrame,
    *,
    fitted_values: pd.DataFrame,
    config: Mapping[str, object],
) -> tuple[plt.Figure, pd.DataFrame]:
    """Plot cumulative data and fitted counterparts for the configured sample."""
    _validate_regression_dataset(regression_dataset=regression_dataset)

    required_fitted = {
        "survey_year",
        "survey_quarter",
        "fitted_model_1",
        "fitted_model_2",
        "fitted_model_3",
        "fitted_model_P",
    }
    missing_fitted = required_fitted.difference(fitted_values.columns)
    if missing_fitted:
        raise KeyError(f"Missing required fitted_values columns: {sorted(missing_fitted)}")

    plot_panel = regression_dataset.loc[:, ["survey_year", "survey_quarter", "r_bar"]].merge(
        fitted_values,
        how="inner",
        on=["survey_year", "survey_quarter"],
    )
    plot_panel = _restrict_to_sample_window(
        regression_dataset=plot_panel,
        config=config,
    )
    plot_panel = plot_panel.sort_values(["survey_year", "survey_quarter"]).reset_index(drop=True)
    for value_column in [
        "r_bar",
        "fitted_model_1",
        "fitted_model_2",
        "fitted_model_3",
        "fitted_model_P",
    ]:
        plot_panel[value_column] = pd.to_numeric(plot_panel[value_column], errors="coerce")

    plot_panel["cumulative_data"] = plot_panel["r_bar"].cumsum()
    plot_panel["cumulative_model_1"] = plot_panel["fitted_model_1"].cumsum()
    plot_panel["cumulative_model_2"] = plot_panel["fitted_model_2"].cumsum()
    plot_panel["cumulative_model_3"] = plot_panel["fitted_model_3"].cumsum()
    plot_panel["cumulative_model_P"] = plot_panel["fitted_model_P"].cumsum()

    figure, axis = plt.subplots(figsize=(10, 4))
    x_positions = range(len(plot_panel))
    axis.plot(
        x_positions,
        plot_panel["cumulative_data"].to_numpy(),
        color="black",
        linestyle="--",
        label="Data",
    )
    axis.plot(
        x_positions,
        plot_panel["cumulative_model_1"].to_numpy(),
        color="magenta",
        linestyle="-",
        label="Model 1",
    )
    axis.plot(
        x_positions,
        plot_panel["cumulative_model_2"].to_numpy(),
        color="blue",
        linestyle="-",
        label="Model 2",
    )
    axis.plot(
        x_positions,
        plot_panel["cumulative_model_3"].to_numpy(),
        color="red",
        linestyle="-",
        label="Model 3",
    )
    axis.plot(
        x_positions,
        plot_panel["cumulative_model_P"].to_numpy(),
        color="green",
        linestyle="-",
        label="Model P",
    )
    axis.set_xlabel("Survey year-quarter")
    axis.set_ylabel("Cumulative change in long-term inflation forecast")
    axis.set_title(
        "Cumulative change in long-term inflation forecast, "
        f"{_sample_window_label(config=config)}"
    )
    if len(plot_panel) > 0:
        tick_step = max(len(plot_panel) // 8, 1)
        tick_idx = list(range(0, len(plot_panel), tick_step))
        axis.set_xticks(tick_idx)
        axis.set_xticklabels(
            [
                f"{int(row.survey_year)}:Q{int(row.survey_quarter)}"
                for row in plot_panel.iloc[tick_idx].itertuples(index=False)
            ],
            rotation=45,
            ha="right",
        )
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    return figure, plot_panel


def build_specification_comparison_panel(
    regression_datasets: Mapping[str, pd.DataFrame],
    *,
    value_column: str,
    config: Mapping[str, object],
) -> pd.DataFrame:
    """Return panel comparing one survey-level series across x definitions."""
    panels: list[pd.DataFrame] = []
    for x_definition, regression_dataset in regression_datasets.items():
        _validate_regression_dataset(regression_dataset=regression_dataset)
        if value_column not in regression_dataset.columns:
            raise KeyError(f"Missing required comparison column: {value_column}")

        panel = _restrict_to_sample_window(
            regression_dataset=regression_dataset.loc[
                :, ["survey_year", "survey_quarter", value_column]
            ].copy(),
            config=config,
        )
        panel = panel.rename(columns={value_column: x_definition})
        panels.append(panel)

    if len(panels) == 0:
        raise ValueError("regression_datasets must contain at least one specification.")

    comparison_panel = panels[0]
    for panel in panels[1:]:
        comparison_panel = comparison_panel.merge(
            panel,
            how="outer",
            on=["survey_year", "survey_quarter"],
        )

    comparison_panel = comparison_panel.sort_values(
        ["survey_year", "survey_quarter"]
    ).reset_index(drop=True)
    for column in comparison_panel.columns:
        if column not in {"survey_year", "survey_quarter"}:
            comparison_panel[column] = pd.to_numeric(comparison_panel[column], errors="coerce")
    return comparison_panel


def plot_specification_comparison(
    comparison_panel: pd.DataFrame,
    *,
    raw_column: str,
    adjusted_column: str,
    title: str,
    y_label: str,
) -> plt.Figure:
    """Plot one survey-level comparison figure for raw versus adjusted x."""
    required = {"survey_year", "survey_quarter", raw_column, adjusted_column}
    missing = required.difference(comparison_panel.columns)
    if missing:
        raise KeyError(f"Missing required comparison_panel columns: {sorted(missing)}")

    figure, axis = plt.subplots(figsize=(10, 4))
    x_positions = range(len(comparison_panel))
    axis.plot(
        x_positions,
        comparison_panel[raw_column].to_numpy(),
        color="black",
        linestyle="-",
        label=format_x_definition_label(raw_column),
    )
    axis.plot(
        x_positions,
        comparison_panel[adjusted_column].to_numpy(),
        color="blue",
        linestyle="-",
        label=format_x_definition_label(adjusted_column),
    )
    axis.set_xlabel("Survey year-quarter")
    axis.set_ylabel(y_label)
    axis.set_title(title)
    if len(comparison_panel) > 0:
        tick_step = max(len(comparison_panel) // 8, 1)
        tick_idx = list(range(0, len(comparison_panel), tick_step))
        axis.set_xticks(tick_idx)
        axis.set_xticklabels(
            [
                f"{int(row.survey_year)}:Q{int(row.survey_quarter)}"
                for row in comparison_panel.iloc[tick_idx].itertuples(index=False)
            ],
            rotation=45,
            ha="right",
        )
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    return figure
