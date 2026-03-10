"""Clean SPF individual forecasts to 3NF CSV.

Reads config/spf_clean.json (input_dir, cleaned_dir), loads all
Individual_*.xlsx from input_dir, and writes forecast_individual.csv,
survey.csv, and forecaster_survey.csv to cleaned_dir.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_clean import clean_individual_to_3nf


def main(config_path: str | None = None) -> None:
    """Load config and run SPF individual cleaning to 3NF."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spf_clean.json"
    else:
        config_path = Path(config_path)

    with open(config_path) as f:
        config = json.load(f)

    repo_root = Path(__file__).parent.parent
    input_dir = repo_root / config["input_dir"]
    cleaned_dir = repo_root / config["cleaned_dir"]

    print("SPF individual cleaning (3NF)")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {cleaned_dir}")

    forecast_individual, survey, forecaster_survey = clean_individual_to_3nf(
        input_dir=input_dir,
        cleaned_dir=cleaned_dir,
    )

    print(f"  forecast_individual: {len(forecast_individual)} rows -> cleaned/forecast_individual.csv")
    print(f"  survey:              {len(survey)} rows -> cleaned/survey.csv")
    print(f"  forecaster_survey:   {len(forecaster_survey)} rows -> cleaned/forecaster_survey.csv")
    print("Done.")


if __name__ == "__main__":
    config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path=config_path_arg)
