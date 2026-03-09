"""Download SPF data for variables specified in config.

Reads variable names (and optional file_types, out_dir, overwrite) from
config/spf_download.json and calls download_by_variable_names from src.spf_download.
Output is written to data-pipeline/input/ by default.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spf_download import download_by_variable_names


def main(config_path: str | None = None) -> None:
    """Load config and download SPF files for the configured variables."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spf_download.json"
    else:
        config_path = Path(config_path)

    with open(config_path) as f:
        config = json.load(f)

    variable_names = config["variable_names"]
    file_types = config.get(
        "file_types",
        ["median_level", "mean_level", "dispersion", "individual"],
    )
    out_dir_raw = config.get("out_dir", "input")
    overwrite = config.get("overwrite", "skip-if-exists")

    # Resolve out_dir relative to data-pipeline root (parent of scripts)
    repo_root = Path(__file__).parent.parent
    out_dir = repo_root / out_dir_raw if not Path(out_dir_raw).is_absolute() else Path(out_dir_raw)

    print(f"Downloading SPF data for variables: {variable_names}")
    print(f"File types: {file_types}")
    print(f"Output directory: {out_dir}")
    print(f"Overwrite policy: {overwrite}")

    written = download_by_variable_names(
        variable_names=variable_names,
        file_types=file_types,
        out_dir=out_dir,
        overwrite=overwrite,
    )

    print(f"Wrote {len(written)} file(s) to {out_dir}")
    for p in written:
        print(f"  {p.name}")


if __name__ == "__main__":
    config_path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_path=config_path_arg)
