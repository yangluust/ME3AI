"""Estimate forecast-revision regressions and construct comparison figures."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def _validate_regression_dataset(regression_dataset: pd.DataFrame) -> None:
    """Require the columns needed for the survey-level regressions."""
    required = {"survey_year", "survey_quarter", "r_bar", "n_bar", "z2", "z3"}
    missing = required.difference(regression_dataset.columns)
    if missing:
        raise KeyError(f"Missing required regression_dataset columns: {sorted(missing)}")


def _fit_no_constant_ols(
    regression_dataset: pd.DataFrame,
    *,
    regressor_column: str,
    model_label: str,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Estimate one no-constant OLS regression and return stats plus fitted values."""
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
    x_sum_squares = float(np.dot(x, x))
    if x_sum_squares == 0.0:
        raise ValueError(f"{model_label} regressor has zero sum of squares.")

    estimate = float(np.dot(x, y) / x_sum_squares)
    fitted = estimate * x
    residuals = y - fitted
    sample_size = len(working)
    degrees_of_freedom = sample_size - 1
    ssr = float(np.dot(residuals, residuals))
    rmse = math.sqrt(ssr / sample_size)
    uncentered_tss = float(np.dot(y, y))
    if uncentered_tss == 0.0:
        adjusted_r_squared = math.nan
    else:
        rsquared = 1.0 - ssr / uncentered_tss
        adjusted_r_squared = 1.0 - (sample_size / degrees_of_freedom) * (1.0 - rsquared)

    if ssr == 0.0:
        p_value = 0.0
    else:
        variance = ssr / degrees_of_freedom
        standard_error = math.sqrt(variance / x_sum_squares)
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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate the three no-constant forecast-revision regressions."""
    _validate_regression_dataset(regression_dataset=regression_dataset)

    model_specs = [
        ("model_1", "n_bar"),
        ("model_2", "z2"),
        ("model_3", "z3"),
    ]
    statistics_rows: list[dict[str, object]] = []
    fitted_values: pd.DataFrame | None = None
    for model_label, regressor_column in model_specs:
        statistics_row, model_fitted = _fit_no_constant_ols(
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
) -> tuple[plt.Figure, pd.DataFrame]:
    """Plot cumulative data and fitted counterparts since 1991:Q4."""
    _validate_regression_dataset(regression_dataset=regression_dataset)

    required_fitted = {
        "survey_year",
        "survey_quarter",
        "fitted_model_1",
        "fitted_model_2",
        "fitted_model_3",
    }
    missing_fitted = required_fitted.difference(fitted_values.columns)
    if missing_fitted:
        raise KeyError(f"Missing required fitted_values columns: {sorted(missing_fitted)}")

    plot_panel = regression_dataset.loc[:, ["survey_year", "survey_quarter", "r_bar"]].merge(
        fitted_values,
        how="inner",
        on=["survey_year", "survey_quarter"],
    )
    plot_panel = plot_panel.loc[
        (plot_panel["survey_year"] > 1991)
        | ((plot_panel["survey_year"] == 1991) & (plot_panel["survey_quarter"] >= 4))
    ].copy()
    plot_panel = plot_panel.sort_values(["survey_year", "survey_quarter"]).reset_index(drop=True)
    for value_column in ["r_bar", "fitted_model_1", "fitted_model_2", "fitted_model_3"]:
        plot_panel[value_column] = pd.to_numeric(plot_panel[value_column], errors="coerce")

    plot_panel["cumulative_data"] = plot_panel["r_bar"].cumsum()
    plot_panel["cumulative_model_1"] = plot_panel["fitted_model_1"].cumsum()
    plot_panel["cumulative_model_2"] = plot_panel["fitted_model_2"].cumsum()
    plot_panel["cumulative_model_3"] = plot_panel["fitted_model_3"].cumsum()

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
    axis.set_xlabel("Survey year-quarter")
    axis.set_ylabel("Cumulative change in long-term inflation forecast")
    axis.set_title("Cumulative change in long-term inflation forecast since 1991:Q4")
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
