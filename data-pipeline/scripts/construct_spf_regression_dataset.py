"""Construct SPF forecast-revision regression dataset from cleaned inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import construct_raw_cpi10_x, construct_regression_dataset


def main(config_path: str | None = None) -> None:
    """Load cleaned inputs, construct regression dataset, and write CSV."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        config_path = Path(config_path)

    with open(config_path) as file:
        config = json.load(file)

    repo_root = Path(__file__).parent.parent
    cleaned_dir = repo_root / config["cleaned_dir"]
    forecast_path = cleaned_dir / "forecast_individual.csv"
    inflation_news_path = cleaned_dir / "inflation_news.csv"
    reputation_path = cleaned_dir / "reputation_measure.csv"
    output_path = cleaned_dir / "regression_dataset.csv"

    forecast_individual = pd.read_csv(forecast_path)
    inflation_news = pd.read_csv(inflation_news_path)
    reputation_measure = pd.read_csv(reputation_path)

    regression_dataset = construct_regression_dataset(
        x_table=construct_raw_cpi10_x(forecast_individual=forecast_individual),
        inflation_news=inflation_news,
        reputation_measure=reputation_measure,
    )

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    regression_dataset.to_csv(output_path, index=False)

    print("Constructed SPF regression dataset")
    print(f"  X input:          {forecast_path}")
    print(f"  Inflation news:   {inflation_news_path}")
    print(f"  Reputation input: {reputation_path}")
    print(f"  Output:           {output_path}")
    print(f"  Rows:             {len(regression_dataset)}")
    print("Done.")


if __name__ == "__main__":
    config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path=config_path_arg)
