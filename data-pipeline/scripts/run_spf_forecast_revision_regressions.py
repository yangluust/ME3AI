"""Run SPF forecast-revision regressions and write results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import (
    ADJUSTED_CPI10_X_SOURCE,
    RAW_CPI10_X_SOURCE,
    get_configured_x_definitions,
)
from src.spf_regression import (
    build_specification_comparison_panel,
    format_x_definition_label,
    plot_cumulative_forecast_revision_comparison,
    plot_specification_comparison,
    run_forecast_revision_regressions,
)


def _sample_window_label(regression_config: Dict[str, object]) -> str:
    """Return readable sample-window label."""
    return (
        f"{regression_config['sample_start_year']}:Q{regression_config['sample_start_quarter']}"
        " to "
        f"{regression_config['sample_end_year']}:Q{regression_config['sample_end_quarter']}"
    )


def _regression_results_to_latex(
    regression_results: pd.DataFrame,
    *,
    x_definition: str,
    sample_window: str,
) -> str:
    """Render one regression-results table as LaTeX."""
    regressor_labels = {
        "n_bar": r"$\bar{n}_s$",
        "z2": r"$z_{2,s}$",
        "z3": r"$z_{3,s}$",
        "zP": r"$z_{P,s}$",
    }
    model_labels = {
        "model_1": "Model 1",
        "model_2": "Model 2",
        "model_3": "Model 3",
        "model_P": "Model P",
    }
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        (
            r"\caption{Forecast revision regression results using "
            + format_x_definition_label(x_definition)
            + " ("
            + sample_window
            + ").}"
        ),
        r"\begin{tabular}{@{}lllllll@{}}",
        r"\toprule",
        r"Model & Regressor & Estimate & p value & Adjusted $R^2$ & RMSE & Sample size \\",
        r"\midrule",
    ]
    for row in regression_results.itertuples(index=False):
        lines.append(
            " & ".join(
                [
                    model_labels[str(row.model)],
                    regressor_labels[str(row.regressor)],
                    f"{float(row.estimate):.6f}",
                    f"{float(row.p_value):.3e}",
                    f"{float(row.adjusted_r_squared):.6f}",
                    f"{float(row.rmse):.6f}",
                    f"{int(row.sample_size)}",
                ]
            )
            + r" \\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def main(
    clean_config_path: str | None = None,
    regression_config_path: str | None = None,
) -> None:
    """Load regression dataset, run regressions, and write outputs."""
    if clean_config_path is None:
        clean_config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        clean_config_path = Path(clean_config_path)
    if regression_config_path is None:
        regression_config_path = Path(__file__).parent.parent / "config" / "forecast_revision.json"
    else:
        regression_config_path = Path(regression_config_path)

    with open(clean_config_path) as file:
        config = json.load(file)
    with open(regression_config_path) as file:
        regression_config = json.load(file)

    repo_root = Path(__file__).parent.parent
    cleaned_dir = repo_root / config["cleaned_dir"]
    output_dir = repo_root / "output" / "forecast_revision"
    output_dir.mkdir(parents=True, exist_ok=True)

    x_definitions = get_configured_x_definitions(config=regression_config)
    required = {RAW_CPI10_X_SOURCE, ADJUSTED_CPI10_X_SOURCE}
    if set(x_definitions) != required:
        raise ValueError(
            "Comparison workflow requires x_definitions to be exactly "
            f"{sorted(required)}."
        )

    sample_window = _sample_window_label(regression_config=regression_config)
    regression_datasets: Dict[str, pd.DataFrame] = {}

    print("Ran SPF forecast-revision regressions")
    for x_definition in x_definitions:
        regression_dataset_path = (
            cleaned_dir / "forecast_revision" / x_definition / "regression_dataset.csv"
        )
        spec_output_dir = output_dir / x_definition
        table_output_path = spec_output_dir / "regression_results.csv"
        table_tex_output_path = spec_output_dir / "regression_results.tex"
        figure_output_path = spec_output_dir / "cumulative_forecast_revision_comparison.png"

        regression_dataset = pd.read_csv(regression_dataset_path)
        regression_results, fitted_values = run_forecast_revision_regressions(
            regression_dataset=regression_dataset,
            config=regression_config,
        )
        figure, _ = plot_cumulative_forecast_revision_comparison(
            regression_dataset=regression_dataset,
            fitted_values=fitted_values,
            config=regression_config,
        )
        figure.axes[0].set_title(
            "Cumulative change in long-term inflation forecast, "
            f"{format_x_definition_label(x_definition)} ({sample_window})"
        )

        spec_output_dir.mkdir(parents=True, exist_ok=True)
        regression_results.to_csv(table_output_path, index=False)
        table_tex_output_path.write_text(
            _regression_results_to_latex(
                regression_results=regression_results,
                x_definition=x_definition,
                sample_window=sample_window,
            ),
            encoding="utf-8",
        )
        figure.savefig(figure_output_path, dpi=300, bbox_inches="tight")
        figure.clf()
        regression_datasets[x_definition] = regression_dataset

        print(f"  Input:  {regression_dataset_path}")
        print(f"  Table:  {table_output_path}")
        print(f"  TableT: {table_tex_output_path}")
        print(f"  Figure: {figure_output_path}")
        print(f"  X def:  {x_definition}")

    comparison_dir = output_dir / "comparison"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    comparison_specs = [
        (
            "r_bar",
            "long_term_forecast_revision_comparison.png",
            "Survey-level matched-sample mean long-term forecast revision",
            "Long-term forecast revision",
        ),
        (
            "rho_bar_prev",
            "reputation_measure_comparison.png",
            "Survey-level matched-sample mean previous-survey reputation",
            "Reputation measure",
        ),
        (
            "n_bar",
            "regressor_1_comparison.png",
            "Survey-level matched-sample mean regressor 1",
            "Regressor 1",
        ),
        (
            "z2",
            "regressor_2_comparison.png",
            "Survey-level matched-sample mean regressor 2",
            "Regressor 2",
        ),
        (
            "z3",
            "regressor_3_comparison.png",
            "Survey-level matched-sample mean regressor 3",
            "Regressor 3",
        ),
        (
            "zP",
            "regressor_P_comparison.png",
            "Survey-level matched-sample mean placebo regressor",
            "Regressor P",
        ),
    ]
    for value_column, filename, title, y_label in comparison_specs:
        comparison_panel = build_specification_comparison_panel(
            regression_datasets=regression_datasets,
            value_column=value_column,
            config=regression_config,
        )
        figure = plot_specification_comparison(
            comparison_panel=comparison_panel,
            raw_column=RAW_CPI10_X_SOURCE,
            adjusted_column=ADJUSTED_CPI10_X_SOURCE,
            title=f"{title} ({sample_window})",
            y_label=y_label,
        )
        figure_output_path = comparison_dir / filename
        figure.savefig(figure_output_path, dpi=300, bbox_inches="tight")
        figure.clf()
        print(f"  Compare: {figure_output_path}")

    print(f"  Sample: {sample_window}")
    print("Done.")


if __name__ == "__main__":
    clean_config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    regression_config_path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(
        clean_config_path=clean_config_path_arg,
        regression_config_path=regression_config_path_arg,
    )
