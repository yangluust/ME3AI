"""Construct adjusted CPI10 expectations from cleaned SPF data.

Reads config/spf_clean.json to locate the cleaned folder, loads
forecast_individual.csv, computes adjusted 10-year CPI expectations, and writes
adjusted_cpi10.csv to the cleaned folder. For Q2-Q4 surveys, the script removes
realized CPI1 terms and re-averages over the remaining forward-looking quarters.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import adjust_cpi10_forecasts


def main(config_path: str | None = None) -> None:
    """Load config, compute adjusted CPI10 expectations, and write CSV."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        config_path = Path(config_path)

    with open(config_path) as f:
        config = json.load(f)

    repo_root = Path(__file__).parent.parent
    cleaned_dir = repo_root / config["cleaned_dir"]
    input_path = cleaned_dir / "forecast_individual.csv"
    output_path = cleaned_dir / "adjusted_cpi10.csv"

    forecast_individual = pd.read_csv(input_path)
    adjusted_cpi10 = adjust_cpi10_forecasts(
        forecast_individual=forecast_individual,
    )

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    adjusted_cpi10.to_csv(output_path, index=False)

    print("Adjusted CPI10 expectations")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Rows:   {len(adjusted_cpi10)}")
    print("Done.")


if __name__ == "__main__":
    config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path=config_path_arg)
