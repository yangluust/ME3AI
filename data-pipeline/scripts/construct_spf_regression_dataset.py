"""Construct SPF forecast-revision regression dataset from cleaned inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import (
    construct_regression_dataset,
    get_configured_x_definitions,
    select_long_term_inflation_expectation,
)


def main(
    clean_config_path: str | None = None,
    regression_config_path: str | None = None,
) -> None:
    """Load cleaned inputs, construct regression dataset, and write CSV."""
    if clean_config_path is None:
        clean_config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        clean_config_path = Path(clean_config_path)
    if regression_config_path is None:
        regression_config_path = Path(__file__).parent.parent / "config" / "forecast_revision.json"
    else:
        regression_config_path = Path(regression_config_path)

    with open(clean_config_path) as file:
        clean_config = json.load(file)
    with open(regression_config_path) as file:
        regression_config = json.load(file)

    repo_root = Path(__file__).parent.parent
    cleaned_dir = repo_root / clean_config["cleaned_dir"]
    forecast_path = cleaned_dir / "forecast_individual.csv"
    inflation_news_path = cleaned_dir / "inflation_news.csv"

    forecast_individual = pd.read_csv(forecast_path)
    inflation_news = pd.read_csv(inflation_news_path)
    x_definitions = get_configured_x_definitions(config=regression_config)

    print("Constructed SPF regression dataset")
    print(f"  X input:          {forecast_path}")
    print(f"  Inflation news:   {inflation_news_path}")
    for x_definition in x_definitions:
        reputation_path = (
            cleaned_dir / "forecast_revision" / x_definition / "reputation_measure.csv"
        )
        output_path = (
            cleaned_dir / "forecast_revision" / x_definition / "regression_dataset.csv"
        )
        reputation_measure = pd.read_csv(reputation_path)
        regression_dataset = construct_regression_dataset(
            x_table=select_long_term_inflation_expectation(
                forecast_individual=forecast_individual,
                config={"x_definition": x_definition},
            ),
            inflation_news=inflation_news,
            reputation_measure=reputation_measure,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        regression_dataset.to_csv(output_path, index=False)
        print(f"  X def:            {x_definition}")
        print(f"  Reputation input: {reputation_path}")
        print(f"  Output:           {output_path}")
        print(f"  Rows:             {len(regression_dataset)}")
    print("Done.")


if __name__ == "__main__":
    clean_config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    regression_config_path_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(
        clean_config_path=clean_config_path_arg,
        regression_config_path=regression_config_path_arg,
    )
