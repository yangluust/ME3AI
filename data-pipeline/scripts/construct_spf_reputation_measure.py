"""Construct SPF reputation-measure table from adjusted CPI10 forecasts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_adjust import construct_reputation_measure


def main(
    clean_config_path: str | None = None,
    reputation_config_path: str | None = None,
) -> None:
    """Load cleaned data and reputation parameters, then write CSV."""
    repo_root = Path(__file__).parent.parent
    if clean_config_path is None:
        clean_config = repo_root / "config" / "spf_clean.json"
    else:
        clean_config = Path(clean_config_path)
    if reputation_config_path is None:
        reputation_config = repo_root / "config" / "reputation_measure.json"
    else:
        reputation_config = Path(reputation_config_path)

    with open(clean_config) as file:
        clean_settings = json.load(file)
    with open(reputation_config) as file:
        reputation_settings = json.load(file)

    cleaned_dir = repo_root / clean_settings["cleaned_dir"]
    input_path = cleaned_dir / "adjusted_cpi10.csv"
    output_path = cleaned_dir / "reputation_measure.csv"

    adjusted_cpi10 = pd.read_csv(input_path)
    x_table = adjusted_cpi10.rename(columns={"adjusted_cpi10": "x"})
    reputation_measure = construct_reputation_measure(
        x_table=x_table,
        config=reputation_settings,
    )

    cleaned_dir.mkdir(parents=True, exist_ok=True)
    reputation_measure.to_csv(output_path, index=False)

    print("Constructed SPF reputation measure")
    print(f"  Input:  {input_path}")
    print(f"  Config: {reputation_config}")
    print(f"  Output: {output_path}")
    print(f"  Rows:   {len(reputation_measure)}")
    print("Done.")


if __name__ == "__main__":
    clean_config_arg = sys.argv[1] if len(sys.argv) > 1 else None
    reputation_config_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(
        clean_config_path=clean_config_arg,
        reputation_config_path=reputation_config_arg,
    )
