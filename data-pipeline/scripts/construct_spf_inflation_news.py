"""Construct SPF inflation-news table from cleaned forecast data."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import construct_inflation_news


def main(config_path: str | None = None) -> None:
    """Load cleaned data, construct inflation news, and write CSV."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        config_path = Path(config_path)

    with open(config_path) as file:
        config = json.load(file)

    repo_root = Path(__file__).parent.parent
    cleaned_dir = repo_root / config["cleaned_dir"]
    input_path = cleaned_dir / "forecast_individual.csv"
    output_path = cleaned_dir / "inflation_news.csv"

    forecast_individual = pd.read_csv(input_path)
    inflation_news = construct_inflation_news(
        forecast_individual=forecast_individual,
    )

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    inflation_news.to_csv(output_path, index=False)

    print("Constructed SPF inflation news")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Rows:   {len(inflation_news)}")
    print("Done.")


if __name__ == "__main__":
    config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path=config_path_arg)
