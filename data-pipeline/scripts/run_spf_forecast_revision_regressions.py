"""Run SPF forecast-revision regressions and write results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_regression import (
    plot_cumulative_forecast_revision_comparison,
    run_forecast_revision_regressions,
)


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
    regression_dataset_path = cleaned_dir / "regression_dataset.csv"
    output_dir = repo_root / "output" / "forecast_revision"
    table_output_path = output_dir / "regression_results.csv"
    figure_output_path = output_dir / "cumulative_forecast_revision_comparison.png"

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

    output_dir.mkdir(parents=True, exist_ok=True)
    regression_results.to_csv(table_output_path, index=False)
    figure.savefig(figure_output_path, dpi=300, bbox_inches="tight")
    figure.clf()

    print("Ran SPF forecast-revision regressions")
    print(f"  Input:  {regression_dataset_path}")
    print(f"  Table:  {table_output_path}")
    print(f"  Figure: {figure_output_path}")
    print(f"  X def:  {regression_config['x_definition']}")
    print(
        "  Sample: "
        f"{regression_config['sample_start_year']}:Q{regression_config['sample_start_quarter']}"
        " to "
        f"{regression_config['sample_end_year']}:Q{regression_config['sample_end_quarter']}"
    )
    print(f"  Rows:   {len(regression_results)}")
    print("Done.")


if __name__ == "__main__":
    clean_config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    regression_config_path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(
        clean_config_path=clean_config_path_arg,
        regression_config_path=regression_config_path_arg,
    )
